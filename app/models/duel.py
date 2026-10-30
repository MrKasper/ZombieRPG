from datetime import datetime
from app.extensions import db


class Duel(db.Model):
    __tablename__ = "duels"
    id = db.Column(db.Integer, primary_key=True)
    challenger_id = db.Column(db.Integer, db.ForeignKey("characters.id"),
                              nullable=False, index=True)
    target_id = db.Column(db.Integer, db.ForeignKey("characters.id"),
                          nullable=False, index=True)
    status = db.Column(db.String(16), default="pending", index=True)
    # pending | finished | declined | cancelled | expired
    winner_id = db.Column(db.Integer, db.ForeignKey("characters.id"), nullable=True)
    log = db.Column(db.JSON, default=list)
    rounds = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    finished_at = db.Column(db.DateTime, nullable=True)

    challenger = db.relationship("Character", foreign_keys=[challenger_id])
    target = db.relationship("Character", foreign_keys=[target_id])
    winner = db.relationship("Character", foreign_keys=[winner_id])