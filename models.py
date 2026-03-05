from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

class UrlScrape(db.Model):
    __tablename__ = "urls"

    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String, nullable=False)
    url = db.Column(db.String, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))