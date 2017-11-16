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
import os,json,string
from datetime import datetime
from random import choice
import datetime,MySQLdb,time
from .forms import LoginForm
from flask.ext.login import login_user, logout_user,current_user
from flask.ext.login import login_required



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
        mysql_privilege = mysql_privileges.query.filter_by(is_delete=0).order_by(desc(mysql_privileges.id)).all()
        return render_template('mysqlpt/mysql_index.html',mysql_privileges=mysql_privilege)
        #return render_template('mysqlpt/mysql_privileges.html',mysql_privileges=mysql_privilege,customer_id=customer_id)

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
            mysql_privilege=mysql_privileges(customer_id=customer.id,user_name=customer.db_user,user_pass=customer.db_pass,user_ip=customer.db_ip,user_db=customer.db_name,is_delete=1)
            db.session.add(mysql_privilege)
            db.session.commit()
        mysql_privilege= mysql_privileges.query.filter_by(customer_id=customer_id,is_delete=0)
        return render_template('mysqlpt/mysql_privileges.html',mysql_privileges=mysql_privilege,customer_id=customer_id)

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
                    db1=DB(customer.db_ip,int(customer.db_port),customer.db_user,customer.db_pass,customer.db_name)
                    sql="update mysql.user set authentication_string=password(\'"+password02+"\') where user=\'"+mysql_privilege.user_name+"\'"
                    db1.update(sql)
                    db1.update('flush privileges;')
                    t1 = mysql_privileges.query.filter_by(user_name=mysql_privilege.user_name,is_delete=0)
                    for i in t1:
                        i.user_pass=password02
                        db.session.add(i)
                    db.session.commit()
                    flash("密码更新成功")
        except Exception as e:
            return render_template('mysqlpt/test.html',test_id='您访问的网页不存在，请稍后再试！')
        return redirect(url_for('mysql.mysql_index'))
    else:
        return render_template('mysqlpt/mysql_resetpassword.html',customer_id=customer_id)

@mysql.route('/mysql_changeprivileges/<int:customer_id>',methods=['GET', 'POST'])
@login_required
##user_status=0 只读权限
##user_status=1 读写权限
##user_status=2 无权限
def mysql_changeprivileges(customer_id):
    if request.method == 'POST':
        try:
            customer_oper=request.form['optionsRadiosInline']
            mysql_privilege = mysql_privileges.query.filter_by(id=customer_id).first()
            customer=customers.query.filter_by(id=mysql_privilege.customer_id).first()
            if customer.db_user ==  mysql_privilege.user_name:
                flash("管理员密码禁止修改")
            else:
                if customer_oper == 'readonly':
                    if mysql_privilege.user_status == 0:
                        flash("您目前为只读权限，无需修改")
                    else:
                        db1=DB(customer.db_ip,int(customer.db_port),customer.db_user,customer.db_pass,customer.db_name)
                        if mysql_privilege.user_status == 1:
                            sql1="REVOKE SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER, CREATE TEMPORARY TABLES, " \
                                "LOCK TABLES, EXECUTE, CREATE VIEW, SHOW VIEW, CREATE ROUTINE, ALTER ROUTINE, EVENT, TRIGGER ON "\
                                +mysql_privilege.user_db+".* FROM '"+mysql_privilege.user_name+"'@'%';"
                            db1.update(sql1)
                            db1.update('flush privileges;')
                        sql2="GRANT SELECT ON "+mysql_privilege.user_db+".* to '"+mysql_privilege.user_name+"'@'%';"
                        db1.update(sql2)
                        db1.update('flush privileges;')
                        mysql_privilege.user_status=0
                        db.session.add(mysql_privilege)
                        db.session.commit()
                        flash("修改为只读权限")

                else:
                    if customer_oper == 'readwrite':
                        if mysql_privilege.user_status == 1:
                            flash("您目前为读写权限，无需修改")
                        else:
                            db1=DB(customer.db_ip,int(customer.db_port),customer.db_user,customer.db_pass,customer.db_name)
                            if mysql_privilege.user_status == 0:
                                sql1="REVOKE SELECT ON "+mysql_privilege.user_db+".* FROM '"+mysql_privilege.user_name+"'@'%';"
                                db1.update(sql1)
                                db1.update('flush privileges;')
                            sql2="GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER, CREATE TEMPORARY TABLES, " \
                            "LOCK TABLES, EXECUTE, CREATE VIEW, SHOW VIEW, CREATE ROUTINE, ALTER ROUTINE, EVENT, TRIGGER ON "\
                            +mysql_privilege.user_db+".* to '"+mysql_privilege.user_name+"'@'%';"
                            db1.update(sql2)
                            db1.update('flush privileges;')
                            mysql_privilege.user_status=1
                            db.session.add(mysql_privilege)
                            db.session.commit()
                            flash("修改为读写权限")
                            return redirect(url_for('mysql.mysql_index'))
                    else:
                        if mysql_privilege.user_status == 2:
                            flash("您目前为无权限，无需修改")
                        else:
                            db1=DB(customer.db_ip,int(customer.db_port),customer.db_user,customer.db_pass,customer.db_name)
                            if mysql_privilege.user_status == 0:
                                sql1="REVOKE SELECT ON "+mysql_privilege.user_db+".* FROM '"+mysql_privilege.user_name+"'@'%';"
                                db1.update(sql1)
                                db1.update('flush privileges;')
                            elif mysql_privilege.user_status == 1:
                                sql1="REVOKE SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER, CREATE TEMPORARY TABLES, " \
                                "LOCK TABLES, EXECUTE, CREATE VIEW, SHOW VIEW, CREATE ROUTINE, ALTER ROUTINE, EVENT, TRIGGER ON "\
                                +mysql_privilege.user_db+".* FROM '"+mysql_privilege.user_name+"'@'%';"
                                db1.update(sql1)
                                db1.update('flush privileges;')
                            else:
                                db1.close()
                                flash("您目前为无权限，无需修改")
                            mysql_privilege.user_status=2
                            db.session.add(mysql_privilege)
                            db.session.commit()
                            flash("目前对"+mysql_privilege.user_db+"无访问权限")
                        return redirect(url_for('mysql.mysql_index'))
        except Exception as e:
            return render_template('mysqlpt/test.html',test_id='您访问的页面不存在，请稍后重试')
        return redirect(url_for('mysql.mysql_index'))
    else:
        mysql_privilege = mysql_privileges.query.filter_by(id=customer_id,is_delete=0).first()
        return render_template('mysqlpt/mysql_changeprivileges.html',mysql_privilege=mysql_privilege)

