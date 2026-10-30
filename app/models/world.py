from app.extensions import db

DIRECTIONS = ("north", "south", "east", "west", "in", "out")

class Location(db.Model):
    __tablename__ = "locations"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text, default="")
    is_safe_zone = db.Column(db.Boolean, default=False)
    danger_level = db.Column(db.Integer, default=1)
    bg_color = db.Column(db.String(16), default="#222")
    grid_w = db.Column(db.Integer, default=20)
    grid_h = db.Column(db.Integer, default=15)
    tilemap_id = db.Column(db.String(32), default="street")

    exits = db.relationship("LocationExit", foreign_keys="LocationExit.from_id", back_populates="from_loc", cascade="all, delete-orphan")
    npcs = db.relationship("NPC", backref="location", lazy="dynamic")

class LocationExit(db.Model):
    __tablename__ = "location_exits"
    id = db.Column(db.Integer, primary_key=True)
    from_id = db.Column(db.Integer, db.ForeignKey("locations.id"), nullable=False)
    to_id = db.Column(db.Integer, db.ForeignKey("locations.id"), nullable=False)
    direction = db.Column(db.String(8), nullable=False)
    x = db.Column(db.Integer, default=0)
    y = db.Column(db.Integer, default=0)

    from_loc = db.relationship("Location", foreign_keys=[from_id], back_populates="exits")
    to_loc = db.relationship("Location", foreign_keys=[to_id])

    __table_args__ = (db.UniqueConstraint("from_id", "direction", name="uq_exit_dir"),)

class NPC(db.Model):
    __tablename__ = "npcs"
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey("locations.id"), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    role = db.Column(db.String(16), nullable=False)
    faction = db.Column(db.String(16), default="neutral") # scientists, military
    icon = db.Column(db.String(8), default="🧑")
    dialogue = db.Column(db.Text, default="")

class ShopStock(db.Model):
    __tablename__ = "shop_stock"
    id = db.Column(db.Integer, primary_key=True)
    npc_id = db.Column(db.Integer, db.ForeignKey("npcs.id"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, default=-1)

    npc = db.relationship("NPC", backref="stock_items")
    item = db.relationship("Item")

    __table_args__ = (db.UniqueConstraint("npc_id", "item_id", name="uq_shop_item"),)

class LootPoint(db.Model):
    __tablename__ = "loot_points"
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey("locations.id"), nullable=False, index=True)
    x = db.Column(db.Integer, nullable=False)
    y = db.Column(db.Integer, nullable=False)
    kind = db.Column(db.String(16), default="box")
    loot_table = db.Column(db.JSON, default=list)
    gold = db.Column(db.Integer, default=0)
    state = db.Column(db.String(12), default="available")
    respawn_at = db.Column(db.DateTime, nullable=True)

class Decoration(db.Model):
    __tablename__ = "decorations"
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey("locations.id"), nullable=False, index=True)
    x = db.Column(db.Integer, nullable=False)
    y = db.Column(db.Integer, nullable=False)
    kind = db.Column(db.String(24), nullable=False)
    alpha = db.Column(db.Float, default=0.75)

class Obstacle(db.Model):
    __tablename__ = "obstacles"
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey("locations.id"), nullable=False, index=True)
    x = db.Column(db.Integer, nullable=False)
    y = db.Column(db.Integer, nullable=False)
    kind = db.Column(db.String(16), nullable=False) # wall|door|window|fence|barrel|car|crate|door_locked
    variant = db.Column(db.String(24), default="")
    hp = db.Column(db.Integer, default=0)
    max_hp = db.Column(db.Integer, default=0)

    location = db.relationship("Location")

    __table_args__ = (db.UniqueConstraint("location_id", "x", "y", name="uq_obstacle_cell"),)

    def is_blocking(self):
        return self.kind not in ("door", "door_locked")

class LoreNote(db.Model):
    __tablename__ = "lore_notes"
    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey("locations.id"), nullable=False)
    x = db.Column(db.Integer, nullable=False)
    y = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(64), default="Записка")
    text = db.Column(db.Text, nullable=False)