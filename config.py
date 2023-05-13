import os

class Config(object):
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SITEMAP_INCLUDE_RULES_WITHOUT_PARAMS = True
    SERVER_NAME = "localhost.localdomain:5000"