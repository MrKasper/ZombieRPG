from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from app.extensions import db
from app.models import Trade, Character, Inventory, Item

trade_bp = Blueprint("trade", __name__)


def _serialize(trade):
    def offer_of(side_id):
        offers = trade.offers or {}
        side = offers.get(str(side_id), {"items": [], "gold": 0})
        # развернуть item-ы
        expanded = []
        for entry in side["items"]:
            inv = Inventory.query.get(entry["inv_id"])
            if inv:
                expanded.append({
                    "inv_id": inv.id, "item_id": inv.item_id,
                    "name": inv.item.name, "icon": inv.item.icon,
                    "quantity": entry["quantity"],
                })
        return {"items": expanded, "gold": side["gold"]}

    confirmed = trade.confirmed or {}
    return {
        "id": trade.id,
        "initiator": {"id": trade.initiator_id,
                      "name": (Character.query.get(trade.initiator_id) or {}).name},
        "target": {"id": trade.target_id,
                   "name": (Character.query.get(trade.target_id) or {}).name},
        "offers": {
            trade.initiator_id: offer_of(trade.initiator_id),
            trade.target_id: offer_of(trade.target_id),
        },
        "confirmed": confirmed,
        "status": trade.status,
    }


@trade_bp.post("/trade/init/<int:target_id>")
@login_required
def init_trade(target_id):
    if target_id == current_user.id:
        return jsonify({"error": "self_trade"}), 400

    target = Character.query.get(target_id)
    if not target:
        return jsonify({"error": "no_such_character"}), 404
    if target.location_id != current_user.location_id:
        return jsonify({"error": "not_same_location"}), 400
    if not current_user.location.is_safe_zone:
        return jsonify({"error": "trade_only_in_safe_zone"}), 400

    # если уже есть открытый трейд с этим игроком — вернуть его
    existing = Trade.query.filter(
        Trade.status == "open",
        db.or_(
            db.and_(Trade.initiator_id == current_user.id, Trade.target_id == target.id),
            db.and_(Trade.initiator_id == target.id, Trade.target_id == current_user.id),
        )
    ).first()
    if existing:
        return jsonify({"ok": True, "trade_id": existing.id,
                        "trade": _serialize(existing)})

    trade = Trade(initiator_id=current_user.id, target_id=target.id,
                  status="open", offers={}, confirmed={})
    db.session.add(trade)
    db.session.commit()
    return jsonify({"ok": True, "trade_id": trade.id, "trade": _serialize(trade)})


@trade_bp.get("/trade/current")
@login_required
def current_trade():
    trade = Trade.query.filter(
        Trade.status == "open",
        db.or_(Trade.initiator_id == current_user.id,
               Trade.target_id == current_user.id)
    ).order_by(Trade.id.desc()).first()
    if not trade:
        return jsonify({"trade": None})
    return jsonify({"trade": _serialize(trade)})


@trade_bp.post("/trade/<int:trade_id>/offer")
@login_required
def set_offer(trade_id):
    trade = Trade.query.get_or_404(trade_id)
    if trade.status != "open":
        return jsonify({"error": "trade_closed"}), 400
    if current_user.id not in (trade.initiator_id, trade.target_id):
        return jsonify({"error": "not_participant"}), 403

    data = request.get_json(silent=True) or {}
    raw_items = data.get("items", [])
    gold = max(0, int(data.get("gold", 0)))

    if gold > current_user.gold:
        return jsonify({"error": "not_enough_gold"}), 400

    items = []
    for entry in raw_items:
        inv = Inventory.query.filter_by(
            id=entry.get("inv_id"), character_id=current_user.id
        ).first()
        if not inv or inv.equipped_slot:
            continue
        qty = max(1, min(int(entry.get("quantity", 1)), inv.quantity))
        items.append({"inv_id": inv.id, "quantity": qty})

    offers = dict(trade.offers or {})
    offers[str(current_user.id)] = {"items": items, "gold": gold}
    trade.offers = offers

    confirmed = dict(trade.confirmed or {})
    confirmed[str(current_user.id)] = False
    confirmed[str(trade.target_id if current_user.id == trade.initiator_id else trade.initiator_id)] = False
    trade.confirmed = confirmed

    db.session.commit()
    return jsonify({"ok": True, "trade": _serialize(trade)})


@trade_bp.post("/trade/<int:trade_id>/confirm")
@login_required
def confirm(trade_id):
    trade = Trade.query.get_or_404(trade_id)
    if trade.status != "open":
        return jsonify({"error": "trade_closed"}), 400
    if current_user.id not in (trade.initiator_id, trade.target_id):
        return jsonify({"error": "not_participant"}), 403

    confirmed = dict(trade.confirmed or {})
    confirmed[str(current_user.id)] = True
    trade.confirmed = confirmed

    other = trade.target_id if current_user.id == trade.initiator_id else trade.initiator_id
    if confirmed.get(str(other)):
        return _execute(trade)

    db.session.commit()
    return jsonify({"ok": True, "trade": _serialize(trade)})


@trade_bp.post("/trade/<int:trade_id>/cancel")
@login_required
def cancel(trade_id):
    trade = Trade.query.get_or_404(trade_id)
    if current_user.id not in (trade.initiator_id, trade.target_id):
        return jsonify({"error": "not_participant"}), 403
    if trade.status == "open":
        trade.status = "cancelled"
        db.session.commit()
    return jsonify({"ok": True})


def _execute(trade):
    """Обмен: сначала валидируем всё, потом применяем. Любая ошибка = откат."""
    offers = trade.offers or {}
    inv_changes = []  # (inv_obj, delta_qty, owner_char_id, item_id)
    gold_a = 0
    gold_b = 0

    for side_id_str, side in offers.items():
        side_id = int(side_id_str)
        char = Character.query.get(side_id)
        if not char:
            trade.status = "cancelled"
            db.session.commit()
            return jsonify({"error": "player_gone"}), 400

        if side["gold"] > char.gold:
            trade.status = "cancelled"
            db.session.commit()
            return jsonify({"error": "gold_changed"}), 400
        if side_id == trade.initiator_id:
            gold_a = side["gold"]
        else:
            gold_b = side["gold"]

        for entry in side["items"]:
            inv = Inventory.query.filter_by(id=entry["inv_id"],
                                            character_id=side_id).first()
            if not inv or inv.quantity < entry["quantity"]:
                trade.status = "cancelled"
                db.session.commit()
                return jsonify({"error": "item_changed"}), 400
            inv_changes.append((inv, entry["quantity"], side_id, inv.item_id))

    # применяем
    initiator = Character.query.get(trade.initiator_id)
    target = Character.query.get(trade.target_id)
    initiator.gold += gold_b - gold_a
    target.gold += gold_a - gold_b

    # сначала изъять
    for inv, qty, _owner, _item_id in inv_changes:
        if inv.quantity > qty:
            inv.quantity -= qty
        else:
            db.session.delete(inv)
    db.session.flush()

    # потом выдать получателю
    from app.services.loot import add_to_inventory
    for inv, qty, owner_id, item_id in inv_changes:
        receiver_id = (trade.target_id if owner_id == trade.initiator_id
                       else trade.initiator_id)
        receiver = Character.query.get(receiver_id)
        if receiver:
            add_to_inventory(receiver, item_id, qty)

    trade.status = "done"
    db.session.commit()
    return jsonify({"ok": True, "trade": _serialize(trade)})