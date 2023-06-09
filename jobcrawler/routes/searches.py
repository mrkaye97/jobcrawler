## Application Imports
from jobcrawler import db
from jobcrawler.core.models import Companies, Searches

## Flask Imports
from flask import request, Blueprint, current_app, render_template
from flask_login import login_required, current_user

## Other imports
import json
import datetime

searches_bp = Blueprint(
    "searches_bp", __name__, template_folder="templates", static_folder="static"
)


@searches_bp.route("/searches/list")
def list_searches():
    current_app.logger.info("Listing searches")
    searches = (
        Searches.query.filter_by(user_id=current_user.get_id())
        .join(Companies)
        .with_entities(
            Searches.id.label("search_id"),
            Companies.id.label("company_id"),
            Companies.name,
            Companies.board_url,
            Searches.search_regex,
        )
        .order_by(Searches.id)
    )

    result = list(
        map(
            lambda x: {
                "search_id": x.search_id,
                "company_id": x.company_id,
                "name": x.name,
                "url": x.board_url,
                "search_regex": x.search_regex,
            },
            searches,
        )
    )

    return result


@searches_bp.route("/searches")
@login_required
def get_searches():
    searches = (
        Searches.query.filter_by(user_id=current_user.get_id())
        .join(Companies)
        .with_entities(
            Searches.id.label("search_id"),
            Companies.id.label("company_id"),
            Companies.name,
            Companies.board_url,
            Searches.search_regex,
        )
        .order_by(Searches.id)
    )

    return render_template("searches.html", searches=searches)


@searches_bp.route("/searches/<int:id>")
@login_required
def get_search(id):
    record = db.session.get(Searches, id)
    record = record.__dict__

    del record["_sa_instance_state"]

    return record


@searches_bp.route("/searches", methods=["POST"])
@login_required
def create_search():
    content = request.json

    current_app.logger.info("Creating a new search")
    current_app.logger.info(json.dumps(content))

    company_id = content.get("company_id")
    search_regex = content.get("search_regex")
    user_id = current_user.get_id()

    if company_id and search_regex:
        p = Searches(company_id=company_id, search_regex=search_regex, user_id=user_id)
        db.session.add(p)
        db.session.commit()

        id = p.id
        record = db.session.get(Searches, id)
        record = record.__dict__
        del record["_sa_instance_state"]

        return record
    else:
        return "Failed", 400


@searches_bp.route("/searches/<int:id>", methods=["PUT"])
@login_required
def update_search(id):
    current_app.logger.info("Updating a record")

    content = request.json
    current_app.logger.info(json.dumps(content))

    company_id = content.get("company_id")
    search_regex = content.get("search_regex")

    posting = db.session.get(Searches, id)

    posting.company_id = company_id
    posting.search_regex = search_regex
    posting.updated_at = datetime.datetime.now()

    db.session.commit()

    record = db.session.get(Searches, id)
    record = record.__dict__
    del record["_sa_instance_state"]

    return record


@searches_bp.route("/searches/<int:id>", methods=["DELETE"])
@login_required
def delete_search(id):
    current_app.logger.info("Deleting a search")
    data = db.session.get(Searches, id)
    db.session.delete(data)
    db.session.commit()

    return f"Successfully deleted {id}"
