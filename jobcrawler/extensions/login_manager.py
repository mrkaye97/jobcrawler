from flask_login import LoginManager
from jobcrawler.models.users import Users
from jobcrawler.models import db

login_manager = LoginManager()
login_manager.login_view = "auth_bp.login"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Users, user_id)
