# app/routes.py
# This file contains all the URL routes for the application.
# Routes decide what happens when a user visits a specific page.
# This follows the Controller part of the MVC pattern from L14.

from flask import Blueprint, render_template, request, abort

# Create a Blueprint called 'main'
# All our main routes will be registered on this blueprint
main = Blueprint('main', __name__)


@main.route('/')
def index():
    """
    Home page — shows a list of all countries.
    Splits countries into producers and non-producers.
    Supports basic search by country name.
    """
    from app.models import Country

    # Get the search query from the URL e.g. /?search=Saudi
    search = request.args.get('search', '')

    if search:
        # Filter countries where the name contains the search term
        # ilike means case-insensitive search
        countries = Country.query.filter(
            Country.name.ilike(f'%{search}%')
        ).order_by(Country.name).all()
    else:
        # No search — return all countries alphabetically
        countries = Country.query.order_by(Country.name).all()

    # Split into two lists in Python
    # Producers are countries with an average production above 0
    producers = [c for c in countries if c.avg_production() > 0]

    # Non-producers are countries with no recorded oil production
    non_producers = [c for c in countries if c.avg_production() == 0]

    return render_template('index.html',
                           producers=producers,
                           non_producers=non_producers,
                           search=search)


@main.route('/country/<int:country_id>')
def country(country_id):
    """
    Detail page for a single country.
    Shows all yearly production data and some statistics.
    """
    # Import here to avoid circular imports
    from app.models import Country, Production

    # Get the country or return 404 if it doesn't exist
    country = Country.query.get_or_404(country_id)

    # Get all production records for this country ordered by year
    productions = Production.query.filter_by(
        country_id=country_id
    ).order_by(Production.year).all()

    # Get top 5 producing countries for comparison
    all_countries = Country.query.all()
    top_countries = sorted(
        all_countries,
        key=lambda c: c.avg_production(),
        reverse=True
    )[:5]

    return render_template('country.html',
                           country=country,
                           productions=productions,
                           top_countries=top_countries)


@main.route('/compare')
def compare():
    """
    Comparison page — shows top 10 producing countries side by side.
    This helps satisfy criterion 2 for data comparison.
    """
    # Import here to avoid circular imports
    from app.models import Country

    all_countries = Country.query.all()

    # Sort by average production and take top 10
    top_countries = sorted(
        all_countries,
        key=lambda c: c.avg_production(),
        reverse=True
    )[:10]

    return render_template('compare.html',
                           top_countries=top_countries)


@main.route('/oil-price')
def oil_price():
    """
    Oil price page - fetches current WTI crude oil price
    from the EIA (U.S. Energy Information Administration) API.
    This is the same organisation that produced our dataset.
    """
    import requests
    import os

    # Get the EIA API key from environment variables
    api_key = os.environ.get('EIA_API_KEY')

    # EIA API endpoint for WTI crude oil weekly spot price
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
        # Make the API request with a timeout of 10 seconds
        response = requests.get(url, timeout=10)
        data = response.json()

        # Check if we got valid data back
        if ('response' in data and
                'data' in data['response'] and
                len(data['response']['data']) > 0):

            # Get the most recent price entry
            latest = data['response']['data'][0]
            price_data = {
                'price': round(float(latest['value']), 2),
                'date': latest['period'],
                'unit': 'USD per barrel'
            }
        else:
            error = 'Price data currently unavailable.'

    except Exception as e:
        # Handle any network or parsing errors gracefully
        print("EIA API ERROR:", e)
        error = 'Could not fetch oil price at this time.'

    return render_template('oil_price.html',
                           price_data=price_data,
                           error=error)


@main.route('/analysis')
def analysis():
    """
    Analysis page - shows global oil production trends
    and statistics across all countries and years.
    This satisfies criterion 2 for detailed data analysis.
    """
    from app.models import Country, Production
    from sqlalchemy import func
    from app import db

    # Get total world production per year
    # We sum all countries production for each year
    yearly_totals = db.session.query(
        Production.year,
        func.sum(Production.production).label('total')
    ).filter(
        Production.production.isnot(None)
    ).group_by(
        Production.year
    ).order_by(
        Production.year
    ).all()

    # Find the peak production year globally
    # Handle empty database gracefully for testing
    peak_year = max(
        yearly_totals, key=lambda x: x.total
    ) if yearly_totals else None

    # Get all countries for analysis
    all_countries = Country.query.all()

    # Sort by average production highest first
    sorted_countries = sorted(
        all_countries,
        key=lambda c: c.avg_production(),
        reverse=True
    )

    # Top 5 producing countries
    top_5 = sorted_countries[:5]

    # Bottom 5 producers excluding zero producers
    producers_only = [c for c in all_countries
                      if c.avg_production() > 0]
    bottom_5 = sorted(
        producers_only,
        key=lambda c: c.avg_production()
    )[:5]

    # Total number of producing countries
    total_producers = len(producers_only)

    # Total number of non producing countries
    total_non_producers = len(all_countries) - total_producers

    return render_template('analysis.html',
                           yearly_totals=yearly_totals,
                           peak_year=peak_year,
                           top_5=top_5,
                           bottom_5=bottom_5,
                           total_producers=total_producers,
                           total_non_producers=total_non_producers)