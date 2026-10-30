from datetime import datetime
from app.extensions import db


class Skill(db.Model):
    __tablename__ = "skills"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(48), nullable=False)
    description = db.Column(db.Text, default="")
    icon = db.Column(db.String(8), default="✨")
    mp_cost = db.Column(db.Integer, default=0)
    cooldown_sec = db.Column(db.Integer, default=3)
    learn_level = db.Column(db.Integer, default=1)      # открывается с уровня
    effect_type = db.Column(db.String(16), default="damage")  # damage|heal|buff|stun
    damage_mult = db.Column(db.Float, default=1.0)
    heal_percent = db.Column(db.Float, default=0.0)
    buff_attack_pct = db.Column(db.Float, default=0.0)
    buff_turns = db.Column(db.Integer, default=0)
    can_use_outside = db.Column(db.Boolean, default=False)  # хилка вне боя


class CharacterSkill(db.Model):
    __tablename__ = "character_skills"
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey("characters.id"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"), nullable=False)
    level = db.Column(db.Integer, default=1)         # 1..10, растёт от использования
    cooldown_until = db.Column(db.DateTime, nullable=True)

    character = db.relationship("Character", back_populates="skills")
    skill = db.relationship("Skill")