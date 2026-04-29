#run.py
#This si the entry running pount for the flask application locally 
#It creates the app using the factory function setting, which allows us to set up the database
#And this allows the server to start

from app import create_app, db

# Create the Flask app using the factory function from app/__init__.py
app = create_app()

if __name__ =='__main__':
    # app_context() is needed to work with the database outside of requests
    # db.create_all() creates all tables defined in models.py
    # if they don't already exist

    with app.app_context():
        db.create_all()

    #Run the Flask development server 
    #debug = true means the server will automatically restart when you chnage or update code 

    
    app.run(debug=True)