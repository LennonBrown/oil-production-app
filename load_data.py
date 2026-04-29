# load_data.py
# This script reads the oil production CSV file and loads it
# into the SQLite database.
# It is run ONCE to populate the database before starting the app.
# Run it with: python load_data.py

import pandas as pd
from app import create_app, db

# Create the app so we can use the database
app = create_app()


def load_data():
    """
    Reads the CSV file, reshapes it from wide to long format,
    and loads it into the Country and Production tables.
    """
    # Import models inside function to avoid circular imports
    from app.models import Country, Production

    print("Reading CSV file...")
    df = pd.read_csv('data/oil_production.csv')

    # The CSV has columns: Country, Flag, 1992, 1993, 1994 ... 2018
    # We need to reshape it from wide format to long format.
    # Wide:  Country | 1992 | 1993 | 1994
    # Long:  Country | Year | Production

    # Get just the year columns (anything that is a number)
    year_columns = [col for col in df.columns
                    if col.strip().isdigit()]

    print(f"Found year columns: {year_columns}")

    # Melt reshapes wide format into long format
    # id_vars are the columns we keep as-is
    # value_vars are the year columns we want to reshape
    df_long = pd.melt(
        df,
        id_vars=['Country', 'Flag'],
        value_vars=year_columns,
        var_name='year',
        value_name='production'
    )

    # Rename columns to match our models
    df_long.columns = ['name', 'flag_url', 'year', 'production']

    # Convert year to integer
    df_long['year'] = df_long['year'].astype(int)

    # Replace '--' and any non-numeric values with None
    df_long['production'] = pd.to_numeric(
        df_long['production'], errors='coerce'
    )

    # Drop rows where country name is missing
    df_long = df_long.dropna(subset=['name'])

    print(f"Total records after reshaping: {len(df_long)}")

    with app.app_context():
        # Create tables if they don't exist yet
        # This creates the country and production tables in oil.db
        db.create_all()

        # Clear existing data so we can reload cleanly
        print("Clearing existing data...")
        Production.query.delete()
        Country.query.delete()
        db.session.commit()

        # Load countries first (parent table)
        print("Loading countries...")
        countries_added = {}

        for name, flag_url in df[['Country', 'Flag']].values:
            # Skip if name is missing
            if pd.isna(name):
                continue

            # Skip if we have already added this country (avoid duplicates)
            if str(name) in countries_added:
                continue

            # Skip non-country rows at the bottom of the CSV
            # Skip non-country rows at the bottom of the CSV
            if str(name).startswith('Crude Oil') or \
               str(name).startswith('Petroleum') or \
               str(name).startswith('Total') or \
               str(name) == 'Production':
                continue

            # Clean up the flag URL
            flag = flag_url if pd.notna(flag_url) else None

            country = Country(name=str(name), flag_url=flag)
            db.session.add(country)

            # flush() gets the auto-generated id without fully committing
            db.session.flush()

            # Store the country id for use when loading productions
            countries_added[str(name)] = country.id

        db.session.commit()
        print(f"Loaded {len(countries_added)} countries.")

        # Load production records (child table)
        print("Loading production records...")
        count = 0

        for _, row in df_long.iterrows():
            name = str(row['name'])

            # Skip if we don't have this country
            if name not in countries_added:
                continue

            production = Production(
                country_id=countries_added[name],
                year=int(row['year']),
                production=row['production']
                if pd.notna(row['production']) else None
            )
            db.session.add(production)
            count += 1

            # Commit in batches of 500 to keep memory usage low
            if count % 500 == 0:
                db.session.commit()
                print(f"  {count} records loaded...")

        # Commit any remaining records
        db.session.commit()
        print(f"Finished! Loaded {count} production records.")


if __name__ == '__main__':
    load_data()