from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class Searches(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), index = True)
    search_regex = db.Column(db.String(256), unique=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), index = True)
    posting_id = db.Column(db.Integer, db.ForeignKey("postings.id"))

    def __repr__(self):
        return f"Company : {self.company}, URL: {self.url}, search: {self.search_regex}"

class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(128))
    email = db.Column(db.String(128), index=True)
    password_hash = db.Column(db.String(128))
    email_frequency_days = db.Column(db.Integer, nullable = False, default = 7)
    default_search_regex = db.Column(db.String, nullable = True)

    def __repr__(self):
        return '<User {}>'.format(self.email)

class Companies(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(128), index = True, nullable = False)
    board_url = db.Column(db.String(128), nullable = False)
    job_posting_url_prefix = db.Column(db.String(128), nullable = True)
    scraping_method = db.Column(db.String(64), nullable = False, default = "soup")

    def __repr__(self):
        return '<Company {}>'.format(self.name)

class Postings(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), index = True)
    link_text = db.Column(db.String(256), index = True)
    link_href = db.Column(db.String(256), index = True)

    def __repr__(self):
        return '<Posting {}>'.format(self.id)
