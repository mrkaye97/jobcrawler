from . import app
from flask import request, jsonify, render_template, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from . import *
import json
from flask_login import login_user, login_required, logout_user, current_user

@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    # login code goes here
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = Users.query.filter_by(email=email).first()

    # check if the user actually exists
    # take the user-supplied password, hash it, and compare it to the hashed password in the database
    if not user or not check_password_hash(user.password_hash, password):
        flash('Please check your login details and try again.')
        return redirect(url_for('login')) # if the user doesn't exist or password is wrong, reload the page

    # if the above check passes, then we know the user has the right credentials
    login_user(user, remember=remember)
    return redirect(url_for('index'))

@app.route('/signup')
def signup():
    return render_template('signup.html', host = os.environ.get("HOSTNAME"), protocol = os.environ.get("PROTOCOL"))

@app.route('/signup', methods=['POST'])
def signup_post():
    # code to validate and add user to database goes here
    email = request.form.get('email')
    first_name = request.form.get('first_name')
    password = request.form.get('password')

    user = Users.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database

    if user: # if a user is found, we want to redirect back to signup page so user can try again
        flash('Email address already exists. Please log in.')
        return redirect(url_for('login'))

    # create a new user with the form data. Hash the password so the plaintext version isn't saved.
    new_user = Users(email=email, first_name=first_name, password_hash=generate_password_hash(password, method='sha256'))

    # add the new user to the database
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('login'))

## CRUD operations for a job search
@app.route("/searches")
@login_required
def get_searches():
    searches = Searches.\
        query.\
        filter_by(user_id = current_user.get_id()).\
        join(Companies).\
        with_entities(Searches.id.label("search_id"), Companies.id.label("company_id"), Companies.name, Companies.board_url, Searches.search_text).\
        order_by(Searches.id).\
        all()

    result = [
        {"search_id": search.search_id, "company_id": search.company_id, "name": search.name, "url": search.board_url, "search_text": search.search_text}
        for search in searches
    ]

    app.logger.info(json.dumps(result))
    return result

@app.route('/searches', methods=["POST"])
@login_required
def create_search():
    content = request.json

    app.logger.info(request.json)
    company_id = content.get("company_id")
    search_text = content.get("search_text")
    user_id = current_user.get_id()

    if company_id and search_text:
        p = Searches(company_id = company_id, search_text = search_text, user_id = user_id)
        db.session.add(p)
        db.session.commit()

        id = p.id
        record = Searches.query.get(id)
        record = record.__dict__
        del record["_sa_instance_state"]

        app.logger.info(json.dumps(record))

        return record
    else:
        return "Failed", 400

@app.route('/searches/<int:id>', methods=["PUT"])
@login_required
def update_search(id):
    company_id = request.form.get("company_id")
    search_text = request.form.get("search_text")

    app.logger.info("Company Id: ", company_id)
    app.logger.info("Search: ", search_text)

    posting = Searches.query.get(id)

    posting.company_id = company_id
    posting.search_text = search_text

    db.session.commit()

    return f"Successfully updated the record for id: {id}"

@app.route('/searches/<int:id>', methods = ["DELETE"])
@login_required
def delete_search(id):
    app.logger.info("Deleting: ", id)
    data = Searches.query.get(id)
    db.session.delete(data)
    db.session.commit()
    return jsonify(f"Successfully deleted {id}")

@app.route('/searches', methods=["DELETE"])
@login_required
def delete_search_by_name():
    company = request.form.get("company")
    url = request.form.get("url")
    search_text = request.form.get("search_text")

    app.logger.info("Deleting: ", company, url, search_text)
    data = Searches.query.filter_by(company = company, url = url, search_text = search_text).first()
    app.logger.info(data)
    db.session.delete(data)
    db.session.commit()
    return jsonify(f"Successfully deleted")


## CRUD operations for a company
@app.route("/companies")
def get_companies():
    result = Companies.query.all()
    return [{key: b.__dict__[key] for key in ["id", "name", "board_url", "scraping_method"]} for b in result]

@app.route('/companies', methods=["POST"])
def create_company():
    content = request.json
    name = content.get("name")
    board_url = content.get("board_url")
    scraping_method = content.get("scraping_method")

    if name and board_url:
        c = Companies(name = name, board_url = board_url, scraping_method = scraping_method)
        db.session.add(c)
        db.session.commit()

        id = c.id

        record = Companies.query.get(id)
        record = record.__dict__
        del record["_sa_instance_state"]

        return record
    else:
        return "Failed", 400

@app.route('/companies/<int:id>', methods=["PUT"])
def update_company(id):
    name = request.form.get("name")
    board_url = request.form.get("board_url")
    scraping_method = request.form.get("scraping_method")

    app.logger.info("Name: ", name)
    app.logger.info("URL:", board_url)
    app.logger.info("Scraping method: ", scraping_method)

    company = Companies.query.get(id)

    company.name = name
    company.board_url = board_url
    company.scraping_method = scraping_method

    db.session.commit()

    return f"Successfully updated the record for id: {id}"

@app.route('/companies/<int:id>', methods = ["DELETE"])
def delete_company(id):
    app.logger.info("Deleting: ", id)
    data = Companies.query.get(id)
    db.session.delete(data)
    db.session.commit()
    return jsonify(f"Successfully deleted {id}")
