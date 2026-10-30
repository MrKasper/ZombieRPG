from datetime import datetime
from app.extensions import db


class ZombieType(db.Model):
    __tablename__ = "zombie_types"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(48), nullable=False)
    level = db.Column(db.Integer, default=1)
    max_hp = db.Column(db.Integer, default=30)
    attack = db.Column(db.Integer, default=3)
    defense = db.Column(db.Integer, default=0)
    xp_reward = db.Column(db.Integer, default=10)
    gold_reward = db.Column(db.Integer, default=1)
    icon = db.Column(db.String(8), default="🧟")
    loot_table = db.Column(db.JSON, default=list)

    attack_type = db.Column(db.String(16), default="normal")  # normal|fast|poison|stun|aoe
    stun_chance = db.Column(db.Float, default=0.0)


class Spawn(db.Model):
    __tablename__ = "spawns"
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey("locations.id"), nullable=False)
    zombie_type_id = db.Column(db.Integer, db.ForeignKey("zombie_types.id"), nullable=False)
    max_count = db.Column(db.Integer, default=3)
    respawn_sec = db.Column(db.Integer, default=60)


class Zombie(db.Model):
    __tablename__ = "zombies"
    id = db.Column(db.Integer, primary_key=True)
    type_id = db.Column(db.Integer, db.ForeignKey("zombie_types.id"), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey("locations.id"), nullable=False, index=True)
    hp = db.Column(db.Integer, nullable=False)
    max_hp = db.Column(db.Integer, nullable=False)
    x = db.Column(db.Integer, default=1)
    y = db.Column(db.Integer, default=1)
    state = db.Column(db.String(12), default="alive")
    respawn_at = db.Column(db.DateTime, nullable=True)
    engaged_combat_id = db.Column(db.Integer, db.ForeignKey("combats.id"), nullable=True)
    is_event_zombie = db.Column(db.Boolean, default=False)

    type = db.relationship("ZombieType")


class Combat(db.Model):
    __tablename__ = "combats"
    id = db.Column(db.Integer, primary_key=True)
    zombie_id = db.Column(db.Integer, db.ForeignKey("zombies.id"), nullable=False)
    status = db.Column(db.String(12), default="active")
    log = db.Column(db.JSON, default=list)
    round = db.Column(db.Integer, default=1)
    next_zombie_attack_at = db.Column(db.DateTime, nullable=True)
    last_activity_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)

    zombie = db.relationship("Zombie", foreign_keys=[zombie_id], post_update=True)
    participants = db.relationship("CombatParticipant", back_populates="combat",
                                   cascade="all, delete-orphan")

    def append_log(self, msg):
        log = list(self.log or [])
        log.append(msg)
        self.log = log[-60:]


class CombatParticipant(db.Model):
    __tablename__ = "combat_participants"
    id = db.Column(db.Integer, primary_key=True)
    combat_id = db.Column(db.Integer, db.ForeignKey("combats.id"), nullable=False)
    character_id = db.Column(db.Integer, db.ForeignKey("characters.id"), nullable=False)
    last_action_at = db.Column(db.DateTime, default=datetime.utcnow)
    auto_mode = db.Column(db.Boolean, default=False)
    damage_dealt = db.Column(db.Integer, default=0)
    is_dead = db.Column(db.Boolean, default=False)

    combat = db.relationship("Combat", back_populates="participants")
    character = db.relationship("Character")

    __table_args__ = (db.UniqueConstraint("combat_id", "character_id", name="uq_participant"),)


class CombatEffect(db.Model):
    __tablename__ = "combat_effects"
    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey("combat_participants.id"),
                               nullable=False, index=True)
    type = db.Column(db.String(16), nullable=False)  # bleed|poison|stun|buff_attack|buff_defense
    value = db.Column(db.Integer, default=0)
    turns_left = db.Column(db.Integer, default=1)

    participant = db.relationship("CombatParticipant", backref="effects")