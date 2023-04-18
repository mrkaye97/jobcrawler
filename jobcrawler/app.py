from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/jobcrawler'

db = SQLAlchemy(app)

migrate = Migrate(app, db)

class Boards(db.Model):
    __table_args__ = (
        db.UniqueConstraint('company', 'url', 'search_text'),
    )

    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(256), unique=False, nullable=False)
    url = db.Column(db.String(256), unique=False, nullable=False)
    search_text = db.Column(db.String(256), unique=False, nullable=False)

    # repr method represents how one object of this datatable
    # will look like
    def __repr__(self):
        return f"Company : {self.company}, URL: {self.url}, search: {self.search_text}"


# function to add profiles
@app.route('/create', methods=["POST"])
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

@app.route('/delete/<int:id>')
def erase(id):
    data = Boards.query.get(id)
    db.session.delete(data)
    db.session.commit()
    return jsonify(f"Successfully deleted {id}")

def sensor():
    """ Function for test purposes. """
    print("Scheduler is alive!")

sched = BackgroundScheduler(daemon=True)
sched.add_job(sensor,'interval',minutes=1)
sched.start()


if __name__ == '__main__':
    app.run()