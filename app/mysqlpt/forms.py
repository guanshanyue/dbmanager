#!/usr/bin/python
# coding=utf-8
#__author__ = 'wangqy'

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, BooleanField, SubmitField,validators
from wtforms.validators import DataRequired, Length,EqualTo, Email, DataRequired

class LoginForm(Form):
    db_host= StringField('db_host', validators=[DataRequired()])
    db_name = StringField('db_name', validators=[DataRequired()])
    db_password = PasswordField('db_password', validators=[DataRequired()])
    db_privileges = StringField('db_privileges', validators=[DataRequired()])
    db_name= StringField('db_name', validators=[DataRequired()])
    remember_me = BooleanField(u'记住我')
    submit = SubmitField('Log In')