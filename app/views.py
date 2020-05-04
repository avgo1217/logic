# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

# Python modules
import os, logging 
import json
import urllib.request
from datetime import datetime

from flask import redirect, render_template, request, url_for, flash, jsonify, session
from flask_login import current_user,login_required
from flask_login import login_user
from flask_login import logout_user
from werkzeug.urls import url_parse
import pandas as pd
import requests

# Flask modules
from flask               import render_template, request, url_for, redirect, send_from_directory
from flask_login         import login_user, logout_user, current_user, login_required
from werkzeug.exceptions import HTTPException, NotFound, abort

# App modules
from app import db, app
from app.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from app.models import User, TrainingInstance, Scenarios, TrainingInstanceSchema, Videos
from app.email import send_password_reset_email

# sql modules
from sqlalchemy.sql import func

# Logout user
@app.route('/logout.html')
def logout():
    logout_user()
    return redirect(url_for('index'))

# Register a new user
@app.route('/register.html', methods=['GET', 'POST'])
def register():
    
    # cut the page for authenticated users
    if current_user.is_authenticated:
        return redirect(url_for('index'))
            
    # declare the Registration Form
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, aim_training_tool_user_status=1)
        user.set_password(form.password.data)
        user.set_name_encrypt()
        db.session.add(user)
        db.session.commit()
        flash('Congrats! You have suceessfully registered.')
        return redirect(url_for('login'))
    return render_template('auth/register.html', title='Register', form=form)

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('auth/reset_password_request.html', title='Reset Password', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('auth/reset_password.html', form=form)

# Authenticate user
@app.route('/login.html', methods=['GET', 'POST'])
def login():
    
    if current_user.is_authenticated:
        return redirect(url_for('aim_tracker'))
    form = LoginForm()

    #If the form is valid, returns user to a certain page with the login
    if form.validate_on_submit():
        user = User.query.filter_by(username = form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user,remember=form.remember_me.data)
        user.update_scenarios_table(1,'all_scenarios.csv')
        user.add_videos_table()
        all_scenarios_df = pd.read_sql(db.session.query(Scenarios).statement,db.session.bind)
        user.add_all_new_sessions(all_scenarios_df)
        #user.add_videos_table('temp_videos.csv')

        next_page = url_for('aim_tracker')

        #if not next_page or url_parse(next_page).netloc != '':
        #   next_page = url_for('main.render_dashboard')
        return redirect(next_page)

    return render_template('auth/login.html', title='Sign In', form=form)


# App main route + generic routing
@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path>')
def index(path):

    #if not current_user.is_authenticated:
    #    return redirect(url_for('login'))

    #content = None
    try:

        # try to match the pages defined in -> pages/<input file>
        return render_template( 'pages/'+path )
    
    except:
        
        return render_template( 'pages/error-404.html' )

# App main route + generic routing
@app.route('/aim-data-tracker/')
def aim_tracker():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    try:
        # try to match the pages defined in -> pages/<input file>
        return render_template( 'aim-data-tracker.html')    
    except:
        return render_template( 'pages/error-404.html' )

# App main route + generic routing
@app.route('/browse/')
def logic_browse():
    #if not current_user.is_authenticated:
    #    return redirect(url_for('login'))
    try:
        # try to match the pages defined in -> pages/<input file>
        return render_template( 'logic-browse.html')    
    except:
        return render_template( 'pages/error-404.html' )

@app.route('/browse/<video_id>')
def logic_browse_single(video_id):
    #if not current_user.is_authenticated:
    #    return redirect(url_for('login'))
    try:
        # try to match the pages defined in -> pages/<input file>
        return render_template( 'single-video.html', video_id = video_id)    
    except:
        return render_template( 'pages/error-404.html' )


#APIs
@app.route("/api/videos/search/<video_id>", methods=["GET"])
def get_one_video_search(video_id):
    result = get_one_video(video_id)
    return result

@app.route("/api/videos/search/", methods=["GET"])
def get_all_videos_search():
    if request.args.get('search'):
        term = request.args.get('search')
    else:
        term = ""
    result = get_search_bar_data(term)
    return result

@app.route("/api/videos/filters/", methods=["GET"])
def get_filtered_videos_list():
    # get all args
    tags = request.args.getlist('tag')
    game = request.args.get('game')
    difficulty = request.args.get('difficulty')
    n1select = request.args.get('n1select')
    n1original = request.args.get('n1original')

    if tags:
        tag_list = tags
    else:
        tag_list = []
    

    result = get_videos_by_filters(tag_list, game, difficulty, n1select, n1original)
    return result

@app.route("/api/traininginstances/<username>/<scenario>/<aimmetric>/<daterange>/<smoothflag>", methods=["GET"])
def get_training_instances(username, scenario, aimmetric,daterange,smoothflag):
    if current_user.is_authenticated and current_user.username == username:
        result = get_training_instances_by_username_scenario(username, scenario, current_user,aimmetric, daterange, smoothflag)
        return result
    else:
        return redirect(url_for('login'))

@app.route("/api/scenarios/<username>", methods=["GET"])
def get_unique_scenarios(username):

    # Angular, react, to abstract away raw jquery (vue.js)
    if current_user.is_authenticated and current_user.username == username:
        result = get_unique_list_of_user_scenarios(username, current_user)
        return result
    else:
        return redirect(url_for('login'))

@app.route("/api/stats/<username>/<scenario>/<aimmetric>/<daterange>/<smoothflag>", methods=["GET"])
def get_bottom_row_stats(username, scenario, aimmetric,daterange,smoothflag):
    if current_user.is_authenticated and current_user.username == username:
        result = calculate_bottom_row_stats(username, scenario, aimmetric, daterange, smoothflag)
        return result
    else:
        return redirect(url_for('login'))

@app.route("/api/globalstat/<scenario>/<aim_metric>/<stat_type>", methods=["GET"])
def get_global_comparison_stat(scenario,aim_metric,stat_type):

    # Angular, react, to abstract away raw jquery (vue.js)
    if current_user.is_authenticated:
        result = calculate_global_stat(scenario, aim_metric, stat_type)
        return result
    else:
        return redirect(url_for('login'))

# Return sitemap 
@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'sitemap.xml')

