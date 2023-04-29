from flask import render_template, send_from_directory, Blueprint

homepage = Blueprint('homepage', __name__, template_folder='templates', static_folder = "static")

@homepage.route('/')
@homepage.route('/index')
def index():
    return render_template("index.html")
