from flask import render_template, send_from_directory, current_app, Blueprint
import os

home_bp = Blueprint(
    "home_bp", __name__, template_folder="templates", static_folder="static"
)


@home_bp.route("/")
@home_bp.route("/index")
def index():
    return render_template("index.html")


@home_bp.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(current_app.root_path, "static", "img"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


@home_bp.route("/robots.txt")
def robots_dot_txt():
    return send_from_directory(
        os.path.join(current_app.root_path, "static", "txt"), "robots.txt"
    )
