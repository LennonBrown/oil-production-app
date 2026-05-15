# This is the application factory file
from dotenv import load_dotenv
load_dotenv(override=False)

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'dev-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///oil.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    from app.models import Region, Country, Production

    from app.routes import main
    app.register_blueprint(main)

    from app.errors import errors
    app.register_blueprint(errors)

    print("DEBUG: blueprints registered")
    print([str(r) for r in app.url_map.iter_rules()])

    return app