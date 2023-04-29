from jobcrawler.models import db

class Postings(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), index = True)
    link_text = db.Column(db.String(2048), index = True)
    link_href = db.Column(db.String(2048), index = True)

    def __repr__(self):
        return '<Posting {}>'.format(self.id)
