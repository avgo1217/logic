# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

# Python modules
import os, logging 
import json
import urllib.request
from datetime import datetime, date

from flask import redirect, render_template, request, url_for, flash, jsonify, session
from flask_login import current_user,login_required
from flask_login import login_user
from flask_login import logout_user
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
import pandas as pd
import requests
from io import StringIO
# Flask modules
from flask               import render_template, request, url_for, redirect, send_from_directory
from flask_login         import login_user, logout_user, current_user, login_required
from werkzeug.exceptions import HTTPException, NotFound, abort

# App modules
from app import db, app
from app.forms import LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from app.models import User, TrainingInstance, Scenarios, Videos, Playlists
from app.email import send_password_reset_email

# sql modules
from sqlalchemy.sql import func
from sqlalchemy import or_

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

#############################################
###################LOGIN######################
#############################################
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
        user = User(username=form.username.data, email=form.email.data, admin_status=1)
        user.set_password(form.password.data)
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
        
        #user.add_videos_table('temp_videos.csv')

        next_page = url_for('aim_tracker')

        #if not next_page or url_parse(next_page).netloc != '':
        #   next_page = url_for('main.render_dashboard')
        return redirect(next_page)

    return render_template('auth/login.html', title='Sign In', form=form)

#############################################
###################ADMIN######################
#############################################
@app.route('/admin/home', methods=['GET','POST'])
def admin_home():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    if not current_user.admin_status == 1:
        return redirect(url_for('index'))
    if request.method =='GET':
        try:
            # try to match the pages defined in -> pages/<input file>

            return render_template( '/admin/admin-home.html', config=app.config['ROOT'])    
        except:
            return render_template( 'pages/error-404.html' )

    homepage_playlists=request.form["featured_playlists"]
    best_new_videos =request.form["best_new_videos"]
    staff_picks = request.form["staff_picks"]

    if homepage_playlists:
        try: 
            Playlists.query.update({Playlists.homepage_featured: 0})
            db.session.commit()

            playlist_split = homepage_playlists.split(",")

            for playlist_id in playlist_split:
                playlist_temp = Playlists.query.get(int(playlist_id))
                playlist_temp.homepage_featured = 1
                db.session.commit()

        except:
            return render_template( 'pages/error-404.html' )

    if best_new_videos:
        try: 
            Videos.query.update({Videos.homepage_bestnew:0})
            db.session.commit()

            bestnew_split = best_new_videos.split(",")

            for video_id in bestnew_split:
                video_temp = Videos.query.get(int(video_id))
                video_temp.homepage_bestnew = 1
                db.session.commit()
        except:
            return render_template( 'pages/error-404.html' )

    if staff_picks:
        try:
            Videos.query.update({Videos.homepage_staffpick:0})
            db.session.commit()

            staff_picks_split = staff_picks.split(",")

            for video_id in staff_picks_split:
                video_temp = Videos.query.get(int(video_id))
                video_temp.homepage_staffpick = 1
                db.session.commit()
        except:
            return render_template( 'pages/error-404.html' )

    return render_template( '/admin/admin-home.html', config=app.config['ROOT']) 

@app.route('/admin/addvideo', methods=['GET','POST'])
def admin_video_add():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    if not current_user.admin_status == 1:
        return redirect(url_for('index'))
    if request.method =='GET':
        try:
            # try to match the pages defined in -> pages/<input file>

            return render_template( '/admin/admin-add-video.html', config=app.config['ROOT'])    
        except:
            return render_template( 'pages/error-404.html' )

    video_url=request.form["video_url"]
    video_title=request.form["video_title"]
    video_description= request.form["video_description"]
    video_channel_name= request.form["video_channel_name"]
    video_channel_url= request.form["video_channel_url"]
    game= request.form["game"]
    timestamps= request.form["timestamps"]
    tags=request.form["tags"]
    difficulty=request.form["difficulty"]
    featured_video_tag = request.form["featured_video_tag"]
    best_new_video_tag = request.form["best_new_video_tag"]
    n1_select_tag=request.form["n1_select_tag"]

    if video_url and video_title and video_description and video_channel_name and video_channel_url and game and tags and timestamps and difficulty and featured_video_tag and n1_select_tag and best_new_video_tag:
        new_video = Videos(video_url=video_url,
                            video_title=video_title,
                            video_description= video_description,
                            video_channel_name= video_channel_name,
                            video_channel_url= video_channel_url,
                            game= game,
                            timestamps= timestamps,
                            tags=tags,
                            date_added_n1=date.today(),
                            difficulty=difficulty,
                            featured_video_tag = featured_video_tag,
                            best_new_video_tag = best_new_video_tag,
                            n1_select_tag=n1_select_tag,
                            homepage_bestnew =0,
                            homepage_staffpick=0
                            )

        db.session.add(new_video)
        db.session.commit()
        return render_template( '/admin/admin-add-video.html',config=app.config['ROOT'])
    else:
        flash("Complete the form")

