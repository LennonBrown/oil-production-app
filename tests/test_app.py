# tests/test_app.py
# This file contains all tests for the OilTracker Flask application.
# We use pytest as our testing framework as taught in the module lectures.
# Run all tests with: pytest tests/test_app.py -v
# The -v flag gives verbose output showing each test name and result.

import pytest
from app import create_app, db
from app.models import Country, Production, Region


# =============================================================
# --- FIXTURES ---
# Fixtures are reusable setup functions that pytest automatically
# passes into any test function that requests them by name.
# They help us avoid repeating setup code in every test.
# =============================================================

@pytest.fixture
def app():
    """
    Creates a test version of the Flask app.
    Key differences from the real app:
    - TESTING mode is enabled so Flask handles errors differently
    - Uses an in-memory SQLite database (:memory:) instead of oil.db
    - This means tests never read from or write to the real database
    - Tables are created fresh before each test and dropped after
    This approach is recommended by the Flask documentation for testing.
    """
    app = create_app()
    app.config['TESTING'] = True

    # Use an in-memory database so tests are isolated
    # and dont affect the real oil.db file
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        # Create all tables defined in models.py
        db.create_all()
        yield app
        # Drop all tables after the test finishes
        # This ensures each test starts with a clean database
        db.drop_all()


@pytest.fixture
def client(app):
    """
    Creates a Flask test client.
    The test client lets us make fake HTTP requests to the app
    (GET, POST etc.) without needing a real running web server.
    This is how we test routes and pages in Flask.
    """
    return app.test_client()


@pytest.fixture
def sample_data(app):
    """
    Populates the test database with sample data.
    We need this fixture for tests that check real data is displayed.
    Creates:
    - 2 regions (Test Region A and Test Region B)
    - 2 countries linked to those regions
    - 3 production records (2 for country A, 1 for country B)
    Any test that needs data in the database should request
    this fixture alongside the app and client fixtures.
    """
    with app.app_context():
        # Create two test regions
        # These test the Region model and its relationship to Country
        region1 = Region(name='Test Region A')
        region2 = Region(name='Test Region B')
        db.session.add(region1)
        db.session.add(region2)

        # flush() sends the INSERT to the database without committing
        # This gives us the auto-generated IDs we need for foreign keys
        db.session.flush()

        # Create two test countries linked to the regions above
        # country1 has a flag URL, country2 does not
        # This lets us test both cases in the templates
        country1 = Country(
            name='Test Country A',
            flag_url='http://example.com/flag_a.jpg',
            region_id=region1.id
        )
        country2 = Country(
            name='Test Country B',
            flag_url=None,
            region_id=region2.id
        )
        db.session.add(country1)
        db.session.add(country2)
        db.session.flush()

        # Add two production records for country1
        # These are used to test avg_production and peak_production
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
        # This tests that non-producers are handled correctly
        prod3 = Production(
            country_id=country2.id,
            year=2000,
            production=0.0
        )
        db.session.add(prod1)
        db.session.add(prod2)
        db.session.add(prod3)

        # commit() permanently saves everything to the database
        db.session.commit()


# =============================================================
# --- MODEL TESTS ---
# These tests check that our SQLAlchemy database models work
# correctly. They test creating records, saving them, and
# checking relationships between tables.
# =============================================================

def test_country_model(app):
    """
    Tests that a Country object can be created and saved
    to the database correctly.
    Checks: the country is not None after saving, and the
    name matches what we put in.
    """
    with app.app_context():
        # Arrange - create a new country object
        country = Country(name='Test Nation X', flag_url=None)
        db.session.add(country)
        db.session.commit()

        # Act - query the database for the country we just saved
        saved = Country.query.filter_by(name='Test Nation X').first()

        # Assert - check it was saved correctly
        assert saved is not None
        assert saved.name == 'Test Nation X'


def test_production_model(app):
    """
    Tests that a Production record can be created and correctly
    linked to a Country via the foreign key relationship.
    Checks: the production value is correct and the backref
    relationship (production.country) works correctly.
    """
    with app.app_context():
        # Arrange - create a country to link the production to
        country = Country(name='Norway', flag_url=None)
        db.session.add(country)
        db.session.flush()

        # Create a production record linked to the country
        prod = Production(
            country_id=country.id,
            year=2005,
            production=3000.5
        )
        db.session.add(prod)
        db.session.commit()

        # Act - query for the production record
        saved = Production.query.filter_by(year=2005).first()

        # Assert - check values and the relationship works
        assert saved is not None
        assert saved.production == 3000.5

        # This tests the backref relationship defined in models.py
        # production.country should give us the parent Country object
        assert saved.country.name == 'Norway'


