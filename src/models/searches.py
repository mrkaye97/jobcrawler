from src.models import db

class Searches(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), index = True)
    search_regex = db.Column(db.String(256), unique=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), index = True)
    posting_id = db.Column(db.Integer, db.ForeignKey("postings.id"))

    def __repr__(self):
        return f"Company : {self.company}, URL: {self.url}, search: {self.search_regex}"
