from flask import render_template, Blueprint

home_bp = Blueprint('home_bp', __name__, template_folder='templates', static_folder = "static")

@home_bp.route('/')
@home_bp.route('/index')
def index():
    return render_template("index.html")
