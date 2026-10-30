from app.extensions import db


class Quest(db.Model):
    __tablename__ = "quests"
    id = db.Column(db.Integer, primary_key=True)
    npc_id = db.Column(db.Integer, db.ForeignKey("npcs.id"))
    name = db.Column(db.String(64))
    description = db.Column(db.Text, default="")
    req_type = db.Column(db.String(16))
    req_target = db.Column(db.String(64))
    req_count = db.Column(db.Integer, default=1)
    xp_reward = db.Column(db.Integer, default=0)
    gold_reward = db.Column(db.Integer, default=0)
    item_reward_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=True)
    requires_quest_id = db.Column(db.Integer, db.ForeignKey("quests.id"),
                                   nullable=True)

    npc = db.relationship("NPC")
    item_reward = db.relationship("Item", foreign_keys=[item_reward_id])
    requires_quest = db.relationship("Quest", remote_side=[id])


class CharacterQuest(db.Model):
    __tablename__ = "character_quests"
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey("characters.id"))
    quest_id = db.Column(db.Integer, db.ForeignKey("quests.id"))
    progress = db.Column(db.Integer, default=0)
    status = db.Column(db.String(12), default="active")

    character = db.relationship("Character")
    quest = db.relationship("Quest")