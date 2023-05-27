from jobcrawler.models import db

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