@app.route('/admin/editvideo', methods=['GET','POST'])
def admin_video_edit():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    if not current_user.admin_status == 1:
        return redirect(url_for('index'))
    if request.method =='GET':
        try:
            # try to match the pages defined in -> pages/<input file>

            return render_template( '/admin/admin-edit-video.html', config=app.config['ROOT'])    
        except:
            return render_template( 'pages/error-404.html' )

    video_id = request.form["video_id"]
    video_url=request.form["video_url"]
    video_title=request.form["video_title"]
    video_description= request.form["video_description"]
    video_channel_name= request.form["video_channel_name"]
    video_channel_url= request.form["video_channel_url"]
    game= request.form["game"]
    timestamps= request.form["timestamps"]
    tags=request.form["tags"]
    difficulty=request.form["difficulty"]
    featured_video_tag = request.form["featured_video_tag"]
    best_new_video_tag = request.form["best_new_video_tag"]
    n1_select_tag=request.form["n1_select_tag"]

    if video_id and video_url and video_title and video_channel_name and video_channel_url and game and difficulty:
        new_video = Videos.query.filter_by(id= video_id).first()
        new_video.video_url =video_url
        new_video.video_title =video_title
        new_video.video_description= video_description
        new_video.video_channel_name= video_channel_name
        new_video.video_channel_url= video_channel_url
        new_video.game= game
        new_video.timestamps= timestamps
        new_video.tags=tags
        new_video.date_added_n1=date.today()
        new_video.difficulty=difficulty
        new_video.featured_video_tag = featured_video_tag
        new_video.best_new_video_tag = best_new_video_tag
        new_video.n1_select_tag=n1_select_tag
        new_video.homepage_bestnew =0
        new_video.homepage_staffpick=0

        db.session.commit()
        return render_template( '/admin/admin-edit-video.html',config=app.config['ROOT'])
    else:
        flash("Complete the form")

@app.route('/admin/addplaylist', methods=['GET','POST'])
def admin_playlist_add():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    if not current_user.admin_status == 1:
        return redirect(url_for('index'))
    if request.method =='GET':
        try:
            # try to match the pages defined in -> pages/<input file>

            return render_template( '/admin/admin-add-playlist.html', config=app.config['ROOT'])    
        except:
            return render_template( 'pages/error-404.html' )

    playlist_name=request.form["playlist_name"]
    playlist_description =request.form["playlist_description"]
    list_of_videos = request.form["list_of_videos"]
    playlist_img_src = request.form["imagesource"]
    playlist_difficulty = request.form["difficulty"]
    playlist_author_name = request.form["author_username"]
    playlist_author_id = request.form["author_id"]

    if playlist_name and playlist_description and list_of_videos and playlist_img_src and playlist_difficulty and playlist_author_name and playlist_author_id:
        new_playlist = Playlists(playlist_date_created = date.today(), 
                             playlist_name=request.form["playlist_name"],
                             playlist_description =request.form["playlist_description"],
                             list_of_videos = request.form["list_of_videos"],
                             playlist_img_src = request.form["imagesource"],
                             playlist_difficulty = request.form["difficulty"],
                             playlist_author_name = request.form["author_username"],
                             playlist_author_id = request.form["author_id"],
                             homepage_featured = 0)
        db.session.add(new_playlist)
        db.session.commit()
        return render_template( '/admin/admin-add-playlist.html',config=app.config['ROOT'])
    else:
        flash("Complete the form")

