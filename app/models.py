# app/models.py
from app import db


class Region(db.Model):
    __tablename__ = 'region'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

    countries = db.relationship('Country', backref='region', lazy=True)

    def __repr__(self):
        return f'<Region {self.name}>'

    def total_avg_production(self):
        return sum(c.avg_production() for c in self.countries)

    def country_count(self):
        return len(self.countries)

    def producing_countries(self):
        return [c for c in self.countries if c.avg_production() > 0]


class Country(db.Model):
    __tablename__ = 'country'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    flag_url = db.Column(db.String(300), nullable=True)
    region_id = db.Column(db.Integer, db.ForeignKey('region.id'), nullable=True)

    productions = db.relationship('Production', backref='country', lazy=True)

    def __repr__(self):
        return f'<Country {self.name}>'

    def avg_production(self):
        values = [p.production for p in self.productions if p.production is not None]
        return round(sum(values) / len(values), 2) if values else 0

    def peak_production(self):
        valid = [p for p in self.productions if p.production is not None]
        return max(valid, key=lambda p: p.production, default=None)


class Production(db.Model):
    __tablename__ = 'production'

    id = db.Column(db.Integer, primary_key=True)
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    production = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return f'<Production {self.country_id} {self.year}>'