@mysql.route('/mysql_dropusers/<int:customer_id>',methods=['GET', 'POST'])
@login_required
def mysql_dropusers(customer_id):
    if request.method == 'POST':
        try:
            customer_oper=request.form['optionsRadiosInline']
            mysql_privilege = mysql_privileges.query.filter_by(id=customer_id).first()
            customer=customers.query.filter_by(id=mysql_privilege.customer_id).first()
            db1=DB(customer.db_ip,int(customer.db_port),customer.db_user,customer.db_pass,customer.db_name)
            if customer.db_user ==  mysql_privilege.user_name:
                flash("管理员密码禁止修改")
            else:
                if customer_oper == 'yes':
                    if mysql_privilege.user_status == 0:
                        sql1="REVOKE SELECT ON "+mysql_privilege.user_db+".* FROM '"+mysql_privilege.user_name+"'@'%';"
                        db1.update(sql1)
                        db1.update('flush privileges;')
                    elif mysql_privilege.user_status == 1:
                        sql1="REVOKE SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER, CREATE TEMPORARY TABLES, " \
                        "LOCK TABLES, EXECUTE, CREATE VIEW, SHOW VIEW, CREATE ROUTINE, ALTER ROUTINE, EVENT, TRIGGER ON "\
                        +mysql_privilege.user_db+".* FROM '"+mysql_privilege.user_name+"'@'%';"
                        db1.update(sql1)
                        db1.update('flush privileges;')
                    mysql_privilege.is_delete=1
                    db.session.add(mysql_privilege)
                    db.session.commit()
                    mysql_privilege.user_status=2
                    db.session.add(mysql_privilege)
                    db.session.commit()
                    mysql_privilege_01= mysql_privileges.query.filter_by(user_name=mysql_privilege.user_name,user_ip=mysql_privilege.user_ip,is_delete=0).count()
                    if mysql_privilege_01 == 0:
                        sql1="drop user '"+mysql_privilege.user_name+"'@'%';"
                        db1.update(sql1)
                        db1.update('flush privileges;')
                    flash("账号"+mysql_privilege.user_name+"对"+mysql_privilege.user_db+"数据库的访问权限已收回")
                else:
                    flash("权限没有变更")
            return redirect(url_for('mysql.mysql_index'))
        except Exception as e:
            return render_template('mysqlpt/test.html',test_id='您访问的页面不存在，请稍后重试')
    else:
        mysql_privilege = mysql_privileges.query.filter_by(id=customer_id,is_delete=0).first()
        return render_template('mysqlpt/mysql_dropuser.html',mysql_privilege=mysql_privilege)

