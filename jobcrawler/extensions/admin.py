from flask_admin import Admin
from flask_admin.menu import MenuLink
from flask_admin.contrib.sqla import ModelView
from jobcrawler.models.users import Users
from jobcrawler.models.searches import Searches
from jobcrawler.models.postings import Postings
from jobcrawler.models.companies import Companies
from jobcrawler.models import db
from flask_login import current_user

class AdminView(ModelView):
    def is_accessible(self):
        if current_user.get_id():
            return current_user.is_admin
        else:
            return False

admin = Admin(name="jobcrawler")

admin.add_view(AdminView(Users, db.session))
admin.add_view(AdminView(Postings, db.session))
admin.add_view(AdminView(Companies, db.session))
admin.add_view(AdminView(Searches, db.session))
admin.add_link(MenuLink(name="Home", category="", url="/index"))