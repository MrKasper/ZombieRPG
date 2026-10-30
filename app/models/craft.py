from app.extensions import db


class Recipe(db.Model):
    __tablename__ = "recipes"
    id = db.Column(db.Integer, primary_key=True)
    result_item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False)
    result_qty = db.Column(db.Integer, default=1)
    # [{"item_id": 1, "qty": 3}, ...]
    ingredients = db.Column(db.JSON, nullable=False, default=list)
    gold_cost = db.Column(db.Integer, default=0)

    result_item = db.relationship("Item")