#Functions
def get_videos_by_filters(tag_list, game, difficulty, n1select, n1original):
    df = pd.read_sql(db.session.query(Videos).statement, db.session.bind)
    if game != "All":
        df = df.loc[df['game']==game]
    if difficulty != "All":
        df = df.loc[df['difficulty']==difficulty]

    if n1select == "select":
        df = df.loc[df['n1_select_tag']==1]
    if n1original =="original":
        df = df.loc[df['n1_original_content_tag']==1]

    if len(tag_list)>0:
        for tag in tag_list:
            df = df[df['tags'].str.contains('|'.join([tag])).any(level=0)]

    df_json = df.to_json(orient='records')
    return jsonify(df_json)

def get_search_bar_data(term): 
    df = pd.read_sql(db.session.query(Videos).statement, db.session.bind)
    all_tags = []
    count = 1;
    for item in df.tags:
        if item is not None:
            tag_list = item.split(',')
            all_tags.extend(tag_list)
    final_tags = []
    [final_tags.append(x) for x in all_tags if x not in final_tags]
    final_tags.sort()

    #Create all tags to keep consistent id
    all_results={}
    all_results['results'] = [{"text":"Tags","children":[]}]
    for tag in final_tags:
        all_results['results'][0]["children"].append(dict(id=count,text=tag))
        count = count+1

    #Filter out for search term
    if len(term)>0:
        all_results['results'][0]["children"] = [s for s in all_results['results'][0]["children"] if term.upper() in s["text"].upper()]

    #creates the result dict
    return jsonify(all_results)

def process_date_range(filtered_df, date_range):
    #Check for date range
    if date_range == "today":
        filtered_df = filtered_df[filtered_df.date_time > datetime.now() - pd.to_timedelta('1day')]

    if date_range == "this_week":
        filtered_df = filtered_df[filtered_df.date_time > datetime.now() - pd.to_timedelta('7day')]

    if date_range == "this_month":
        filtered_df = filtered_df[filtered_df.date_time > datetime.now() - pd.to_timedelta('30day')]

    filtered_df['date_time'] = filtered_df['date_time'].dt.strftime('%m/%d/%Y')
    return filtered_df

def filter_for_aim_metric(filtered_df, aim_metric):
    df = filtered_df[[aim_metric,"date_time"]]
    return df

