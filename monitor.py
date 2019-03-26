#!/usr/bin/python
# -*- coding: utf-8 -*-
from requests import get
from flask import Flask, render_template, request, redirect, session
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, PasswordField, SelectField, FileField
from wtforms.widgets import TextArea, TextInput
from wtforms.validators import DataRequired, Email
import time


TIME_UPDATE = time.time()

key = '13cf673e9db6fbf3f096ee120086c8925939cd4d'
secret = 'eacbcadbefc1ae089c11d216bfc0785bf233152d'

def get_attempts(handle):
    map_request = 'http://codeforces.com/api/user.status?handle={}'.format(handle)
    attempts = []
    request = get(map_request).json()
    if request['status'] != 'OK':
        return attempts
    if handle == 'AffirmativeActor':
        print()
        for i in request['result']:
            print(i)
    for i in request['result']:
        attempt = i['problem']
        contestId = attempt['contestId']
        index = attempt['index']
        if(i['verdict'] == 'OK'):
            attempts.append(str(contestId) + index)
    return attempts

def load_groupsofproblems():
    file = open('static/groupsofproblems.txt', 'r', encoding='utf-8')
    data = file.readlines()
    buffer = []
    sz = len(data)

    if(len(data) % 2 != 0):
        sz -= 1
    for i in range(0, sz, 2):
        title = data[i].strip()
        problems = data[i + 1].split()
        buffer.append((title, problems))
    file.close()
    return buffer



ADMINS = dict()
users = []
groupsofproblems = []
tables = []


def update_users():
    global users
    file = open('static/users.txt', 'r', encoding='utf-8')
    users = file.readlines()
    for i in range(len(users)):
        users[i] = users[i].strip()
    file.close()

def update_problems():
    global groupsofproblems, tables
    groupsofproblems = load_groupsofproblems()
    groupsofproblems.reverse()
    tables = []
    for title, problems in groupsofproblems:
        problems_buffer = []
        cnt = 0
        for i in problems:
            name = ''
            number = ''
            for j in i:
                if j.isdigit():
                    number += j
                else:
                    name += j

            problems_buffer.append((chr(cnt + ord('A')), number, name))
            cnt += 1

        tables.append((title, problems_buffer, []))

        for user in users:
            solved = get_attempts(user)
            statusofproblems = []
            cnt_solved = 0
            for problem in problems:
                if problem in solved:
                    statusofproblems.append('+')
                    cnt_solved += 1
                else:
                    statusofproblems.append('-')

            tables[-1][2].append((user, statusofproblems, cnt_solved))
        tables[-1][2].sort(key=lambda x: -x[2])


    global TIME_UPDATE
    TIME_UPDATE = time.time()


def load_admins():
    file = open('static/admins.txt', 'r', encoding='utf-8')
    data = file.readlines()

    for i in data:
        buffer = i.split()
        log, pas = buffer[0], buffer[1]
        ADMINS[log] = pas

    file.close()


load_admins()
update_users()
update_problems()


app = Flask(__name__)
app.config['SECRET_KEY'] = 'e70lIUUoXRKlXc5VUBmiJ9Hdi'


@app.route('/', methods=['GET', 'POST'])
def mainpage():
    global TIME_UPDATE
    NOW_TIME = time.time()
    if(NOW_TIME - TIME_UPDATE >= 60):
        TIME_UPDATE = NOW_TIME
        update_problems()
    return render_template('index.html', TABLE=tables, session=session, last_update=int(NOW_TIME - TIME_UPDATE))

@app.route('/update/1', methods=['GET', 'POST'])
def now_update_problems():
    update_problems()
    return redirect('/')

@app.route('/update/2', methods=['GET', 'POST'])
def now_update_users():
    update_users()
    update_problems()
    return redirect('/')


@app.errorhandler(404)
def not_found_error(error):
    return redirect('/')

class LoginForm(FlaskForm):
    username = StringField('Login:', validators=[DataRequired()], widget=TextInput())
    password = StringField('Password:', validators=[DataRequired()], widget=TextInput())
    submit = SubmitField('Отправить')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if 'login' in session:
        return redirect('/')
    form = LoginForm()

    if form.validate_on_submit():
        login = form.username.data
        password = form.password.data
        if login in ADMINS:
            if(ADMINS[login] == password):
                session['login'] = login
                return redirect('/')
            else:
                return render_template('login.html', form = form, status=1)
        else:
            return render_template('login.html', form=form, status=1)
    return render_template('login.html', form = form)

@app.route('/logout')
def logout():
    session.pop('login',0)
    return redirect('/')


@app.route('/edittasks', methods=['GET', 'POST'])
def edittasks():
    if 'login' not in session:
        return redirect('/')

    NOW_TIME = time.time()
    if request.method == 'GET':
        file = open('static/groupsofproblems.txt', 'r', encoding='utf-8')
        data = file.read()
        file.close()
        return render_template('editfile.html',session=session, nowtitle='Edit Tasks',
                               defaulttext=data, last_update=int(NOW_TIME - TIME_UPDATE))
    if request.method == 'POST':
        text = request.form['textfield']
        file = open('static/groupsofproblems.txt', 'w', encoding='utf-8')
        data = file.writelines(text.split('\n'))
        file.close()
        return redirect('/update/1')

@app.route('/editusers', methods=['GET', 'POST'])
def editusers():
    if 'login' not in session:
        return redirect('/')

    NOW_TIME = time.time()
    if request.method == 'GET':
        file = open('static/users.txt', 'r', encoding='utf-8')
        data = file.read()
        file.close()
        return render_template('editfile.html',session=session, nowtitle='Edit users',
                               defaulttext=data, last_update=max(0, int(NOW_TIME - TIME_UPDATE)))
    if request.method == 'POST':
        text = request.form['textfield'].split()
        file = open('static/users.txt', 'w', encoding='utf-8')
        data = file.write('\n'.join(text))
        file.close()
        return redirect('/update/2')

@app.route('/editadmins', methods=['GET', 'POST'])
def editadmins():
    if 'login' not in session:
        return redirect('/')

    NOW_TIME = time.time()
    if request.method == 'GET':
        file = open('static/admins.txt', 'r', encoding='utf-8')
        data = file.read()
        file.close()
        return render_template('editfile.html',session=session, nowtitle='Edit admins',
                               defaulttext=data, last_update=max(0, int(NOW_TIME - TIME_UPDATE)))
    if request.method == 'POST':
        text = request.form['textfield']
        file = open('static/admins.txt', 'w', encoding='utf-8')
        data = file.writelines(text.split('\n'))
        file.close()
        load_admins()
        return redirect('/')

DEBUG = True
if DEBUG:
    app.run(port=8080, host='127.0.0.1')
