from jobcrawler import db
from jobcrawler.core.models import Users

from flask import request, render_template, redirect, url_for, flash, Blueprint
from flask_login import login_required, current_user

preferences_bp = Blueprint(
    "preferences_bp", __name__, template_folder="templates", static_folder="static"
)


@preferences_bp.route("/preferences", methods=["GET", "POST"])
@login_required
def get_preferences():
    if request.method == "POST":
        first_name = request.form.get("first_name")
        email_frequency_days = int(request.form.get("email_frequency_days"))
        default_search_regex = request.form.get("default_search_regex")

        current_user.first_name = first_name
        current_user.email_frequency_days = email_frequency_days
        current_user.default_search_regex = default_search_regex
        db.session.commit()

        flash("Preferences updated successfully", "success")
        return redirect(url_for("preferences_bp.get_preferences"))

    return render_template("preferences.html")


@preferences_bp.route("/users/current/preferences")
def get_current_user_preferences():
    u = db.session.get(Users, current_user.get_id())

    return {"default_search": u.default_search_regex, "first_name": u.first_name}
