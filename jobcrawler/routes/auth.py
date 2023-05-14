import os

## Flask imports
from flask import request, render_template, redirect, url_for, flash, Blueprint, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user

## Application Imports
from jobcrawler import db
from jobcrawler.models.users import Users

auth_bp = Blueprint('auth_bp', __name__, template_folder='templates', static_folder = "static")

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home_bp.index'))

@auth_bp.route('/login')
def login():
    if os.environ.get('ENV') == 'DEV' and os.environ.get("DEV_AUTOLOGIN") == "True":
        user_email = os.environ.get("DEV_USER_EMAIL")
        dev_is_admin = os.environ.get("DEV_IS_ADMIN_USER") == "True"

        user = Users.query.filter_by(email=user_email).first()
        if not user:
            new_user = Users(
                email = user_email,
                first_name = "Testy",
                password_hash = generate_password_hash("placeholder", method = 'sha256'),
                is_admin = dev_is_admin
            )

            db.session.add(new_user)
            db.session.commit()

            user = db.session.get(Users, new_user.id)

        login_user(user)
        return redirect(url_for('home_bp.index'))

    return render_template('login.html')

@auth_bp.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = Users.query.filter_by(email=email).first()

    # check if the user actually exists
    # take the user-supplied password, hash it, and compare it to the hashed password in the database
    if not user or not check_password_hash(user.password_hash, password):
        flash('Please check your login details and try again.')
        return redirect(url_for('auth_bp.login')) # if the user doesn't exist or password is wrong, reload the page

    # if the above check passes, then we know the user has the right credentials
    login_user(user, remember=remember)
    return redirect(url_for('home_bp.index'))

@auth_bp.route('/signup')
def signup():
    return render_template('signup.html')

@auth_bp.route('/signup', methods=['POST'])
def signup_post():
    email = request.form.get('email')
    first_name = request.form.get('first_name')
    password = request.form.get('password')

    user = Users.query.filter_by(email=email).first()

    if user:
        flash('Email address already exists. Please log in.')
        return redirect(url_for('auth_bp.login'))

    new_user = Users(email=email, first_name=first_name, password_hash=generate_password_hash(password, method='sha256'), is_admin=False)

    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('auth_bp.login'))
