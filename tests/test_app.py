# tests/test_app.py
# This file contains tests for the Flask application.
# We use pytest to run these tests.
# Run with: pytest tests/test_app.py -v

import pytest
from app import create_app, db
from app.models import Country, Production


# --- Fixtures ---
# Fixtures are reusable test setup functions.
# pytest automatically passes them into test functions that need them.

@pytest.fixture
def app():
    """
    Creates a test version of the app.
    Uses an in-memory SQLite database so tests never
    touch the real oil.db file.
    """
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        # Create all tables in the test database
        db.create_all()
        yield app
        # Drop all tables after each test
        db.drop_all()


@pytest.fixture
def client(app):
    """
    Gives tests a test client to make fake HTTP requests
    without needing a real running server.
    """
    return app.test_client()


@pytest.fixture
def sample_data(app):
    """
    Adds sample countries and production records to the
    test database so we have data to test against.
    """
    with app.app_context():
        # Create two test countries
        country1 = Country(
            name='Test Country A',
            flag_url='http://example.com/flag_a.jpg'
        )
        country2 = Country(
            name='Test Country B',
            flag_url=None
        )
        db.session.add(country1)
        db.session.add(country2)
        db.session.flush()

        # Add production records for country1
        prod1 = Production(
            country_id=country1.id,
            year=2000,
            production=1000.0
        )
        prod2 = Production(
            country_id=country1.id,
            year=2001,
            production=2000.0
        )
        # Add a zero production record for country2
        prod3 = Production(
            country_id=country2.id,
            year=2000,
            production=0.0
        )
        db.session.add(prod1)
        db.session.add(prod2)
        db.session.add(prod3)
        db.session.commit()


# --- Model Tests ---
# These tests check that our database models work correctly.

def test_country_model(app):
    """Test that a Country can be created and saved."""
    with app.app_context():
        country = Country(name='Test Nation X', flag_url=None)
        db.session.add(country)
        db.session.commit()

        # Check it was saved correctly
        saved = Country.query.filter_by(name='Test Nation X').first()
        assert saved is not None
        assert saved.name == 'Test Nation X'


def test_production_model(app):
    """Test that a Production record can be created and linked to a Country."""
    with app.app_context():
        # Create a country first
        country = Country(name='Norway', flag_url=None)
        db.session.add(country)
        db.session.flush()

        # Create a production record linked to it
        prod = Production(
            country_id=country.id,
            year=2005,
            production=3000.5
        )
        db.session.add(prod)
        db.session.commit()

        # Check the relationship works
        saved = Production.query.filter_by(year=2005).first()
        assert saved is not None
        assert saved.production == 3000.5
        assert saved.country.name == 'Norway'


def test_avg_production(app, sample_data):
    """Test that avg_production calculates correctly."""
    with app.app_context():
        country = Country.query.filter_by(name='Test Country A').first()
        # Average of 1000 and 2000 should be 1500
        assert country.avg_production() == 1500.0


def test_peak_production(app, sample_data):
    """Test that peak_production returns the correct year."""
    with app.app_context():
        country = Country.query.filter_by(name='Test Country A').first()
        peak = country.peak_production()
        # Peak should be 2001 with production of 2000
        assert peak.year == 2001
        assert peak.production == 2000.0


# --- Route Tests ---
# These tests check that our pages load correctly.

def test_index_page(client):
    """Test that the home page loads successfully."""
    response = client.get('/')
    # 200 means the page loaded OK
    assert response.status_code == 200


def test_index_page_contains_title(client):
    """Test that the home page contains the app title."""
    response = client.get('/')
    assert b'Oil Production' in response.data


def test_search_works(client, app, sample_data):
    """Test that searching for a country returns results."""
    response = client.get('/?search=Test')
    assert response.status_code == 200
    assert b'Test Country A' in response.data


def test_country_page(client, app, sample_data):
    """Test that a country detail page loads correctly."""
    with app.app_context():
        country = Country.query.filter_by(name='Test Country A').first()
        response = client.get(f'/country/{country.id}')
        assert response.status_code == 200
        assert b'Test Country A' in response.data


def test_404_page(client):
    """Test that visiting a non-existent country returns 404."""
    response = client.get('/country/99999')
    assert response.status_code == 404


def test_compare_page(client):
    """Test that the compare page loads successfully."""
    response = client.get('/compare')
    assert response.status_code == 200