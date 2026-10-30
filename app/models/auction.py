from datetime import datetime
from app.extensions import db


class Auction(db.Model):
    __tablename__ = "auctions"
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey("characters.id"),
                          nullable=False, index=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey("characters.id"),
                         nullable=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Integer, nullable=False)   # цена за лот (не за единицу)
    status = db.Column(db.String(12), default="active", index=True)
    # active | sold | expired | cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    sold_at = db.Column(db.DateTime, nullable=True)

    seller = db.relationship("Character", foreign_keys=[seller_id])
    buyer = db.relationship("Character", foreign_keys=[buyer_id])
    item = db.relationship("Item")