from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

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

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(128))
    last_name = db.Column(db.String(128))
    email = db.Column(db.String(128), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def __repr__(self):
        return '<User {}>'.format(self.email)