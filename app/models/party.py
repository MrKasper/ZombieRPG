from datetime import datetime
from app.extensions import db


class Party(db.Model):
    __tablename__ = "parties"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), default="Party")
    leader_id = db.Column(db.Integer, db.ForeignKey("characters.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # backref "members" уже объявлен из Character.party


class PartyInvite(db.Model):
    __tablename__ = "party_invites"
    id = db.Column(db.Integer, primary_key=True)
    party_id = db.Column(db.Integer, db.ForeignKey("parties.id"), nullable=False)
    from_id = db.Column(db.Integer, db.ForeignKey("characters.id"), nullable=False)
    to_id = db.Column(db.Integer, db.ForeignKey("characters.id"), nullable=False)
    status = db.Column(db.String(12), default="pending")  # pending|accepted|declined|expired
    created_at = db.Column(db.DateTime, default=datetime.utcnow)