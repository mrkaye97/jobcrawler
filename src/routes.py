from . import app
from flask import request, jsonify, render_template
from . import *

@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html")

@app.route("/boards")
def getjobs():
    result = Boards.query.all()
    out = [{key: b.__dict__[key] for key in ["id", "company", "url", "search_text"]} for b in result]
    print(out)
    return jsonify(out)

@app.route('/boards', methods=["POST"])
def create():
    company = request.form.get("company")
    url = request.form.get("url")
    search_text = request.form.get("search_text")

    if company and url and search_text:
        p = Boards(company = company, url = url, search_text = search_text)
        db.session.add(p)
        db.session.commit()
        return jsonify(f"Successfully created {company} board @ {url}")
    else:
        return jsonify("Failed")

@app.route('/boards', methods=["PUT"])
def insert():
    company = request.form.get("company")
    url = request.form.get("url")
    search_text = request.form.get("search_text")

    print("Company: ", company)
    print("URL:", url)
    print("Search: ", search_text)

    if company and url and search_text:
        p = Boards(company = company, url = url, search_text = search_text)
        db.session.add(p)
        db.session.commit()
        return jsonify(f"Successfully created {company} board @ {url}")
    else:
        return jsonify("Failed")

@app.route('/boards/<int:id>', methods = ["DELETE"])
def erase(id):
    print("Deleting: ", id)
    data = Boards.query.get(id)
    db.session.delete(data)
    db.session.commit()
    return jsonify(f"Successfully deleted {id}")

@app.route('/boards', methods=["DELETE"])
def erase_by_name():
    company = request.form.get("company")
    url = request.form.get("url")
    search_text = request.form.get("search_text")

    print("Deleting: ", company, url, search_text)
    data = Boards.query.filter_by(company = company, url = url, search_text = search_text).first()
    print(data)
    db.session.delete(data)
    db.session.commit()
    return jsonify(f"Successfully deleted")