def test_region_model(app):
    """
    Tests that a Region object can be created and saved
    to the database correctly.
    This is the third linked table added to the application.
    Checks: the region is not None and the name is correct.
    """
    with app.app_context():
        # Arrange - create a new region
        region = Region(name='Test Region')
        db.session.add(region)
        db.session.commit()

        # Act - query for the region we just saved
        saved = Region.query.filter_by(name='Test Region').first()

        # Assert - check it was saved correctly
        assert saved is not None
        assert saved.name == 'Test Region'


def test_region_country_relationship(app, sample_data):
    """
    Tests the relationship between Region and Country.
    A region should have access to its countries via the
    relationship defined in models.py.
    Checks: country_count returns 1 and the country name
    matches what we put in sample_data.
    """
    with app.app_context():
        # Act - query for the region
        region = Region.query.filter_by(name='Test Region A').first()

        # Assert - check the relationship works
        assert region is not None

        # country_count() is a helper method defined on the Region model
        assert region.country_count() == 1
        assert region.countries[0].name == 'Test Country A'


def test_avg_production(app, sample_data):
    """
    Tests the avg_production() helper method on the Country model.
    Test Country A has two production records: 1000 and 2000.
    The average should be 1500.
    Checks: avg_production returns the mathematically correct average.
    """
    with app.app_context():
        # Act - get the country and calculate average
        country = Country.query.filter_by(
            name='Test Country A').first()

        # Assert - average of 1000 and 2000 should be 1500
        assert country.avg_production() == 1500.0


def test_peak_production(app, sample_data):
    """
    Tests the peak_production() helper method on the Country model.
    Test Country A has production of 1000 in 2000 and 2000 in 2001.
    The peak should be 2001 with a value of 2000.
    Checks: peak_production returns the correct year and value.
    """
    with app.app_context():
        # Act - get the country and find the peak
        country = Country.query.filter_by(
            name='Test Country A').first()
        peak = country.peak_production()

        # Assert - peak should be year 2001 with value 2000
        assert peak.year == 2001
        assert peak.production == 2000.0


def test_region_total_avg_production(app, sample_data):
    """
    Tests the total_avg_production() helper method on the Region model.
    Test Region A contains Test Country A which has an avg of 1500.
    So the region total should also be 1500.
    Checks: total_avg_production sums country averages correctly.
    """
    with app.app_context():
        # Act - get the region and calculate total
        region = Region.query.filter_by(
            name='Test Region A').first()

        # Assert - region total should match country average
        assert region.total_avg_production() == 1500.0


def test_region_producing_countries(app, sample_data):
    """
    Tests the producing_countries() helper method on the Region model.
    Test Region A has one country with production above zero.
    Checks: only countries with avg_production > 0 are returned.
    """
    with app.app_context():
        # Act - get producing countries for region A
        region = Region.query.filter_by(
            name='Test Region A').first()
        producers = region.producing_countries()

        # Assert - should have exactly one producing country
        assert len(producers) == 1
        assert producers[0].name == 'Test Country A'


# =============================================================
# --- ROUTE TESTS ---
# These tests check that our URL routes return the correct
# HTTP status codes and contain the expected content.
# A 200 status means the page loaded successfully.
# A 404 status means the page was not found.
# =============================================================

def test_index_page(client):
    """
    Tests that the home page (/) loads successfully.
    Checks: HTTP status code is 200 (OK).
    """
    # Act - make a GET request to the home page
    response = client.get('/')

    # Assert - 200 means the page loaded OK
    assert response.status_code == 200


def test_index_page_contains_title(client):
    """
    Tests that the home page contains the expected title text.
    Checks: the response body contains 'Oil Production'.
    response.data is the raw bytes of the HTML response.
    """
    # Act - make a GET request to the home page
    response = client.get('/')

    # Assert - check the page content contains our title
    assert b'Oil Production' in response.data


def test_search_works(client, app, sample_data):
    """
    Tests that the search functionality works correctly.
    Searching for 'Test' should return Test Country A in the results.
    Checks: status code is 200 and the country name appears in the response.
    """
    # Act - make a GET request with a search query in the URL
    response = client.get('/?search=Test')

    # Assert - page loads and contains the expected country
    assert response.status_code == 200
    assert b'Test Country A' in response.data


