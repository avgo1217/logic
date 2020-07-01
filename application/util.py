# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

from flask   import json, url_for, jsonify, render_template
from jinja2  import TemplateNotFound
from application     import application

from . models import User
from application    import db,bc,mail
from . common import *
from sqlalchemy import desc,or_
import hashlib
from flask_mail  import Message
import re
from flask       import render_template

import      os, datetime, time, random

# build a Json response
def response( data ):
    return application.response_class( response=json.dumps(data),
                               status=200,
                               mimetype='application/json' )

def g_db_commit( ):

    db.session.commit( );    

def g_db_add( obj ):

    if obj:
        db.session.add ( obj )

def g_db_del( obj ):

    if obj:
        db.session.delete ( obj )
