# chat.py
from datetime import datetime
from app.extensions import db

class ChatMessage(db.Model):
    __tablename__ = "chat_messages"
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey("locations.id"), nullable=True)
    character_id = db.Column(db.Integer, db.ForeignKey("characters.id"), nullable=False)
    scope = db.Column(db.String(12), default="location")  # location|global
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    character = db.relationship("Character")