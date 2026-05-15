# app/routes.py
from flask import Blueprint, render_template, request, abort

main = Blueprint('main', __name__)


@main.route('/')
def index():
    from app.models import Country
    search = request.args.get('search', '')
    filter = request.args.get('filter', 'all')
    if search:
        countries = Country.query.filter(
            Country.name.ilike(f'%{search}%')
        ).order_by(Country.name).all()
    else:
        countries = Country.query.order_by(Country.name).all()
    if filter == 'producers':
        countries = [c for c in countries if c.avg_production() > 0]
    elif filter == 'non_producers':
        countries = [c for c in countries if c.avg_production() == 0]
    return render_template('index.html', countries=countries, search=search, filter=filter)


@main.route('/country/<int:country_id>')
def country(country_id):
    from app.models import Country, Production
    country = Country.query.get_or_404(country_id)
    productions = Production.query.filter_by(country_id=country_id).order_by(Production.year).all()
    all_countries = Country.query.all()
    top_countries = sorted(all_countries, key=lambda c: c.avg_production(), reverse=True)[:5]
    return render_template('country.html', country=country, productions=productions, top_countries=top_countries)


@main.route('/compare')
def compare():
    from app.models import Country
    all_countries = Country.query.all()
    top_countries = sorted(all_countries, key=lambda c: c.avg_production(), reverse=True)[:10]
    return render_template('compare.html', top_countries=top_countries)


@main.route('/oil-price')
def oil_price():
    import requests
    import os
    api_key = os.environ.get('EIA_API_KEY')
    url = (
        f'https://api.eia.gov/v2/petroleum/pri/spt/data/'
        f'?api_key={api_key}'
        f'&frequency=weekly'
        f'&data[0]=value'
        f'&facets[product][]=EPCWTI'
        f'&sort[0][column]=period'
        f'&sort[0][direction]=desc'
        f'&length=1'
    )
    price_data = None
    error = None
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        if ('response' in data and 'data' in data['response'] and len(data['response']['data']) > 0):
            latest = data['response']['data'][0]
            price_data = {
                'price': round(float(latest['value']), 2),
                'date': latest['period'],
                'unit': 'USD per barrel'
            }
        else:
            error = 'Price data currently unavailable.'
    except Exception as e:
        print("EIA API ERROR:", e)
        error = 'Could not fetch oil price at this time.'
    return render_template('oil_price.html', price_data=price_data, error=error)


@main.route('/analysis')
def analysis():
    from app.models import Country, Production
    from sqlalchemy import func
    from app import db
    yearly_totals = db.session.query(
        Production.year,
        func.sum(Production.production).label('total')
    ).filter(Production.production.isnot(None)).group_by(Production.year).order_by(Production.year).all()
    peak_year = max(yearly_totals, key=lambda x: x.total) if yearly_totals else None
    all_countries = Country.query.all()
    sorted_countries = sorted(all_countries, key=lambda c: c.avg_production(), reverse=True)
    top_5 = sorted_countries[:5]
    producers_only = [c for c in all_countries if c.avg_production() > 0]
    bottom_5 = sorted(producers_only, key=lambda c: c.avg_production())[:5]
    total_producers = len(producers_only)
    total_non_producers = len(all_countries) - total_producers
    return render_template('analysis.html', yearly_totals=yearly_totals, peak_year=peak_year, top_5=top_5, bottom_5=bottom_5, total_producers=total_producers, total_non_producers=total_non_producers)


@main.route('/regions')
def regions():
    from app.models import Region
    all_regions = Region.query.order_by(Region.name).all()
    all_regions = sorted(all_regions, key=lambda r: r.total_avg_production(), reverse=True)
    return render_template('regions.html', regions=all_regions)


@main.route('/region/<int:region_id>')
def region(region_id):
    from app.models import Region
    region = Region.query.get_or_404(region_id)
    producers = sorted(region.producing_countries(), key=lambda c: c.avg_production(), reverse=True)
    return render_template('region.html', region=region, producers=producers)

print("DEBUG: all routes loaded")