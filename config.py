import os


class Config(object):
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SITEMAP_INCLUDE_RULES_WITHOUT_PARAMS = True
    SCHEDULER_JOB_DEFAULTS = {"max_instances": 3}
