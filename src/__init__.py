from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from .models import *

template_dir = os.path.abspath('templates')
app = Flask(__name__, template_folder=template_dir)
app.config.from_object(Config)
migrate = Migrate(app, db)

db.init_app(app)
migrate.init_app(app, db)
