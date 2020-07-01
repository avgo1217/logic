# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

import os


from flask            import Flask, jsonify, abort, request
from flask_sqlalchemy import SQLAlchemy
from flask_login      import LoginManager
from flask_mail 	  import Mail
from flask_bootstrap import Bootstrap



# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

application = Flask(__name__)

application.config.from_object('app.configuration.Config')

db = SQLAlchemy() # flask-sqlalchemy
mail = Mail()
login = LoginManager() # flask-loginmanager
bootstrap = Bootstrap()


db.init_app(application)
login.init_app(application)
mail.init_app(application)
bootstrap.init_app(application)
login.init_app(application) # init the login manager

login.login_view = 'main.login'
login.login_message = 'Please log in to access this page.'

# Setup database
@application.before_first_request
def initialize_database():
	db.create_all()

# Import routing, models and Start the App
from application import views, models
	