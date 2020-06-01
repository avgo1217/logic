# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

import os

<<<<<<< HEAD
from .flask            import Flask, jsonify, abort, request
from .flask_sqlalchemy import SQLAlchemy
from .flask_login      import LoginManager
from .flask_mail 	  import Mail
from .flask_bootstrap  import Bootstrap
from .flask_marshmallow import Marshmallow
from .flask_dropzone import Dropzone
=======
from flask            import Flask, jsonify, abort, request
from flask_sqlalchemy import SQLAlchemy
from flask_login      import LoginManager
from flask_mail 	  import Mail
from flask_bootstrap import Bootstrap
>>>>>>> 7f2a89201ab971f41bffa81febb69be16ffed6d7


# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

app.config.from_object('app.configuration.Config')

db = SQLAlchemy() # flask-sqlalchemy
mail = Mail()
login = LoginManager() # flask-loginmanager
bootstrap = Bootstrap()


db.init_app(app)
login.init_app(app)
mail.init_app(app)
bootstrap.init_app(app)
login.init_app(app) # init the login manager

login.login_view = 'main.login'
login.login_message = 'Please log in to access this page.'

# Setup database
@app.before_first_request
def initialize_database():
	db.create_all()

# Import routing, models and Start the App
from app import views, models
	