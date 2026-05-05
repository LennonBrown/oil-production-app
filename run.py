# run.py
# Entry point for the Flask application.
# Creates the app, sets up the database, and loads data if needed.

from app import create_app, db

# Create the Flask app using the factory function
app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # Create all tables if they don't exist
        db.create_all()

        # Load data if the database is empty
        from app.models import Country
        if Country.query.count() == 0:
            print("Database is empty - loading data...")
            from load_data import load_data
            load_data()

    app.run(debug=True)