@app.route('/admin/editplaylist', methods=['GET','POST'])
def admin_playlist_edit():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    if not current_user.admin_status == 1:
        return redirect(url_for('index'))
    if request.method =='GET':
        try:
            # try to match the pages defined in -> pages/<input file>

            return render_template( '/admin/admin-edit-playlist.html', config=app.config['ROOT'])    
        except:
            return render_template( 'pages/error-404.html' )

    playlist_id = request.form["playlist_id"]
    playlist_name=request.form["playlist_name"]
    playlist_description =request.form["playlist_description"]
    list_of_videos = request.form["list_of_videos"]
    playlist_img_src = request.form["imagesource"]
    playlist_difficulty = request.form["difficulty"]
    playlist_author_name = request.form["author_username"]
    playlist_author_id = request.form["author_id"]

    if playlist_name and playlist_description and list_of_videos and playlist_img_src and playlist_difficulty and playlist_author_name and playlist_author_id:
        new_playlist = Playlists.query.filter_by(id= playlist_id).first()
        new_playlist.playlist_name = playlist_name
        new_playlist.playlist_description = playlist_description
        new_playlist.list_of_videos = list_of_videos
        new_playlist.playlist_img_src = playlist_img_src
        new_playlist.playlist_difficulty = playlist_difficulty
        new_playlist.playlist_author_name = playlist_author_name
        new_playlist.playlist_author_id = playlist_author_id

        db.session.commit()
        return render_template( '/admin/admin-edit-playlist.html',config=app.config['ROOT'])
    else:
        flash("Complete the form")

#############################################
###################MAIN LINKS######################
#############################################
@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path>')
def index(path):

    #if not current_user.is_authenticated:
    #    return redirect(url_for('login'))

    #content = None
    try:

        # try to match the pages defined in -> pages/<input file>
        return render_template( 'pages/'+path , config=app.config['ROOT'])
    
    except:
        
        return render_template( 'pages/error-404.html' )

@app.route('/aim-data-tracker/')
def aim_tracker():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    try:
        # try to match the pages defined in -> pages/<input file>
        user = User.query.filter_by(username = current_user.username).first()
        if user.get_existing_scenario_instances():
            result = get_most_played_scenario(current_user.username)
            return render_template( 'aim-data-tracker.html', scenario = result, config=app.config['ROOT'])
        else:
            return render_template( 'aim-data-tracker.html',scenario = "Upload Kovaaks Data", config=app.config['ROOT'])
    except:
        return render_template( 'pages/error-404.html' )

@app.route('/browse/')
def logic_browse():
    #if not current_user.is_authenticated:
    #    return redirect(url_for('login'))
    try:
        # try to match the pages defined in -> pages/<input file>
        return render_template( 'logic-browse.html',config=app.config['ROOT'])    
    except:
        return render_template( 'pages/error-404.html' )

@app.route('/browse/<video_id>')
def logic_browse_single(video_id):
    #if not current_user.is_authenticated:
    #    return redirect(url_for('login'))
    try:
        # try to match the pages defined in -> pages/<input file>
        return render_template( 'single-video.html', video_id = video_id, config=app.config['ROOT'])    
    except:
        return render_template( 'pages/error-404.html' )

@app.route('/playlist/<playlist_id>/<video_id>')
def logic_playlist_single(playlist_id, video_id):
    #if not current_user.is_authenticated:
    #    return redirect(url_for('login'))
    try:
        # try to match the pages defined in -> pages/<input file>
        return render_template( 'single-playlist.html', playlist_id = playlist_id, video_id=video_id, config=app.config['ROOT'])    
    except:
        return render_template( 'pages/error-404.html' )

@app.route('/playlists/')
def logic_playlist_all():
    #if not current_user.is_authenticated:
    #    return redirect(url_for('login'))
    try:
        # try to match the pages defined in -> pages/<input file>
        return render_template( 'playlist-browse.html',config=app.config['ROOT'])    
    except:
        return render_template( 'pages/error-404.html' )



#############################################
###################APIS######################
#############################################
@app.route("/api/home")
def get_home_page():
    result = get_home_page_info()
    return result

@app.route("/api/videos/search/<video_id>", methods=["GET"])
def get_one_video_search(video_id):
    result = get_one_video(video_id)
    return result

@app.route("/api/playlists/search/<playlist_id>", methods=["GET"])
def get_one_playlist_search(playlist_id):
    result = get_one_playlist(playlist_id)

    return result

@app.route("/api/admin/playlists/search/<playlist_id>", methods=["GET"])
def get_one_playlist_admin(playlist_id):
    result = get_one_playlist_admin(playlist_id)
    return result

@app.route("/api/playlists/all", methods=["GET"])
def get_all_playlists():
    result = get_all_playlists()
    return result

@app.route("/api/admin/playlists/all", methods=["GET"])
def get_all_playlists_admin():
    result = get_all_playlists_admin()
    return result

@app.route("/api/videos/search/", methods=["GET"])
def get_all_videos_search():
    if request.args.get('search'):
        term = request.args.get('search')
    else:
        term = ""
    result = get_search_bar_data(term)
    return result

@app.route("/api/videos/admin/", methods=["GET"])
def get_all_videos_search_admin():
    if request.args.get('search'):
        term = request.args.get('search')
    else:
        term = ""
    result = get_search_bar_data_admin(term)
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
        if request.args.get('search'):
            term = request.args.get('search')
        else:
            term = ""
        result = get_scenarios_data_for_bar(username, term)
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

