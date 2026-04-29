# app/errors.py
# This file handles HTTP error pages using a Flask Blueprint.
# Instead of showing Flask's default ugly error page, we render
# our own styled templates when errors occur.

from flask import Blueprint, render_template

# Create a Blueprint called 'errors'
# Blueprints let us group related routes into their own module
errors = Blueprint('errors', __name__)


@errors.app_errorhandler(404)
def not_found(e):
    """
    Handle 404 Not Found errors.
    Triggered when a user visits a URL that does not exist.
    """
    return render_template('errors/404.html'), 404


@errors.app_errorhandler(500)
def server_error(e):
    """
    Handle 500 Internal Server errors.
    Triggered when something unexpected goes wrong in the app.
    """
    return render_template('errors/500.html'), 500