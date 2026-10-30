from app.extensions import db


class Contract(db.Model):
    __tablename__ = "contracts"
    id = db.Column(db.Integer, primary_key=True)
    npc_id = db.Column(db.Integer, db.ForeignKey("npcs.id"), nullable=False)
    title = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text, default="")
    req_type = db.Column(db.String(16), nullable=False)  # kill, collect
    req_target = db.Column(db.String(64), nullable=False)
    req_count = db.Column(db.Integer, default=1)
    reward_gold = db.Column(db.Integer, default=0)
    reward_xp = db.Column(db.Integer, default=0)

    npc = db.relationship("NPC")