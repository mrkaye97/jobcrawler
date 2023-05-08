## Application Imports
from jobcrawler import db
from jobcrawler.models.searches import Searches
from jobcrawler.models.companies import Companies

## Flask Imports
from flask import request, Blueprint, current_app, render_template
from flask_login import login_required, current_user

## Other imports
import json

searches_bp = Blueprint('searches_bp', __name__, template_folder='templates', static_folder = "static")

@searches_bp.route("/searches/list")
def list_searches():
    searches = Searches.\
        query.\
        filter_by(user_id = current_user.get_id()).\
        join(Companies).\
        with_entities(Searches.id.label("search_id"), Companies.id.label("company_id"), Companies.name, Companies.board_url, Searches.search_regex).\
        order_by(Searches.id)

    result = [
        {"search_id": search.search_id, "company_id": search.company_id, "name": search.name, "url": search.board_url, "search_regex": search.search_regex}
        for search in searches
    ]

    return result

@searches_bp.route("/searches")
@login_required
def get_searches():
    searches = Searches.\
        query.\
        filter_by(user_id = current_user.get_id()).\
        join(Companies).\
        with_entities(Searches.id.label("search_id"), Companies.id.label("company_id"), Companies.name, Companies.board_url, Searches.search_regex).\
        order_by(Searches.id)

    return render_template(
        "searches.html",
        searches = searches
    )

@searches_bp.route('/searches', methods=["POST"])
@login_required
def create_search():
    content = request.json

    current_app.logger.info("Creating a new search")
    current_app.logger.info(json.dumps(content))

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

        current_app.logger.info(json.dumps(record))

        return record
    else:
        return "Failed", 400

@searches_bp.route('/searches/<int:id>', methods=["PUT"])
@login_required
def update_search(id):
    current_app.logger.info("Updating a record")
    current_app.logger.info(json.dumps(request.form))

    company_id = request.form.get("company_id")
    search_regex = request.form.get("search_regex")

    posting = Searches.query.get(id)

    posting.company_id = company_id
    posting.search_regex = search_regex

    db.session.commit()

    return f"Successfully updated the record for id: {id}"

@searches_bp.route('/searches/<int:id>', methods = ["DELETE"])
@login_required
def delete_search(id):
    data = Searches.query.get(id)
    db.session.delete(data)
    db.session.commit()

    return f"Successfully deleted {id}"
