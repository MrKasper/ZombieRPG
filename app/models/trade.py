# trade.py
from datetime import datetime
from app.extensions import db

class Trade(db.Model):
    __tablename__ = "trades"
    id = db.Column(db.Integer, primary_key=True)
    initiator_id = db.Column(db.Integer, db.ForeignKey("characters.id"), nullable=False)
    target_id = db.Column(db.Integer, db.ForeignKey("characters.id"), nullable=False)
    status = db.Column(db.String(12), default="open")  # open|confirmed|done|cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # items и gold храним в JSON: {"initiator": {"items":[...], "gold":0}, "target": {...}}
    offers = db.Column(db.JSON, default=dict)
    confirmed = db.Column(db.JSON, default=dict)  # {"initiator": false, "target": false}