# app/models.py
# This file defines the database models using SQLAlchemy ORM.
# ORM lets us work with the database using Python classes
# instead of writing raw SQL.

from app import db


class Country(db.Model):
    """
    Represents a country in the database.
    This is the PARENT table - one country has many
    yearly production records.
    """
    __tablename__ = 'country'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    flag_url = db.Column(db.String(300), nullable=True)

    # One country has MANY production records
    # backref lets us do production.country to get the parent
    productions = db.relationship('Production', backref='country', lazy=True)

    def __repr__(self):
        # Useful for debugging
        return f'<Country {self.name}>'

    def avg_production(self):
        """Calculate average production across all years."""
        values = [p.production for p in self.productions
                  if p.production is not None]
        return round(sum(values) / len(values), 2) if values else 0

    def peak_production(self):
        """Find the year with the highest production value."""
        valid = [p for p in self.productions
                 if p.production is not None]
        return max(valid, key=lambda p: p.production, default=None)


class Production(db.Model):
    """
    Represents one year of oil production for a country.
    This is the CHILD table - linked back to Country via foreign key.
    Each row = one country + one year + one production value.
    """
    __tablename__ = 'production'

    id = db.Column(db.Integer, primary_key=True)

    # Foreign key links this record back to a Country row
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'),
                           nullable=False)

    year = db.Column(db.Integer, nullable=False)

    # nullable=True because some CSV entries are missing ('--' or null)
    production = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return f'<Production {self.country_id} {self.year}>'