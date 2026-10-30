from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class Character(db.Model, UserMixin):
    __tablename__ = "characters"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)

    name = db.Column(db.String(32), nullable=False, unique=True)
    title = db.Column(db.String(32), default="Выживший")
    level = db.Column(db.Integer, default=1)
    xp = db.Column(db.Integer, default=0)
    stat_points = db.Column(db.Integer, default=0)
    skill_points = db.Column(db.Integer, default=0)  # Для дерева навыков

    base_hp = db.Column(db.Integer, default=50)
    base_mp = db.Column(db.Integer, default=20)
    base_attack = db.Column(db.Integer, default=5)
    base_defense = db.Column(db.Integer, default=2)
    base_speed = db.Column(db.Integer, default=5)
    base_evasion = db.Column(db.Integer, default=2)

    hp = db.Column(db.Integer, default=50)
    mp = db.Column(db.Integer, default=20)
    gold = db.Column(db.Integer, default=20)

    # --- ВЫЖИВАНИЕ ---
    hunger = db.Column(db.Integer, default=100)
    thirst = db.Column(db.Integer, default=100)
    temperature = db.Column(db.Float, default=36.6)

    # --- МЕТА ---
    reputation_json = db.Column(db.JSON, default=dict)
    visited_locations = db.Column(db.JSON, default=list)
    unlocked_skills = db.Column(db.JSON, default=list)  # [1, 2, 3]

    kills_total = db.Column(db.Integer, default=0)
    boss_kills = db.Column(db.Integer, default=0)
    deaths = db.Column(db.Integer, default=0)
    quests_done = db.Column(db.Integer, default=0)
    pvp_wins = db.Column(db.Integer, default=0)
    pvp_losses = db.Column(db.Integer, default=0)

    location_id = db.Column(db.Integer, db.ForeignKey("locations.id"))
    x = db.Column(db.Integer, default=10)
    y = db.Column(db.Integer, default=7)

    party_id = db.Column(db.Integer, db.ForeignKey("parties.id"), nullable=True)
    in_combat_id = db.Column(db.Integer, db.ForeignKey("combats.id"), nullable=True)

    last_action_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    location = db.relationship("Location")
    inventory = db.relationship("Inventory", back_populates="character", lazy="dynamic")
    skills = db.relationship("CharacterSkill", back_populates="character", lazy="dynamic")
    party = db.relationship("Party", foreign_keys=[party_id], backref="members")
    combat = db.relationship("Combat", foreign_keys=[in_combat_id])

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

    def xp_for_next_level(self):
        if self.level >= 50:
            return 0
        return int(80 * (self.level ** 1.5))

    def add_xp(self, amount):
        from app.services.progression import get_stats, invalidate_stats
        self.xp += amount
        leveled = False
        while self.level < 50 and self.xp >= self.xp_for_next_level():
            self.xp -= self.xp_for_next_level()
            self.level += 1
            self.base_hp += 5
            self.base_mp += 3
            self.base_attack += 2
            self.base_defense += 1
            self.stat_points += 3
            self.skill_points += 1
            leveled = True
        if leveled:
            invalidate_stats(self)
            stats = get_stats(self)
            self.hp = stats["max_hp"]
            self.mp = stats["max_mp"]
        return leveled