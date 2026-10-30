from datetime import datetime
from app.extensions import db


class Achievement(db.Model):
    __tablename__ = "achievements"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(48), unique=True, nullable=False)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(256), default="")
    icon = db.Column(db.String(8), default="🏆")
    condition_type = db.Column(db.String(24), nullable=False)
    condition_value = db.Column(db.Integer, default=0)
    reward_xp = db.Column(db.Integer, default=0)
    reward_gold = db.Column(db.Integer, default=0)
    reward_item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=True)

    reward_item = db.relationship("Item")


class CharacterAchievement(db.Model):
    __tablename__ = "character_achievements"
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey("characters.id"),
                             nullable=False, index=True)
    achievement_id = db.Column(db.Integer, db.ForeignKey("achievements.id"),
                               nullable=False)
    unlocked_at = db.Column(db.DateTime, default=datetime.utcnow)

    character = db.relationship("Character")
    achievement = db.relationship("Achievement")

    __table_args__ = (
        db.UniqueConstraint("character_id", "achievement_id",
                            name="uq_char_achievement"),
    )