@mysql.route('/mysql_createuser/<int:customer_id>',methods=['GET', 'POST'])
@login_required
def mysql_createuser(customer_id):
    if request.method == 'POST':
        user_name = request.form['user_name']
        user_pass = request.form['user_pass']
        user_db = request.form['user_db']
        user_desc=request.form['user_desc']
        privilege_id = int(request.form['privilege_id'])
        #return render_template('mysqlpt/test.html',test_id=u'您访问的页面不存在，请稍后重试  %s %s' %(customer_id,user_db))
        mysql_privilege = mysql_privileges.query.filter_by(customer_id=customer_id).first()
        customer=customers.query.filter_by(id=mysql_privilege.customer_id).first()
        db1=DB(customer.db_ip,int(customer.db_port),customer.db_user,customer.db_pass,customer.db_name)
        mysql_privilege_tmp = mysql_privileges.query.filter_by(user_ip=mysql_privilege.user_ip,user_name=user_name,is_delete=0).all()
        if mysql_privilege_tmp:
            for i in mysql_privilege_tmp:
                if i.user_db == user_db:
                    flash(u'%s 账号及数据库权限已存在，不能重复添加' %user_db)
                    backhost = mysql_privileges.query.filter_by(customer_id=customer_id).group_by(mysql_privileges.user_db)
                    return render_template('mysqlpt/mysql_createuser.html',back_hosts=backhost)
            flash(u'%s 账号已存在，密码不变更；如有疑问请联系管理员' %user_db)
            if privilege_id == 0:
                sql2="GRANT SELECT ON "+user_db+".* to '"+user_name+"'@'%';"
                db1.update(sql2)
                db1.update('flush privileges;')
            else:
                sql2="GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER, CREATE TEMPORARY TABLES, " \
                            "LOCK TABLES, EXECUTE, CREATE VIEW, SHOW VIEW, CREATE ROUTINE, ALTER ROUTINE, EVENT, TRIGGER ON "\
                            +user_db+".* to '"+user_name+"'@'%';"
                db1.update(sql2)
                db1.update('flush privileges;')
            mysql_privilege_01=mysql_privileges(user_name=user_name,user_ip=mysql_privilege.user_ip,user_db=user_db,user_status=privilege_id,user_pass=mysql_privilege.user_pass,
                                                user_desc=user_desc,is_delete=0,customer_id=customer_id)
            db.session.add(mysql_privilege_01)
            db.session.commit()
            return redirect(url_for('mysql.mysql_index'))
        sql1="create user '"+ user_name+"'@'%' IDENTIFIED by '"+user_pass+"';"
        db1.update(sql1)
        if privilege_id == 0:
            sql2="GRANT SELECT ON "+user_db+".* to '"+user_name+"'@'%';"
            db1.update(sql2)
            db1.update('flush privileges;')
        else:
            sql2="GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER, CREATE TEMPORARY TABLES, " \
                        "LOCK TABLES, EXECUTE, CREATE VIEW, SHOW VIEW, CREATE ROUTINE, ALTER ROUTINE, EVENT, TRIGGER ON "\
                        +user_db+".* to '"+user_name+"'@'%';"
            db1.update(sql2)
            db1.update('flush privileges;')
        mysql_privilege_01=mysql_privileges(user_name=user_name,user_ip=mysql_privilege.user_ip,user_db=user_db,user_status=privilege_id,user_pass=user_pass,
                                            user_desc=user_desc,is_delete=0,customer_id=customer_id)
        db.session.add(mysql_privilege_01)
        db.session.commit()
        flash(u'%s 账号创建完成' %user_db)
        return redirect(url_for('mysql.mysql_index'))
    backhost = mysql_privileges.query.filter_by(customer_id=customer_id).group_by(mysql_privileges.user_db)
    return render_template('mysqlpt/mysql_createuser.html',back_hosts=backhost)



