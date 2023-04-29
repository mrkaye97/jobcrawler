from flask import request, render_template, redirect, url_for, flash, send_from_directory
from flask_admin.contrib.sqla import ModelView
from werkzeug.security import generate_password_hash, check_password_hash
from . import *
import json
from flask_login import login_user, login_required, logout_user, current_user
from .jobs import get_links_selenium, get_links_soup, crawl_for_postings
from .exceptions import CompanyExistsException, ScrapingException
from werkzeug.exceptions import HTTPException

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
    if os.environ.get('ENV') == 'DEV':
        user_email = "mrkaye97@gmail.com"
        user = Users.query.filter_by(email=user_email).first()
        if user:
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash(f'User with email {user_email} not found.', 'danger')

    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
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
    return render_template('signup.html')

@app.route('/signup', methods=['POST'])
def signup_post():
    email = request.form.get('email')
    first_name = request.form.get('first_name')
    password = request.form.get('password')

    user = Users.query.filter_by(email=email).first()

    if user:
        flash('Email address already exists. Please log in.')
        return redirect(url_for('login'))

    new_user = Users(email=email, first_name=first_name, password_hash=generate_password_hash(password, method='sha256'))

    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('login'))

@app.route('/preferences', methods=['GET', 'POST'])
@login_required
def get_preferences():

    if request.method == 'POST':
        first_name = request.form.get('first_name')
        email_frequency_days = int(request.form.get('email_frequency_days'))
        default_search_regex = request.form.get('default_search_regex')

        current_user.first_name = first_name
        current_user.email_frequency_days = email_frequency_days
        current_user.default_search_regex = default_search_regex
        db.session.commit()

        flash('Preferences updated successfully', 'success')
        return redirect(url_for('get_preferences'))

    return render_template('preferences.html')

@app.route("/searches")
@login_required
def get_searches():
    searches = Searches.\
        query.\
        filter_by(user_id = current_user.get_id()).\
        join(Companies).\
        with_entities(Searches.id.label("search_id"), Companies.id.label("company_id"), Companies.name, Companies.board_url, Searches.search_regex).\
        order_by(Searches.id).\
        all()

    result = [
        {"search_id": search.search_id, "company_id": search.company_id, "name": search.name, "url": search.board_url, "search_regex": search.search_regex}
        for search in searches
    ]

    return result

@app.route('/searches', methods=["POST"])
@login_required
def create_search():
    content = request.json

    app.logger.info("Creating a new search")
    app.logger.info(json.dumps(content))

    company_id = content.get("company_id")
    search_regex = content.get("search_regex")
    user_id = current_user.get_id()

    if company_id and search_regex:
        p = Searches(company_id = company_id, search_regex = search_regex, user_id = user_id)
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
    app.logger.info("Updating a record")
    app.logger.info(json.dumps(request.form))

    company_id = request.form.get("company_id")
    search_regex = request.form.get("search_regex")

    posting = Searches.query.get(id)

    posting.company_id = company_id
    posting.search_regex = search_regex

    db.session.commit()

    return f"Successfully updated the record for id: {id}"

@app.route('/searches/<int:id>', methods = ["DELETE"])
@login_required
def delete_search(id):
    data = Searches.query.get(id)
    db.session.delete(data)
    db.session.commit()

    return f"Successfully deleted {id}"


@app.route("/companies")
def get_companies():
    result = Companies.query.all()

    result = [{key: b.__dict__[key] for key in ["id", "name", "board_url", "job_posting_url_prefix", "scraping_method"]} for b in result]

    return result

@app.route('/companies', methods=["POST"])
def create_company():

    content = request.json

    app.logger.info("Creating a new company")
    app.logger.info(json.dumps(content))

    name = content.get("name")
    board_url = content.get("board_url")
    url_prefix = content.get("job_posting_url_prefix")
    scraping_method = content.get("scraping_method")

    if name and board_url:
        c = Companies(name = name, board_url = board_url, job_posting_url_prefix = url_prefix, scraping_method = scraping_method)

        db.session.add(c)
        db.session.commit()

        record = Companies.query.get(c.id)
        record = record.__dict__
        del record["_sa_instance_state"]

        return record
    else:
        return "Failed", 400

@app.route('/companies/<int:id>', methods=["PUT"])
def update_company(id):
    app.logger.info("Updating a record")
    app.logger.info(json.dumps(request.form))

    name = request.form.get("name")
    board_url = request.form.get("board_url")
    scraping_method = request.form.get("scraping_method")
    url_prefix = request.form.get("job_posting_url_prefix")

    company = Companies.query.get(id)

    company.name = name
    company.board_url = board_url
    company.scraping_method = scraping_method
    company.job_posting_url_prefix = url_prefix

    db.session.commit()

    return f"Successfully updated the record for id: {id}"

@app.route('/companies/<int:id>', methods = ["DELETE"])
def delete_company(id):
    data = Companies.query.get(id)
    db.session.delete(data)
    db.session.commit()

    return f"Successfully deleted {id}"

@app.route('/users/current/default-search')
def get_current_user_default_search():
    u = Users.query.get(current_user.get_id())

    return {
        "default_search": u.default_search_regex,
        "first_name": u.first_name
    }

@app.errorhandler(Exception)
def handle_error(e):
    app.logger.error("Request failed.")
    app.logger.error(f"URL: {request.url}")
    app.logger.error(str(e))
    app.logger.error(e.code)

    if isinstance(e, CompanyExistsException) or isinstance(e, ScrapingException):
        return {"message": str(e)}, 400

    code = 500
    if isinstance(e, HTTPException):
        code = e.code

    if request.path == "/scraping/test":
        return {"message": "Sorry, something went wrong."}, 500

    if code == 404:
        return render_template('404.html')
    else:
        return render_template("error.html")

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(directory = app.static_folder, path = "favicon.ico")

@app.route('/scraping/test', methods = ["POST"])
def test_scraping():
    content = request.json

    posting_url_prefix = content.get("job_posting_url_prefix")
    board_url = content.get("board_url")
    scraping_method = content.get("scraping_method")
    company_name = content.get("name")

    existing = Companies.query.filter_by(name = company_name).count()

    if existing:
        raise CompanyExistsException(name = company_name)

    if scraping_method == "soup":
        links = get_links_soup(
            url = board_url,
            example_prefix = posting_url_prefix
        )
    elif scraping_method == "selenium":
        links = get_links_selenium(
            app = app,
            url = board_url,
            example_prefix = posting_url_prefix
        )
    else:
        return "Could not find that scraping method", 400

    matching_links = [l for l in links if posting_url_prefix in l.get("href")]
    if not matching_links:
        raise Exception(f"No links found matching {posting_url_prefix} at {board_url} with scraping method {scraping_method}")

    return matching_links

@app.route('/scraping/run-crawl-job', methods = ["POST"])
def run_crawl_job():
    app.logger.info("Kicking off scraping job")
    crawl_for_postings(app, db)


