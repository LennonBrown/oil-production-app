# tests/test_app.py
# Tests for the Oil Production Flask application.
# Run with: pytest tests/test_app.py -v

import pytest
from app import create_app, db
from app.models import Country, Production, Region


# --- FIXTURES ---

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def sample_data(app):
    with app.app_context():
        region1 = Region(name='Test Region A')
        region2 = Region(name='Test Region B')
        db.session.add(region1)
        db.session.add(region2)
        db.session.flush()

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

        prod1 = Production(country_id=country1.id, year=2000, production=1000.0)
        prod2 = Production(country_id=country1.id, year=2001, production=2000.0)
        prod3 = Production(country_id=country2.id, year=2000, production=0.0)
        db.session.add(prod1)
        db.session.add(prod2)
        db.session.add(prod3)
        db.session.commit()


# --- MODEL TESTS ---

def test_country_model(app):
    with app.app_context():
        country = Country(name='Test Nation X', flag_url=None)
        db.session.add(country)
        db.session.commit()

        saved = Country.query.filter_by(name='Test Nation X').first()
        assert saved is not None
        assert saved.name == 'Test Nation X'


def test_production_model(app):
    with app.app_context():
        country = Country(name='Norway', flag_url=None)
        db.session.add(country)
        db.session.flush()

        prod = Production(country_id=country.id, year=2005, production=3000.5)
        db.session.add(prod)
        db.session.commit()

        saved = Production.query.filter_by(year=2005).first()
        assert saved is not None
        assert saved.production == 3000.5
        assert saved.country.name == 'Norway'


def test_region_model(app):
    with app.app_context():
        region = Region(name='Test Region')
        db.session.add(region)
        db.session.commit()

        saved = Region.query.filter_by(name='Test Region').first()
        assert saved is not None
        assert saved.name == 'Test Region'


def test_avg_production(app, sample_data):
    with app.app_context():
        country = Country.query.filter_by(name='Test Country A').first()
        assert country.avg_production() == 1500.0


def test_peak_production(app, sample_data):
    with app.app_context():
        country = Country.query.filter_by(name='Test Country A').first()
        peak = country.peak_production()
        assert peak.year == 2001
        assert peak.production == 2000.0


def test_region_total_avg_production(app, sample_data):
    with app.app_context():
        region = Region.query.filter_by(name='Test Region A').first()
        assert region.total_avg_production() == 1500.0


# --- ROUTE TESTS ---

def test_index_page(client):
    response = client.get('/')
    assert response.status_code == 200


def test_search_works(client, app, sample_data):
    response = client.get('/?search=Test')
    assert response.status_code == 200
    assert b'Test Country A' in response.data


def test_country_page(client, app, sample_data):
    with app.app_context():
        country = Country.query.filter_by(name='Test Country A').first()
        response = client.get(f'/country/{country.id}')
        assert response.status_code == 200
        assert b'Test Country A' in response.data


def test_404_page(client):
    response = client.get('/country/99999')
    assert response.status_code == 404


def test_compare_page(client):
    response = client.get('/compare')
    assert response.status_code == 200


def test_regions_page(client):
    response = client.get('/regions')
    assert response.status_code == 200


def test_region_detail_page(client, app, sample_data):
    with app.app_context():
        region = Region.query.filter_by(name='Test Region A').first()
        response = client.get(f'/region/{region.id}')
        assert response.status_code == 200
        assert b'Test Region A' in response.data


def test_analysis_page(client):
    response = client.get('/analysis')
    assert response.status_code == 200