import random
from datetime import datetime, timedelta
from app.extensions import db
from app.models import Inventory, Item


def roll_loot(zombie_type):
    drops = []
    for entry in (zombie_type.loot_table or []):
        if random.random() < entry.get("chance", 0):
            qty_range = entry.get("qty", [1, 1])
            drops.append({
                "item_id": entry["item_id"],
                "qty": random.randint(qty_range[0], qty_range[1]),
            })
    return drops


def roll_from_table(table):
    drops = []
    for entry in (table or []):
        if random.random() < entry.get("chance", 0):
            qty_range = entry.get("qty", [1, 1])
            drops.append({
                "item_id": entry["item_id"],
                "qty": random.randint(qty_range[0], qty_range[1]),
            })
    return drops


def add_to_inventory(character, item_id, qty):
    from app.services.quest_service import progress_quests

    item = Item.query.get(item_id)
    if not item:
        return

    if item.stackable:
        existing = Inventory.query.filter_by(
            character_id=character.id, item_id=item_id, equipped_slot=None
        ).first()
        if existing:
            existing.quantity += qty
            progress_quests(character, "collect", item_id, qty)
            return

    db.session.add(Inventory(
        character_id=character.id, item_id=item_id, quantity=qty
    ))
    progress_quests(character, "collect", item_id, qty)


def remove_from_inventory(character, item_id, qty):
    rows = Inventory.query.filter_by(
        character_id=character.id, item_id=item_id
    ).all()
    total = sum(r.quantity for r in rows)
    if total < qty:
        return False

    remaining = qty
    for r in rows:
        if remaining <= 0:
            break
        if r.equipped_slot:
            continue
        take = min(r.quantity, remaining)
        r.quantity -= take
        remaining -= take
        if r.quantity == 0:
            db.session.delete(r)
    return remaining <= 0


def count_in_inventory(character, item_id):
    rows = Inventory.query.filter_by(
        character_id=character.id, item_id=item_id
    ).all()
    return sum(r.quantity for r in rows)


def collect_from_lootpoint(lp, character, respawn_seconds=180):
    drops = roll_from_table(lp.loot_table)
    picked = []
    for d in drops:
        item = Item.query.get(d["item_id"])
        if not item:
            continue
        add_to_inventory(character, item.id, d["qty"])
        picked.append({"name": item.name, "icon": item.icon, "qty": d["qty"]})

    gold_gained = lp.gold or 0
    if gold_gained > 0:
        character.gold += gold_gained
        picked.append({"name": "золото", "icon": "💰", "qty": gold_gained})
        lp.gold = 0

    # corpse и airdrop — не респавнятся, удаляются навсегда
    if lp.kind in ("corpse", "airdrop"):
        db.session.delete(lp)
    else:
        lp.state = "looted"
        lp.respawn_at = datetime.utcnow() + timedelta(seconds=respawn_seconds)

    return picked