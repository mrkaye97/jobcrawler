## Application Imports
from jobcrawler import db
from jobcrawler.models.companies import Companies

## Flask Imports
from flask import request, Blueprint, current_app, render_template, jsonify

## Misc Imports
import json

companies_bp = Blueprint(
    "companies_bp", __name__, template_folder="templates", static_folder="static"
)

@companies_bp.route("/flags/add-company/<int:user_id>")
def has_seen_company_tips_modal(user_id):
    return jsonify(True)

@companies_bp.route("/companies/list")
def list_companies():
    return list(
        map(
            lambda x: {"id": x.id, "name": x.name},
            Companies.query.with_entities(Companies.id, Companies.name).all(),
        )
    )


@companies_bp.route("/companies")
def get_companies():
    return render_template("companies.html", companies=Companies.query)


@companies_bp.route("/companies", methods=["POST"])
def create_company():
    content = request.json

    current_app.logger.info("Creating a new company")
    current_app.logger.info(json.dumps(content))

    name = content.get("name")
    board_url = content.get("board_url")
    url_prefix = content.get("job_posting_url_prefix")
    scraping_method = content.get("scraping_method")

    if name and board_url:
        c = Companies(
            name=name,
            board_url=board_url,
            job_posting_url_prefix=url_prefix,
            scraping_method=scraping_method,
        )

        db.session.add(c)
        db.session.commit()

        record = db.session.get(Companies, c.id)
        record = record.__dict__
        del record["_sa_instance_state"]

        return record
    else:
        return "Failed", 400


@companies_bp.route("/companies/<int:id>", methods=["PUT"])
def update_company(id):
    current_app.logger.info("Updating a record")
    current_app.logger.info(json.dumps(request.form))

    name = request.form.get("name")
    board_url = request.form.get("board_url")
    scraping_method = request.form.get("scraping_method")
    url_prefix = request.form.get("job_posting_url_prefix")

    company = db.session.get(Companies, id)

    company.name = name
    company.board_url = board_url
    company.scraping_method = scraping_method
    company.job_posting_url_prefix = url_prefix

    db.session.commit()

    return f"Successfully updated the record for id: {id}"


@companies_bp.route("/companies/<int:id>", methods=["DELETE"])
def delete_company(id):
    data = db.session.get(Companies, id)
    db.session.delete(data)
    db.session.commit()

    return f"Successfully deleted {id}"
