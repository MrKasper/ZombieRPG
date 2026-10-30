from flask import Blueprint, jsonify
from flask_login import current_user, login_required
from app.extensions import db
from app.models import Recipe, Item, Inventory, NPC
from app.services.loot import (add_to_inventory, remove_from_inventory,
                               count_in_inventory)

craft_bp = Blueprint("craft", __name__)


def _has_crafter_here():
    """Есть ли в текущей локации NPC с ролью crafter."""
    return NPC.query.filter_by(
        location_id=current_user.location_id, role="crafter"
    ).first() is not None


@craft_bp.get("/craft/recipes")
@login_required
def list_recipes():
    if not _has_crafter_here():
        return jsonify({"error": "no_crafter_here"}), 400

    recipes = Recipe.query.all()
    result = []

    for r in recipes:
        if not r.result_item:
            continue

        ingredients = []
        can_craft = True
        for entry in (r.ingredients or []):
            it = Item.query.get(entry["item_id"])
            if not it:
                continue
            have = count_in_inventory(current_user, it.id)
            enough = have >= entry["qty"]
            if not enough:
                can_craft = False
            ingredients.append({
                "item_id": it.id, "name": it.name, "icon": it.icon,
                "qty": entry["qty"], "have": have, "enough": enough,
            })

        if r.gold_cost > 0 and current_user.gold < r.gold_cost:
            can_craft = False

        result.append({
            "id": r.id,
            "result": {
                "item_id": r.result_item.id,
                "name": r.result_item.name,
                "icon": r.result_item.icon,
                "rarity": r.result_item.rarity,
                "qty": r.result_qty,
            },
            "ingredients": ingredients,
            "gold_cost": r.gold_cost,
            "can_craft": can_craft,
        })

    return jsonify({"recipes": result})


@craft_bp.post("/craft/<int:recipe_id>")
@login_required
def craft(recipe_id):
    if not _has_crafter_here():
        return jsonify({"error": "no_crafter_here"}), 400

    r = Recipe.query.get_or_404(recipe_id)

    # проверка ингредиентов
    for entry in (r.ingredients or []):
        if count_in_inventory(current_user, entry["item_id"]) < entry["qty"]:
            return jsonify({"error": "missing_ingredients"}), 400

    if r.gold_cost > 0 and current_user.gold < r.gold_cost:
        return jsonify({"error": "not_enough_gold"}), 400

    # списать
    for entry in (r.ingredients or []):
        remove_from_inventory(current_user, entry["item_id"], entry["qty"])

    if r.gold_cost > 0:
        current_user.gold -= r.gold_cost

    # выдать
    add_to_inventory(current_user, r.result_item_id, r.result_qty)

    db.session.commit()
    return jsonify({"ok": True, "gold": current_user.gold})