# run.py
# Entry point for the Flask application.
# Creates the app, sets up the database, and loads data if needed.

from app import create_app, db

# Create the Flask app using the factory function
app = create_app()

# This runs when Render starts the app via gunicorn
# It creates the database tables and loads data if empty
with app.app_context():
    db.create_all()
    from app.models import Country
    if Country.query.count() == 0:
        print("Database empty - loading data now...")
        from load_data import load_data
        load_data()

if __name__ == '__main__':
    app.run(debug=True)