def apply_smoothing(filtered_df,smooth_flag, aim_metric):
    if smooth_flag == "smooth":
        target = filtered_df[aim_metric]
        mean = target.mean()
        sd = target.std()
        filtered_df = filtered_df[(target > mean - 2*sd) & (target < mean + 2*sd)]
    return filtered_df

def calculate_global_stat(scenario, aim_metric, stat_type):
    if stat_type == "none":
        return jsonify([])
    if stat_type == "avg":
        df = pd.read_sql(db.session.query(TrainingInstance)
        .filter(TrainingInstance.scenario==scenario).statement, db.session.bind)
        average_stat = df[aim_metric].mean()
        return jsonify(["{0:.2f}".format(average_stat)])
    if stat_type == "best":
        df = pd.read_sql(db.session.query(TrainingInstance)
        .filter(TrainingInstance.scenario==scenario).statement, db.session.bind)
        if aim_metric == "avg_ttk":
            best_stat = df[aim_metric].min()
        else:
            best_stat = df[aim_metric].max()
        return jsonify(["{0:.2f}".format(best_stat)])

def calculate_bottom_row_stats(username, scenario, selected_aim_metric,date_range,smoothflag):
    filtered_df = process_for_all_filtered_data(username, scenario, current_user, selected_aim_metric, date_range, smoothflag)
    if filtered_df.shape[0] > 0:
        data_list = filtered_df[selected_aim_metric].values
        best = data_list.max()
        average = data_list.mean()
        if selected_aim_metric == 'accuracy':
            best = "{0:.2f}%".format(best*100)
            average = "{0:.2f}%".format(average*100)
        else:
            best = "{0:.2f}".format(best)
            average = "{0:.2f}".format(average)
        improvement = [(data_list[i + 1] - data_list[i])/data_list[i] for i in range(len(data_list)-1)]
        improvement = sum(improvement)/len(improvement)*100
        if improvement > 0:
            improvement = "+ {0:.2f}%".format(improvement)
        else:
            improvement = "{0:.2f}%".format(improvement)
        num_scenario_played = len(data_list)

    else:
        best = "-"
        average = "-"
        improvement = "-"
        num_scenario_played = "-"

    return jsonify([best,average,improvement,num_scenario_played])

#SQL CALLS
def get_all_videos():
    df = pd.read_sql(db.session.query(Videos).statement, db.session.bind)
    df_json = df.to_json(orient='records')
    return jsonify(df_json)

def get_one_video(video_id):
    videoquery = Videos.query.filter_by(id=video_id)
    df = pd.read_sql(videoquery.statement, videoquery.session.bind)
    df_json = df.to_json(orient='records')
    
    return jsonify(df_json)

def process_for_all_filtered_data(username, scenario, current_user, aim_metric, date_range, smooth_flag):
    user = User.query.filter_by(username = current_user.username).first()
    df = pd.read_sql(db.session.query(TrainingInstance)
        .filter(TrainingInstance.user_id == current_user.id)
        .filter(TrainingInstance.scenario==scenario)
        .order_by(TrainingInstance.date_time.asc()).statement, db.session.bind)
    df = process_date_range(df, date_range)
    df = filter_for_aim_metric(df, aim_metric)
    df = apply_smoothing(df, smooth_flag, aim_metric)
    return df

def get_training_instances_by_username_scenario(username, scenario, current_user, aim_metric, date_range, smooth_flag):
    df = process_for_all_filtered_data(username, scenario, current_user, aim_metric, date_range, smooth_flag)
    df_json = df.to_json(orient='records')
    #training_instances_schema = TrainingInstanceSchema(many=True)
    #all_training_instances = TrainingInstance.query.filter(TrainingInstance.user_id==user.id).filter(TrainingInstance.scenario==scenario).all()
    #result = training_instances_schema.dump(all_training_instances)
    return jsonify(df_json)

def get_unique_list_of_user_scenarios(username, current_user):
    user = User.query.filter_by(username = current_user.username).first()
    df = pd.read_sql(db.session.query(TrainingInstance).filter(TrainingInstance.user_id == current_user.id).order_by(TrainingInstance.scenario.asc()).statement, db.session.bind)
    list_of_unique_scenarios = df.scenario.unique()
    #result_dict = { i : list_of_unique_scenarios[i] for i in range(0, len(list_of_unique_scenarios) ) }
    #result = training_instances_schema.dump(all_training_instances)
    return jsonify(list(list_of_unique_scenarios))
