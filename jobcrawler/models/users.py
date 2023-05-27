from jobcrawler.models import db
from flask_login import UserMixin


class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(128))
    email = db.Column(db.String(128), index=True)
    password_hash = db.Column(db.String(128))
    email_frequency_days = db.Column(db.Integer, nullable=False, default=7)
    default_search_regex = db.Column(db.String, nullable=True)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return "<User {}>".format(self.email)
