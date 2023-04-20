import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    if os.environ.get("ENV") == "PROD":
        SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    else:
        SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/jobcrawler'

    SQLALCHEMY_TRACK_MODIFICATIONS = False