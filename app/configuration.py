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
	SQLALCHEMY_DATABASE_URI = 'postgres://mvtceftihysnsf:53e94b349d53a09735f2b285328a5106658badec007047fec68e18733c03664a@ec2-50-17-90-177.compute-1.amazonaws.com:5432/d586tdvmrasj8g'
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
	ROOT='http://127.0.0.1:5000/'