# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

# Python modules
import os, logging 
import json
import urllib.request

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
from app.models import User, TrainingInstance, Scenarios, TrainingInstanceSchema
from app.email import send_password_reset_email


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
        all_scenarios_df = pd.read_sql(db.session.query(Scenarios).statement,db.session.bind)
        user.add_all_new_sessions(all_scenarios_df)

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
    if current_user.is_authenticated:
        url = url_for('get_training_instances', username = current_user.username)
        url = "http://127.0.0.1:5000/api/traininginstances/N1Esports"
        response = requests.get(url)
        data = response.json()
        #data = data.json()
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    #content = None

    try:

        # try to match the pages defined in -> pages/<input file>
        return render_template( 'aim-data-tracker.html', data=data )
    
    except:
        
        return render_template( 'pages/error-404.html' )

@app.route("/api/traininginstances/<username>", methods=["GET"])
def get_training_instances(username):
    if current_user.is_authenticated and current_user.username == username:
        user = User.query.filter_by(username = current_user.username).first()
        training_instances_schema = TrainingInstanceSchema(many=True)
        all_training_instances = TrainingInstance.query.filter(TrainingInstance.user_id==user.id).all()
        result = training_instances_schema.dump(all_training_instances)
        return jsonify(result[0])
    else:
        return redirect(url_for('login'))

# Return sitemap 
@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'sitemap.xml')
