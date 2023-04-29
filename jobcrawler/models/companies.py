from jobcrawler.models import db

class Companies(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(128), index = True, nullable = False)
    board_url = db.Column(db.String(2048), nullable = False)
    job_posting_url_prefix = db.Column(db.String(2048), nullable = True)
    scraping_method = db.Column(db.String(64), nullable = False, default = "soup")

    def __repr__(self):
        return '<Company {}>'.format(self.name)
