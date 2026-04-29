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