def test_country_page(client, app, sample_data):
    """
    Tests that the country detail page loads correctly.
    We use the sample_data fixture to get a real country ID
    then make a request to that country's page.
    Checks: status code is 200 and the country name appears.
    """
    with app.app_context():
        # Arrange - get the country ID from the test database
        country = Country.query.filter_by(
            name='Test Country A').first()

        # Act - make a GET request to the country detail page
        response = client.get(f'/country/{country.id}')

        # Assert - page loads and contains the country name
        assert response.status_code == 200
        assert b'Test Country A' in response.data


def test_404_page(client):
    """
    Tests that visiting a non-existent country URL returns a 404 error.
    We use country ID 99999 which will never exist in the test database.
    This tests our error handling and the custom 404 template.
    Checks: HTTP status code is 404 (Not Found).
    """
    # Act - request a country that doesnt exist
    response = client.get('/country/99999')

    # Assert - should return 404 Not Found
    assert response.status_code == 404


def test_compare_page(client):
    """
    Tests that the compare countries page loads successfully.
    This page shows the top 10 producing countries side by side.
    Checks: HTTP status code is 200 (OK).
    """
    # Act - make a GET request to the compare page
    response = client.get('/compare')

    # Assert - page loads successfully
    assert response.status_code == 200


def test_regions_page(client):
    """
    Tests that the regions list page loads successfully.
    This is the list page for our third linked table (Region).
    Checks: HTTP status code is 200 (OK).
    """
    # Act - make a GET request to the regions page
    response = client.get('/regions')

    # Assert - page loads successfully
    assert response.status_code == 200


def test_regions_page_contains_heading(client):
    """
    Tests that the regions page contains the expected heading text.
    Checks: the response body contains 'World Region'.
    """
    # Act - make a GET request to the regions page
    response = client.get('/regions')

    # Assert - check the page contains the expected heading
    assert b'World Region' in response.data


def test_region_detail_page(client, app, sample_data):
    """
    Tests that the region detail page loads correctly.
    This is the item page for our third linked table (Region).
    We use sample_data to get a real region ID.
    Checks: status code is 200 and the region name appears.
    """
    with app.app_context():
        # Arrange - get the region ID from the test database
        region = Region.query.filter_by(
            name='Test Region A').first()

        # Act - make a GET request to the region detail page
        response = client.get(f'/region/{region.id}')

        # Assert - page loads and contains the region name
        assert response.status_code == 200
        assert b'Test Region A' in response.data


def test_region_404_page(client):
    """
    Tests that visiting a non-existent region URL returns a 404 error.
    We use region ID 99999 which will never exist in the test database.
    Checks: HTTP status code is 404 (Not Found).
    """
    # Act - request a region that doesnt exist
    response = client.get('/region/99999')

    # Assert - should return 404 Not Found
    assert response.status_code == 404


def test_analysis_page(client):
    """
    Tests that the global analysis page loads successfully.
    This page shows world production totals and top 5 vs bottom 5.
    Checks: HTTP status code is 200 (OK).
    """
    # Act - make a GET request to the analysis page
    response = client.get('/analysis')

    # Assert - page loads successfully
    assert response.status_code == 200


def test_analysis_page_contains_heading(client):
    """
    Tests that the analysis page contains the expected heading text.
    Checks: the response body contains 'Global Oil Production Analysis'.
    """
    # Act - make a GET request to the analysis page
    response = client.get('/analysis')

    # Assert - check the page contains the expected heading
    assert b'Global Oil Production Analysis' in response.data


def test_oil_price_page(client):
    """
    Tests that the live oil price page loads successfully.
    Note: the actual price data may not load in tests since there
    is no real API connection in the test environment.
    However the page itself should always load with a 200 status.
    The error handling in routes.py ensures the page renders
    even if the API call fails.
    Checks: HTTP status code is 200 (OK).
    """
    # Act - make a GET request to the oil price page
    response = client.get('/oil-price')

    # Assert - page loads successfully even without API data
    assert response.status_code == 200


def test_oil_price_page_contains_heading(client):
    """
    Tests that the oil price page contains the expected heading text.
    WTI stands for West Texas Intermediate which is the oil benchmark
    used by our EIA API data source.
    Checks: the response body contains 'WTI'.
    """
    # Act - make a GET request to the oil price page
    response = client.get('/oil-price')

    # Assert - check the page contains the expected heading
    assert b'WTI' in response.data