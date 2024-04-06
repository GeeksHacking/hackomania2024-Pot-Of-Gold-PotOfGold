# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import json
from datetime import datetime

from flask_restx import Resource, Api

import flask
from flask import render_template, redirect, request, url_for
from flask_login import (
    current_user,
    login_user,
    logout_user
)

from flask_dance.contrib.github import github

from apps import db, login_manager
from apps.authentication import blueprint
from apps.authentication.forms import LoginForm, CreateAccountForm
from apps.authentication.models import Users
from apps.models import Reports

from apps.authentication.util import verify_pass, generate_token

# Bind API -> Auth BP
api = Api(blueprint)

@blueprint.route('/')
def route_default():
    return redirect(url_for('authentication_blueprint.login'))

# Login & Registration

@blueprint.route("/github")
def login_github():
    """ Github login """
    if not github.authorized:
        return redirect(url_for("github.login"))

    res = github.get("/user")
    return redirect(url_for('home_blueprint.index'))

# User Page
@blueprint.route('/user')
def user_page():
    return render_template('custom/user.html')

# Insert test data into 'Reports' Database
@blueprint.route('/insert')
def insert():
    # Insert data into the database
    # Create a new 'Report' object
    new_report = Reports(title='Test Report 3',
                         description='Test description',
                         created_at=datetime.now(),
                         updated_at=datetime.now(),
                         base64_image='iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAApgAAAKYB3X3/OAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAANCSURBVEiJtZZPbBtFFMZ/M7ubXdtdb1xSFyeilBapySVU8h8OoFaooFSqiihIVIpQBKci6KEg9Q6H9kovIHoCIVQJJCKE1ENFjnAgcaSGC6rEnxBwA04Tx43t2FnvDAfjkNibxgHxnWb2e/u992bee7tCa00YFsffekFY+nUzFtjW0LrvjRXrCDIAaPLlW0nHL0SsZtVoaF98mLrx3pdhOqLtYPHChahZcYYO7KvPFxvRl5XPp1sN3adWiD1ZAqD6XYK1b/dvE5IWryTt2udLFedwc1+9kLp+vbbpoDh+6TklxBeAi9TL0taeWpdmZzQDry0AcO+jQ12RyohqqoYoo8RDwJrU+qXkjWtfi8Xxt58BdQuwQs9qC/afLwCw8tnQbqYAPsgxE1S6F3EAIXux2oQFKm0ihMsOF71dHYx+f3NND68ghCu1YIoePPQN1pGRABkJ6Bus96CutRZMydTl+TvuiRW1m3n0eDl0vRPcEysqdXn+jsQPsrHMquGeXEaY4Yk4wxWcY5V/9scqOMOVUFthatyTy8QyqwZ+kDURKoMWxNKr2EeqVKcTNOajqKoBgOE28U4tdQl5p5bwCw7BWquaZSzAPlwjlithJtp3pTImSqQRrb2Z8PHGigD4RZuNX6JYj6wj7O4TFLbCO/Mn/m8R+h6rYSUb3ekokRY6f/YukArN979jcW+V/S8g0eT/N3VN3kTqWbQ428m9/8k0P/1aIhF36PccEl6EhOcAUCrXKZXXWS3XKd2vc/TRBG9O5ELC17MmWubD2nKhUKZa26Ba2+D3P+4/MNCFwg59oWVeYhkzgN/JDR8deKBoD7Y+ljEjGZ0sosXVTvbc6RHirr2reNy1OXd6pJsQ+gqjk8VWFYmHrwBzW/n+uMPFiRwHB2I7ih8ciHFxIkd/3Omk5tCDV1t+2nNu5sxxpDFNx+huNhVT3/zMDz8usXC3ddaHBj1GHj/As08fwTS7Kt1HBTmyN29vdwAw+/wbwLVOJ3uAD1wi/dUH7Qei66PfyuRj4Ik9is+hglfbkbfR3cnZm7chlUWLdwmprtCohX4HUtlOcQjLYCu+fzGJH2QRKvP3UNz8bWk1qMxjGTOMThZ3kvgLI5AzFfo379UAAAAASUVORK5CYII=',
                         category='Test Category',
                         location='Test Location',
                         status='Open')
    # Add the new object to the database
    db.session.add(new_report)
    # Commit the changes
    db.session.commit()
    # Return a message
    return 'Data inserted into the database'

