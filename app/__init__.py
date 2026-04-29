#This is the application factory file

from flask import Flask                   #Import Flask 
from flask_sqlalchemy import SQLAlchemy   #SQLAlchemy is a Python library used to work with databases without writing raw SQL for everything.

db = SQLAlchemy()          #This creates a single shared SQLAlchemy instance which will get initialised with the app below

def create_app():
    app = Flask(__name__)
    
    # --- App Configuration ---
    # SECRET_KEY is used by Flask for session security (e.g. flash messages)
    app.config['SECRET_KEY'] = 'dev-secret-key'



    # Tell SQLAlchemy to use a local SQLite database file called oil.db
    # It will be created automatically inside an 'instance/' folder
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///oil.db'


    # Disable modification tracking
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # --- Initialise Extensions ---
    db.init_app(app)


    # Import models here so SQLAlchemy knows about the tables
    from app import models
    
    
     # --- Register Blueprints ---
    # Blueprints are Flask's way of organising routes into separate modules.
    # We import inside the function to avoid circular imports.

    from app.routes import main
    app.register_blueprint(main)

    # Register the error handlers blueprint (404, 500 pages)
    from app.errors import errors
    app.register_blueprint(errors)

    return app

