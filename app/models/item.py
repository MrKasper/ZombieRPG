from app.extensions import db


class Item(db.Model):
    __tablename__ = "items"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    type = db.Column(db.String(16), nullable=False)
    slot = db.Column(db.String(16), nullable=True)
    rarity = db.Column(db.String(12), default="common")
    attack = db.Column(db.Integer, default=0)
    defense = db.Column(db.Integer, default=0)
    hp_bonus = db.Column(db.Integer, default=0)
    mp_bonus = db.Column(db.Integer, default=0)
    evasion = db.Column(db.Integer, default=0)
    heal_hp = db.Column(db.Integer, default=0)
    heal_mp = db.Column(db.Integer, default=0)
    learn_skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"), nullable=True)
    icon = db.Column(db.String(8), default="📦")
    description = db.Column(db.Text, default="")
    stackable = db.Column(db.Boolean, default=False)
    base_price = db.Column(db.Integer, default=5)

    # --- НОВОЕ (Типы урона и шум) ---
    damage_type = db.Column(db.String(16), default="blunt")
    noise = db.Column(db.Integer, default=0)


class Inventory(db.Model):
    __tablename__ = "inventory"
    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey("characters.id"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    equipped_slot = db.Column(db.String(16), nullable=True)

    # --- Модификации ---
    mod_scope = db.Column(db.Boolean, default=False)  # +крит
    mod_silencer = db.Column(db.Boolean, default=False)  # -шум

    character = db.relationship("Character", back_populates="inventory")
    item = db.relationship("Item")

    __table_args__ = (
        db.Index(
            "uq_equipped_slot_per_char",
            "character_id", "equipped_slot",
            unique=True,
            sqlite_where=db.text("equipped_slot IS NOT NULL"),
        ),
    )