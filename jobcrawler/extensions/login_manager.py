from flask_login import LoginManager
from jobcrawler.core.models import Users
from jobcrawler.core import db

login_manager = LoginManager()
login_manager.login_view = "auth_bp.login"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Users, user_id)
