# Oil Production App

A Flask web application that displays crude oil production data 
for countries around the world from 1992 to 2018.

## Student
Lennon Brown - t08lb25@abdn.ac.uk - 52536492

## How to Run
1. Clone the repository
2. Create a virtual environment: python -m venv venv
3. Install requirements: pip install -r requirements.txt
4. Load the data: python load_data.py
5. Run the app: python run.py
6. Open in browser at port 5000
7. Run tests: pytest tests/test_app.py -v

## Data Source
U.S. Energy Information Administration (EIA) via Kaggle.
Covers 220 countries and 5940 production records from 1992 to 2018.