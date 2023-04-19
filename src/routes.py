from . import app
from flask import request, jsonify, render_template
from . import *
import json

@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html")

## CRUD operations for a job search
@app.route("/searches")
def get_searches():
    searches = Searches.\
        query.\
        join(Companies).\
        with_entities(Searches.id.label("search_id"), Companies.id.label("company_id"), Companies.name, Companies.board_url, Searches.search_text).\
        order_by(Searches.id).\
        all()

    result = [
        {"search_id": search.search_id, "company_id": search.company_id, "name": search.name, "url": search.board_url, "search_text": search.search_text}
        for search in searches
    ]

    print(json.dumps(result))
    return result

@app.route('/searches', methods=["POST"])
def create_search():
    content = request.json

    print(request.json)
    company_id = content.get("company_id")
    search_text = content.get("search_text")

    if company_id and search_text:
        p = Searches(company_id = company_id, search_text = search_text)
        db.session.add(p)
        db.session.commit()

        id = p.id

        record = Searches.query.get(id)
        record = record.__dict__
        del record["_sa_instance_state"]

        return record
    else:
        return "Failed", 400

@app.route('/searches/<int:id>', methods=["PUT"])
def update_search(id):
    company_id = request.form.get("company_id")
    search_text = request.form.get("search_text")


    print("Company Id: ", company_id)
    print("Search: ", search_text)

    posting = Searches.query.get(id)

    posting.company_id = company_id
    posting.search_text = search_text

    db.session.commit()

    return f"Successfully updated the record for id: {id}"

@app.route('/searches/<int:id>', methods = ["DELETE"])
def delete_search(id):
    print("Deleting: ", id)
    data = Searches.query.get(id)
    db.session.delete(data)
    db.session.commit()
    return jsonify(f"Successfully deleted {id}")

@app.route('/searches', methods=["DELETE"])
def delete_search_by_name():
    company = request.form.get("company")
    url = request.form.get("url")
    search_text = request.form.get("search_text")

    print("Deleting: ", company, url, search_text)
    data = Searches.query.filter_by(company = company, url = url, search_text = search_text).first()
    print(data)
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

    print("Name: ", name)
    print("URL:", board_url)
    print("Scraping method: ", scraping_method)

    company = Companies.query.get(id)

    company.name = name
    company.board_url = board_url
    company.scraping_method = scraping_method

    db.session.commit()

    return f"Successfully updated the record for id: {id}"

@app.route('/companies/<int:id>', methods = ["DELETE"])
def delete_company(id):
    print("Deleting: ", id)
    data = Companies.query.get(id)
    db.session.delete(data)
    db.session.commit()
    return jsonify(f"Successfully deleted {id}")
