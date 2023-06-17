import os
from dotenv import load_dotenv

for env_file in (".env", ".flaskenv"):
    env = os.path.join(os.getcwd(), env_file)
    if os.path.exists(env):
        load_dotenv(env)

class Config(object):
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SITEMAP_INCLUDE_RULES_WITHOUT_PARAMS = True
    SCHEDULER_JOB_DEFAULTS = {"max_instances": 3}

    TESTING = False

class ProductionConfig(Config):
    pass

class DevelopmentConfig(Config):
    pass

class TestingConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'postgresql://matt@localhost/jobcrawler-test'
    TESTING = True

