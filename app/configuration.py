# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

import os

# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

class Config():

	CSRF_ENABLED = True
	SECRET_KEY   = "77tgFCdrEEdv77554##@3" 
	#SQLALCHEMY_DATABASE_URI = 'postgres://zabhqwgiinaxvr:1bcca0b0a8f92323d1020095f22980a1b0af1d027d98407716ce48ac711c95c4@ec2-54-211-210-149.compute-1.amazonaws.com:5432/d85mu1oa759pn4'
	SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:RaliWeinskim@localhost/unlockd_test'
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	MAIL_SERVER = 'smtp.gmail.com'
	MAIL_PORT = 465
	MAIL_USE_SSL = True
	MAIL_USERNAME = 'ryan.kim@n1esports.com'
	MAIL_PASSWORD = 'mgisjfecrekyhiqp'    
	ADMINS = ['ryan.kim@n1esports.com']
	SECURITY_EMAIL_SENDER = 'ryan.kim@n1esports.com'
	SESSION_TYPE = 'filesystem'
	UPLOAD_FOLDER='app/uploads/'
	ALLOWED_EXTENSIONS={'csv'}
	#ROOT='https://warm-journey-64560.herokuapp.com/'
	ROOT = 'http://127.0.0.1:5000/'
	