@app.route("/api/admin/videos", methods=["GET"])
def get_admin_videos():

    # Angular, react, to abstract away raw jquery (vue.js)
    if current_user.is_authenticated and current_user.admin_status==1:
        result = get_all_videos_admin()
        return result
    else:
        return redirect(url_for('login'))

@app.route("/api/videos/delete/<video_id>", methods=['POST'])
def delete_video(video_id):
    if current_user.is_authenticated and current_user.admin_status==1:
        delete_video(video_id)
        return render_template( '/admin/admin-edit-video.html',config=app.config['ROOT'])
    else:
        return render_template( '/admin/admin-edit-video.html',config=app.config['ROOT'])

@app.route("/api/playlists/delete/<playlist_id>", methods=['POST'])
def delete_playlist(playlist_id):
    if current_user.is_authenticated and current_user.admin_status==1:
        delete_playlist(playlist_id)
        return render_template( '/admin/admin-edit-playlist.html',config=app.config['ROOT'])
    else:
        return render_template( '/admin/admin-edit-playlist.html',config=app.config['ROOT'])

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'sitemap.xml')

#############################################
###################HELPER FUNCTIONS######################
#############################################
@app.route('/aim-data-tracker/upload', methods=['POST'])
def upload():
    uploaded_files = request.files.getlist("file[]")
    user = User.query.filter_by(username = current_user.username).first()
    all_scenarios_df = pd.read_sql(db.session.query(Scenarios).statement,db.session.bind)
    new_files = user.add_all_new_sessions(all_scenarios_df, uploaded_files)
    flash('You have successfully uploaded {x} new files'.format(x=new_files))
    return redirect(url_for('aim_tracker')) 

def delete_video(video_id):
    video_to_delete = Videos.query.get(video_id)
    if not video_to_delete:
        abort(404)
    if request.method == 'POST':
        db.session.delete(video_to_delete)
        db.session.commit()

def delete_playlist(playlist_id):
    playlist_to_delete = Playlists.query.get(playlist_id)
    if not playlist_to_delete:
        abort(404)
    if request.method == 'POST':
        db.session.delete(playlist_to_delete)
        db.session.commit()

def get_home_page_info():
    playlist_list=[]
    playlistquery = Playlists.query
    df = pd.read_sql(playlistquery.statement, playlistquery.session.bind)
    df = df.loc[df['homepage_featured']==1]
    df_json = df.to_dict(orient='records')
    for record in df_json:
        the_list = record['list_of_videos'].split(",")
        if the_list[-1] =="":
            the_list.pop()
        new_list=[]
        for item in the_list:
            videoquery = Videos.query.filter_by(id=int(item))
            temp_df = pd.read_sql(videoquery.statement, videoquery.session.bind)
            new_list.append({"video_id":int(item),
                             "video_title":temp_df.iloc[0]['video_title'],
                             "video_channel_name":temp_df.iloc[0]['video_channel_name'],
                             "video_channel_url":temp_df.iloc[0]['video_channel_url'],
                             "video_url":temp_df.iloc[0]['video_url'],
                             "video_description":temp_df.iloc[0]['video_description'],
                             "n1_description":temp_df.iloc[0]['n1_description'],
                             "date_added_n1":temp_df.iloc[0]['date_added_n1'],
                             "tags":temp_df.iloc[0]['tags']})
        
        record['list_of_videos']=new_list
        record['type']="featured_playlist"
    playlist_list.append(df_json)
    #Add best new
    videoquery = Videos.query.filter_by(homepage_bestnew=1)
    temp_df = pd.read_sql(videoquery.statement, videoquery.session.bind)
    best_json = temp_df.to_dict(orient='records')
    playlist_list.append(best_json)

    #Add staff selection
    videoquery = Videos.query.filter_by(homepage_staffpick=1)
    temp_df1 = pd.read_sql(videoquery.statement, videoquery.session.bind)
    best_json1 = temp_df1.to_dict(orient='records')
    playlist_list.append(best_json1)

    return jsonify(playlist_list)

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

def get_scenarios_data_for_bar(username, term):
    user = User.query.filter_by(username = current_user.username).first()
    df = pd.read_sql(db.session.query(TrainingInstance).filter(TrainingInstance.user_id == current_user.id).order_by(TrainingInstance.scenario.asc()).statement, db.session.bind)
    list_of_unique_scenarios = df.scenario.unique()

    all_results={}
    all_results['results'] = []
    count = 1
    for scenario in list_of_unique_scenarios:
        all_results['results'].append(dict(id=count,text=scenario))
        count = count+1

    #Filter out for search term
    if len(term)>0:
        all_results['results'] = [s for s in all_results['results'] if term.upper() in s["text"].upper()]

    return jsonify(all_results)

