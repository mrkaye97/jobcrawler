from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class Searches(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"))

    search_text = db.Column(db.String(256), unique=False, nullable=False)

    def __repr__(self):
        return f"Company : {self.company}, URL: {self.url}, search: {self.search_text}"

class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(128))
    email = db.Column(db.String(128), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def __repr__(self):
        return '<User {}>'.format(self.email)

class Companies(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(128), index = True, nullable = False)
    board_url = db.Column(db.String(128), nullable = False)
    scraping_method = db.Column(db.String(64), nullable = False, default = "soup")

    def __repr__(self):
        return '<Company {}>'.format(self.name)
