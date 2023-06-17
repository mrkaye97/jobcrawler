from jobcrawler.core import db
from flask_login import UserMixin


class Companies(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), index=True, nullable=False)
    board_url = db.Column(db.String(2048), nullable=False)
    job_posting_url_prefix = db.Column(db.String(2048), nullable=True)
    scraping_method = db.Column(db.String(64), nullable=False, default="soup")
    board_url_is_dead_link = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return "<Company {}>".format(self.name)


class Postings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), index=True)
    link_text = db.Column(db.String(2048), index=True)
    link_href = db.Column(db.String(2048), index=True)
    created_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)

    def __repr__(self):
        return "<Posting {}> Company: {}, link_href: {}, link_text: {}, created_at: {}".format(
            self.id, self.company_id, self.link_href, self.link_text, self.created_at
        )


class Searches(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), index=True)
    search_regex = db.Column(db.String(256), unique=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    created_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)

    def __repr__(self):
        return f"Company : {self.company}, URL: {self.url}, search: {self.search_regex}"


class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(128))
    email = db.Column(db.String(128), index=True)
    password_hash = db.Column(db.String(128))
    email_frequency_days = db.Column(db.Integer, nullable=False, default=7)
    default_search_regex = db.Column(db.String, nullable=True)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    has_seen_add_company_helper_modal = db.Column(
        db.Boolean, nullable=False, default=False
    )
    last_received_email_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return "<User {}>".format(self.email)