# Admin Page
@blueprint.route('/admin')
def admin_page():
    # Select every row from the 'Reports' table
    reports = Reports.query.all()

    # Print for debugging
    for report in reports:
        print(report.title, report.description, report.created_at, report.updated_at)
    
    return render_template('custom/admin.html', reports=reports)

# Review Page
@blueprint.route('/admin/review/<int:id>')
def review_page(id):
    report = Reports.query.get(id)
    return render_template('custom/review.html', report=report)

# Pending Page
@blueprint.route('/admin/pending', methods=['POST'])
def pending_page():
    id = request.form['id']
    report = Reports.query.get(id)
    report.status = "Pending"
    db.session.commit()
    return redirect(url_for('authentication_blueprint.admin_page'))
    # return render_template('custom/review.html', report=report)

# Approved Page
@blueprint.route('/admin/approved', methods=['POST'])
def approved_page():
    id = request.form['id']
    report = Reports.query.get(id)
    report.status = "Approved"
    db.session.commit()
    return redirect(url_for('authentication_blueprint.admin_page'))
    # return render_template('custom/review.html', report=report)

@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(request.form)

    if flask.request.method == 'POST':

        # read form data
        username = request.form['username']
        password = request.form['password']

        #return 'Login: ' + username + ' / ' + password

        # Locate user
        user = Users.query.filter_by(username=username).first()

        # Check the password
        if user and verify_pass(password, user.password):
            login_user(user)
            return redirect(url_for('authentication_blueprint.route_default'))

        # Something (user or pass) is not ok
        return render_template('accounts/login.html',
                               msg='Wrong user or password',
                               form=login_form)

    if current_user.is_authenticated:
        return redirect(url_for('home_blueprint.index'))
    else:
        return render_template('accounts/login.html',
                               form=login_form) 


@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    create_account_form = CreateAccountForm(request.form)
    if 'register' in request.form:

        username = request.form['username']
        email = request.form['email']

        # Check usename exists
        user = Users.query.filter_by(username=username).first()
        if user:
            return render_template('accounts/register.html',
                                   msg='Username already registered',
                                   success=False,
                                   form=create_account_form)

        # Check email exists
        user = Users.query.filter_by(email=email).first()
        if user:
            return render_template('accounts/register.html',
                                   msg='Email already registered',
                                   success=False,
                                   form=create_account_form)

        # else we can create the user
        user = Users(**request.form)
        db.session.add(user)
        db.session.commit()

        # Delete user from session
        logout_user()

        return render_template('accounts/register.html',
                               msg='User created successfully.',
                               success=True,
                               form=create_account_form)

    else:
        return render_template('accounts/register.html', form=create_account_form)

@api.route('/login/jwt/', methods=['POST'])
class JWTLogin(Resource):
    def post(self):
        try:
            data = request.form

            if not data:
                data = request.json

            if not data:
                return {
                           'message': 'username or password is missing',
                           "data": None,
                           'success': False
                       }, 400
            # validate input
            user = Users.query.filter_by(username=data.get('username')).first()
            if user and verify_pass(data.get('password'), user.password):
                try:

                    # Empty or null Token
                    if not user.api_token or user.api_token == '':
                        user.api_token = generate_token(user.id)
                        user.api_token_ts = int(datetime.utcnow().timestamp())
                        db.session.commit()

                    # token should expire after 24 hrs
                    return {
                        "message": "Successfully fetched auth token",
                        "success": True,
                        "data": user.api_token
                    }
                except Exception as e:
                    return {
                               "error": "Something went wrong",
                               "success": False,
                               "message": str(e)
                           }, 500
            return {
                       'message': 'username or password is wrong',
                       'success': False
                   }, 403
        except Exception as e:
            return {
                       "error": "Something went wrong",
                       "success": False,
                       "message": str(e)
                   }, 500


@blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('authentication_blueprint.login')) 

# Errors

@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('home/page-403.html'), 403


@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template('home/page-403.html'), 403


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template('home/page-404.html'), 404


@blueprint.errorhandler(500)
def internal_error(error):
    return render_template('home/page-500.html'), 500
