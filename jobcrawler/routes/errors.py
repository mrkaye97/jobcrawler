from flask import request, render_template, Blueprint, current_app
from jobcrawler.exceptions.exceptions import CompanyExistsException, ScrapingException
from werkzeug.exceptions import HTTPException
from sentry_sdk import capture_exception

errors_bp = Blueprint('errors_bp', __name__, template_folder='templates', static_folder = "static")

@errors_bp.app_errorhandler(Exception)
def handle_error(e):
    current_app.logger.error("Request failed.")
    current_app.logger.error(f"URL: {request.url}")
    current_app.logger.error(str(e))

    if isinstance(e, CompanyExistsException) or isinstance(e, ScrapingException):
        return {"message": str(e)}, 400

    code = 500
    if isinstance(e, HTTPException):
        code = e.code

    if request.path == "/scraping/test":
        return {"message": "Sorry, something went wrong."}, 500

    if code == 404:
        capture_exception(e)
        return render_template('404.html')
    else:
        message = "500 - That's our bad." if code == 500 else code
        return render_template("error.html", error_message = message)
