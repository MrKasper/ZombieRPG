from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from app.extensions import db
from app.models import Inventory, CharacterSkill, Item
from app.services.progression import get_stats, invalidate_stats
import random

inventory_bp = Blueprint("inventory", __name__)


def _inv_to_dict(inv):
    it = inv.item
    return {
        "id": inv.id, "item_id": inv.item_id, "name": it.name,
        "icon": it.icon, "type": it.type, "slot": it.slot, "rarity": it.rarity,
        "quantity": inv.quantity, "equipped_slot": inv.equipped_slot,
        "attack": it.attack, "defense": it.defense,
        "hp_bonus": it.hp_bonus, "mp_bonus": it.mp_bonus,
        "evasion": it.evasion or 0, "heal_hp": it.heal_hp, "heal_mp": it.heal_mp,
        "description": it.description, "base_price": it.base_price,
        "damage_type": it.damage_type, "noise": it.noise
    }


@inventory_bp.get("/inventory")
@login_required
def list_inventory():
    rows = current_user.inventory.all()
    return jsonify({"items": [_inv_to_dict(i) for i in rows]})


@inventory_bp.post("/inventory/salvage/<int:inv_id>")
@login_required
def salvage(inv_id):
    inv = Inventory.query.filter_by(id=inv_id, character_id=current_user.id).first()
    if not inv: return jsonify({"error": "not_found"}), 404
    if inv.equipped_slot: return jsonify({"error": "unequip_first"}), 400

    item = inv.item
    if item.type not in ("weapon", "armor", "accessory"):
        return jsonify({"error": "not_salvageable"}), 400

    from app.services.loot import add_to_inventory

    mat_metal = Item.query.filter_by(name="Металл").first()
    mat_cloth = Item.query.filter_by(name="Ткань").first()

    salvaged = []
    if item.type == "weapon" and mat_metal:
        qty = random.randint(1, 2) + (1 if item.rarity in ("rare", "epic") else 0)
        add_to_inventory(current_user, mat_metal.id, qty)
        salvaged.append({"name": "Металл", "qty": qty})
    elif item.type == "armor" and mat_cloth:
        qty = random.randint(1, 3)
        add_to_inventory(current_user, mat_cloth.id, qty)
        salvaged.append({"name": "Ткань", "qty": qty})

    if inv.quantity > 1:
        inv.quantity -= 1
    else:
        db.session.delete(inv)

    db.session.commit()
    return jsonify({"ok": True, "salvaged": salvaged})


@inventory_bp.post("/inventory/equip/<int:inv_id>")
@login_required
def equip(inv_id):
    inv = Inventory.query.filter_by(id=inv_id, character_id=current_user.id).first()
    if not inv: return jsonify({"error": "not_found"}), 404
    if inv.item.type not in ("weapon", "armor", "accessory"): return jsonify({"error": "not_equippable"}), 400
    slot = inv.item.slot
    if not slot: return jsonify({"error": "no_slot"}), 400
    current = Inventory.query.filter_by(character_id=current_user.id, equipped_slot=slot).first()
    if current: current.equipped_slot = None
    inv.equipped_slot = slot
    invalidate_stats(current_user)
    db.session.commit()
    return jsonify({"ok": True, "slot": slot})


@inventory_bp.post("/inventory/unequip/<slot>")
@login_required
def unequip(slot):
    inv = Inventory.query.filter_by(character_id=current_user.id, equipped_slot=slot).first()
    if not inv: return jsonify({"error": "empty_slot"}), 404
    inv.equipped_slot = None
    invalidate_stats(current_user)
    db.session.commit()
    return jsonify({"ok": True})


@inventory_bp.post("/inventory/use/<int:inv_id>")
@login_required
def use(inv_id):
    inv = Inventory.query.filter_by(id=inv_id, character_id=current_user.id).first()
    if not inv: return jsonify({"error": "not_found"}), 404
    item = inv.item
    stats = get_stats(current_user)

    if item.type == "consumable":
        hp_before, mp_before = current_user.hp, current_user.mp
        if item.heal_hp: current_user.hp = min(stats["max_hp"], current_user.hp + item.heal_hp)
        if item.heal_mp: current_user.mp = min(stats["max_mp"], current_user.mp + item.heal_mp)

        if item.name in ("Консервы", "Шоколад"): current_user.hunger = min(100, current_user.hunger + 20)
        if item.name in ("Вода", "Энергетик"): current_user.thirst = min(100, current_user.thirst + 20)

        if current_user.hp == hp_before and current_user.mp == mp_before and item.name not in ("Консервы", "Вода",
                                                                                               "Шоколад", "Энергетик"):
            return jsonify({"error": "nothing_happens"}), 400
        _consume(inv)
        db.session.commit()
        return jsonify({"ok": True, "healed_hp": current_user.hp - hp_before, "healed_mp": current_user.mp - mp_before})

    if item.type == "book" and item.learn_skill_id:
        existing = CharacterSkill.query.filter_by(character_id=current_user.id, skill_id=item.learn_skill_id).first()
        if existing: return jsonify({"error": "already_learned"}), 400
        db.session.add(CharacterSkill(character_id=current_user.id, skill_id=item.learn_skill_id, level=1))
        _consume(inv)
        db.session.commit()
        return jsonify({"ok": True, "learned_skill_id": item.learn_skill_id})

    return jsonify({"error": "not_usable"}), 400


@inventory_bp.post("/inventory/drop/<int:inv_id>")
@login_required
def drop(inv_id):
    inv = Inventory.query.filter_by(id=inv_id, character_id=current_user.id).first()
    if not inv: return jsonify({"error": "not_found"}), 404
    if inv.equipped_slot: invalidate_stats(current_user)
    _consume(inv)
    db.session.commit()
    return jsonify({"ok": True})


def _consume(inv):
    if inv.quantity > 1:
        inv.quantity -= 1
    else:
        db.session.delete(inv)