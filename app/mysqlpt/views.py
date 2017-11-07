#!/usr/bin/python
# coding=utf-8
#__author__ = 'wangqy'

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

from flask import  render_template, request, flash,abort,redirect,url_for
from flask.ext.login import login_required, current_user
from sqlalchemy import and_,desc,or_
from . import mysql
from .. import db
from app.models import users,backhosts,customers,backarchives,config,backfailed,count_day_status,count_mon_status,mysql_privileges
import os,json,string,datetime
from random import choice
import datetime,MySQLdb,time



class DB():
    def __init__(self, DB_HOST, DB_PORT, DB_USER, DB_PWD, DB_NAME):
        self.DB_HOST = DB_HOST
        self.DB_PORT = DB_PORT
        self.DB_USER = DB_USER
        self.DB_PWD = DB_PWD
        self.DB_NAME = DB_NAME

        self.conn = self.getConnection()

    def getConnection(self):
        return MySQLdb.Connect(
                           host=self.DB_HOST,
                           port=self.DB_PORT,
                           user=self.DB_USER,
                           passwd=self.DB_PWD,
                           db=self.DB_NAME,
                           charset='utf8'
                           )

    def query(self, sqlString):
        cursor=self.conn.cursor()
        cursor.execute(sqlString)
        returnData=cursor.fetchall()
        cursor.close()
        return returnData

    def update(self, sqlString):
        cursor=self.conn.cursor()
        cursor.execute(sqlString)
        self.conn.commit()
        cursor.close()

    def close(self):
        self.conn.close()

def GenPassword(length=8,chars=string.ascii_letters+string.digits):
    return ''.join([choice(chars) for i in range(length)])

@mysql.route('/mysql_index/',methods=['GET', 'POST'])
@login_required
def mysql_index():
    if request.method == 'POST':
        pass
    else:
        mysql_privilege = mysql_privileges.query.order_by(desc(mysql_privileges.id)).all()
        return render_template('mysqlpt/mysql_privileges.html',mysql_privileges=mysql_privilege)

@mysql.route('/mysql_manage/<int:customer_id>',methods=['GET', 'POST'])
@login_required
def mysql_manage(customer_id):
    customer=customers.query.filter_by(id=customer_id).first()
    if customer is None:
        abort(404)
    else:
        mysql_privilege= mysql_privileges.query.filter_by(customer_id=customer_id).first()
        if mysql_privilege is  None :
            customer = customers.query.filter_by(id=customer_id).first()
            mysql_privilege=mysql_privileges(customer_id=customer.id,user_name=customer.db_user,user_pass=customer.db_pass,user_db=customer.db_name)
            db.session.add(mysql_privilege)
            db.session.commit()
        mysql_privilege= mysql_privileges.query.filter_by(customer_id=customer_id)
        return render_template('mysqlpt/mysql_privileges.html',mysql_privileges=mysql_privilege)

@mysql.route('/mysql_resetpassword/<int:customer_id>',methods=['GET', 'POST'])
@login_required
def mysql_resetpassword(customer_id):
    if request.method == 'POST':
        try:
            password = request.form['password']
            password02 = request.form['password02']
            if password != password02 :
                flash("密码不一致")
                return render_template('mysqlpt/mysql_resetpassword.html',customer_id=customer_id)
            else:
                mysql_privilege = mysql_privileges.query.filter_by(id=customer_id).first()
                customer=customers.query.filter_by(id=mysql_privilege.customer_id).first()
                if customer.db_user ==  mysql_privilege.user_name:
                    flash("管理员密码禁止修改")
                else:
                    db=DB(customer.db_ip,int(customer.db_port),customer.db_user,customer.db_pass,customer.db_name)
                    sql="update mysql.user set authentication_string=password(\'"+password02+"\') where user=\'"+mysql_privilege.user_name+"\'"
                    db.update(sql)
                    db.update('flush privileges;')
                    flash("密码更新成功")
        except Exception as e:
            return render_template('mysqlpt/test.html',test_id=sql)
        mysql_privilege = mysql_privileges.query.filter_by(id=customer_id)
        return render_template('mysqlpt/mysql_privileges.html',mysql_privileges=mysql_privilege)
    else:
        return render_template('mysqlpt/mysql_resetpassword.html',customer_id=customer_id)

@mysql.route('/mysql_changeprivileges/<int:customer_id>',methods=['GET', 'POST'])
@login_required
def mysql_changeprivileges(customer_id):
    if request.method == 'POST':
        try:
            #customer_oper=request.radio['customer_oper']
            customer_oper=request.form['optionsRadiosInline']
            #customer_id=request.form['customer_id']
            mysql_privilege = mysql_privileges.query.filter_by(id=customer_id).first()
            customer=customers.query.filter_by(id=mysql_privilege.customer_id).first()
            if customer.db_user ==  mysql_privilege.user_name:
                flash("管理员密码禁止修改")
                return render_template('mysqlpt/test.html',test_id=customer_id)
            else:
                if customer_oper == 'readonly':
                    if mysql_privilege.user_status == 0:
                        flash("您目前为只读权限，无需修改")
                        mysql_privilege = mysql_privileges.query.filter_by(id=customer_id)
                        return render_template('mysqlpt/mysql_privileges.html',mysql_privileges=mysql_privilege)
                    else:
                        db=DB(customer.db_ip,int(customer.db_port),customer.db_user,customer.db_pass,customer.db_name)
                        sql="GRANT SELECT ON "+mysql_privilege.user_db+".* to '"+mysql_privilege.user_name+"'@'%';"
                        db.update(sql)
                        db.update('flush privileges;')
                        sql2="update mysql_privileges set user_status=0 where id="+mysql_privilege.id+";"
                        db.update(sql2)
                        #flash("密码更新成功")
                        flash("修改为只读权限")
                        return render_template('mysqlpt/test.html',test_id=sql)
                else:
                    if mysql_privilege.user_status == 1:
                        flash("您目前为读写权限，无需修改")
                        mysql_privilege = mysql_privileges.query.filter_by(id=customer_id)
                        return render_template('mysqlpt/mysql_privileges.html',mysql_privileges=mysql_privilege)
                    else:
                        db=DB(customer.db_ip,int(customer.db_port),customer.db_user,customer.db_pass,customer.db_name)
                        sql="GRANT SELECT ON "+mysql_privilege.user_db+".* to '"+mysql_privilege.user_name+"'@'%';"
                        db.update(sql)
                        db.update('flush privileges;')
                        flash("修改为读写权限")
                        return render_template('mysqlpt/test.html',test_id=sql)
            mysql_privilege = mysql_privileges.query.filter_by(id=customer_id)
            return render_template('mysqlpt/mysql_privileges.html',mysql_privileges=mysql_privilege)
        except Exception as e:
            #customer_oper=request.form['customer_oper']
            return render_template('mysqlpt/test.html',test_id=123)
        mysql_privilege = mysql_privileges.query.filter_by(id=customer_id).first()
        return render_template('mysqlpt/mysql_changeprivileges.html')
         #return render_template('mysqlpt/test.html',test_id=customer_oper)
    else:
        #customer_id=request.form['customer_id']
        mysql_privilege = mysql_privileges.query.filter_by(id=customer_id).first()
        return render_template('mysqlpt/mysql_changeprivileges.html',mysql_privilege=mysql_privilege)
        #return render_template('mysqlpt/mysql_changeprivileges.html')