def get_most_played_scenario(username):
    user = User.query.filter_by(username = current_user.username).first()
    df = pd.read_sql(db.session.query(TrainingInstance).filter(TrainingInstance.user_id == current_user.id).statement, db.session.bind)
    df = df.scenario.value_counts().reset_index()
    most_played = df['index'].iloc[0]
    
    return most_played

def get_search_bar_data(term): 
    df = pd.read_sql(db.session.query(Videos).statement, db.session.bind)
    all_tags = []
    count = 1
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
        filtered_df = filtered_df[(target > mean - 3*sd) & (target < mean + 3*sd)]
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


#############################################
###################SQL CALLS######################
#############################################
def get_all_videos():
    df = pd.read_sql(db.session.query(Videos).statement, db.session.bind)
    df_json = df.to_json(orient='records')
    return jsonify(df_json)

def get_all_playlists_admin():
    playlistquery = Playlists.query
    df = pd.read_sql(playlistquery.statement, playlistquery.session.bind)
    df_json = df.to_dict(orient='records')
    return jsonify(df_json)

def get_all_playlists():
    playlistquery = Playlists.query
    df = pd.read_sql(playlistquery.statement, playlistquery.session.bind)
    df_json = df.to_dict(orient='records')
    for record in df_json:

        the_list = record['list_of_videos'].split(",")
        if the_list[-1] =="":
            the_list.pop()
        new_list=[]
        for item in the_list:
            videoquery = Videos.query.filter_by(id=int(item))
            temp_df = pd.read_sql(videoquery.statement, videoquery.session.bind)
            new_list.append({"video_id":int(item),
                             "video_title":temp_df.iloc[0]['video_title'],
                             "video_channel_name":temp_df.iloc[0]['video_channel_name'],
                             "video_channel_url":temp_df.iloc[0]['video_channel_url'],
                             "video_url":temp_df.iloc[0]['video_url'],
                             "video_description":temp_df.iloc[0]['video_description'],
                             "n1_description":temp_df.iloc[0]['n1_description'],
                             "date_added_n1":temp_df.iloc[0]['date_added_n1'],
                             "tags":temp_df.iloc[0]['tags']})
        
        record['list_of_videos']=new_list

    return jsonify(df_json)

def get_all_videos_admin():
    df = pd.read_sql(db.session.query(Videos).statement, db.session.bind)
    df = df[['id','video_title','video_channel_name','date_added_n1']]
    df = df.sort_values(by=['date_added_n1'])
    df_json = df.to_json(orient='records')
    return jsonify(df_json)


def get_one_video(video_id):
    videoquery = Videos.query.filter_by(id=video_id)
    df = pd.read_sql(videoquery.statement, videoquery.session.bind)
    df_json = df.to_json(orient='records')
    return jsonify(df_json)

def get_one_playlist(playlist_id):
    playlistquery = Playlists.query.filter_by(id=playlist_id)
    df = pd.read_sql(playlistquery.statement, playlistquery.session.bind)
    df_json = df.to_dict(orient='records')
    the_list = df_json[0]['list_of_videos'].split(",")
    if the_list[-1] =="":
        the_list.pop()
    new_list=[]

    for item in the_list:
        videoquery = Videos.query.filter_by(id=int(item))
        temp_df = pd.read_sql(videoquery.statement, videoquery.session.bind)
        new_list.append({"video_id":int(item),
                         "video_title":temp_df.iloc[0]['video_title'],
                         "video_channel_name":temp_df.iloc[0]['video_channel_name'],
                         "video_channel_url":temp_df.iloc[0]['video_channel_url'],
                         "video_url":temp_df.iloc[0]['video_url'],
                         "video_description":temp_df.iloc[0]['video_description'],
                         "n1_description":temp_df.iloc[0]['n1_description'],
                         "date_added_n1":temp_df.iloc[0]['date_added_n1'],
                         "tags":temp_df.iloc[0]['tags']})
    
    df_json[0]['list_of_videos']=new_list

    return jsonify(df_json)

def get_one_playlist_admin(playlist_id):
    playlistquery = Playlists.query.filter_by(id=playlist_id)
    df = pd.read_sql(playlistquery.statement, playlistquery.session.bind)
    df_json = df.to_dict(orient='records')

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
