from jobcrawler import create_app
from config import *
import os

config = ProductionConfig if os.environ.get("ENV") == "PROD" else DevelopmentConfig

app = create_app(config)
