from datetime import datetime
from app.extensions import db


class GameEvent(db.Model):
    __tablename__ = "game_events"
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(32), nullable=False, index=True)
    location_id = db.Column(db.Integer, db.ForeignKey("locations.id"), nullable=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ends_at = db.Column(db.DateTime, nullable=False)
    state = db.Column(db.String(12), default="active")   # active|finished
    data_json = db.Column(db.JSON, default=dict)

    location = db.relationship("Location")