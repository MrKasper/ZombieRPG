from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from app.extensions import db
from app.models import NPC, ShopStock, Item, Inventory

shop_bp = Blueprint("shop", __name__)


@shop_bp.get("/shop/<int:npc_id>")
@login_required
def view_shop(npc_id):
    npc = NPC.query.get_or_404(npc_id)
    if npc.role != "merchant":
        return jsonify({"error": "not_a_merchant"}), 400
    if npc.location_id != current_user.location_id:
        return jsonify({"error": "npc_not_here"}), 400

    rows = ShopStock.query.filter_by(npc_id=npc.id).all()
    return jsonify({
        "npc": {"id": npc.id, "name": npc.name, "icon": npc.icon},
        "items": [
            {
                "item_id": s.item_id,
                "name": s.item.name,
                "icon": s.item.icon,
                "rarity": s.item.rarity,
                "type": s.item.type,
                "slot": s.item.slot,
                "attack": s.item.attack,
                "defense": s.item.defense,
                "hp_bonus": s.item.hp_bonus,
                "mp_bonus": s.item.mp_bonus,
                "heal_hp": s.item.heal_hp,
                "heal_mp": s.item.heal_mp,
                "description": s.item.description,
                "price": s.price,
                "stock": s.stock,
            }
            for s in rows if s.item
        ],
    })


@shop_bp.post("/shop/<int:npc_id>/buy")
@login_required
def buy(npc_id):
    npc = NPC.query.get_or_404(npc_id)
    if npc.role != "merchant":
        return jsonify({"error": "not_a_merchant"}), 400
    if npc.location_id != current_user.location_id:
        return jsonify({"error": "npc_not_here"}), 400

    data = request.get_json(silent=True) or {}
    item_id = data.get("item_id")
    qty = int(data.get("qty", 1))
    if qty < 1 or qty > 99:
        return jsonify({"error": "bad_qty"}), 400

    stock = ShopStock.query.filter_by(npc_id=npc.id, item_id=item_id).first()
    if not stock:
        return jsonify({"error": "not_in_stock"}), 404
    if 0 <= stock.stock < qty:
        return jsonify({"error": "not_enough_stock",
                        "available": stock.stock}), 400

    total = stock.price * qty
    if current_user.gold < total:
        return jsonify({"error": "not_enough_gold", "need": total}), 400

    current_user.gold -= total
    if stock.stock > 0:
        stock.stock -= qty

    from app.services.loot import add_to_inventory
    add_to_inventory(current_user, item_id, qty)
    db.session.commit()
    return jsonify({"ok": True, "gold": current_user.gold})


@shop_bp.post("/shop/<int:npc_id>/sell")
@login_required
def sell(npc_id):
    npc = NPC.query.get_or_404(npc_id)
    if npc.role != "merchant":
        return jsonify({"error": "not_a_merchant"}), 400
    if npc.location_id != current_user.location_id:
        return jsonify({"error": "npc_not_here"}), 400

    data = request.get_json(silent=True) or {}
    inv_id = data.get("inv_id")
    qty = int(data.get("qty", 1))

    inv = Inventory.query.filter_by(id=inv_id, character_id=current_user.id).first()
    if not inv:
        return jsonify({"error": "not_found"}), 404
    if inv.equipped_slot:
        return jsonify({"error": "unequip_first"}), 400
    if inv.quantity < qty:
        return jsonify({"error": "not_enough_quantity"}), 400

    price_each = max(1, int(inv.item.base_price * 0.4))   # 40% от базовой
    total = price_each * qty
    current_user.gold += total

    if inv.quantity > qty:
        inv.quantity -= qty
    else:
        db.session.delete(inv)

    db.session.commit()
    return jsonify({"ok": True, "gold": current_user.gold, "sold_for": total})