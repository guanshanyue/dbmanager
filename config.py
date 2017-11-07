#!/usr/bin/python
# coding=utf-8
#__author__ = 'wangqy'

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import os
basedir = os.path.abspath(os.path.dirname(__file__))

CSRF_ENABLED = True

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    POSTS_PER_PAGE = 15
    scripts_dir = os.path.join(basedir,'scripts')
    back_script = os.path.join(scripts_dir,'Backup_Mysql.py')

    @staticmethod
    def init_app(app):
        pass


class ProductionConfig(Config):
    DEBUG = True
    #SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or  'mysqlpt://root:123456@127.0.0.1:3306/backmanage?charset=utf8'
    SQLALCHEMY_DATABASE_URI =  'mysql://root:123456@127.0.0.1:3306/backmanage?charset=utf8'


config = {
    'production': ProductionConfig,
    'default': ProductionConfig
}
