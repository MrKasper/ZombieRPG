from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from app.extensions import db
from app.models import Auction, Inventory, Item, Character
from app.services.loot import add_to_inventory

auction_bp = Blueprint("auction", __name__)

COMMISSION_PCT = 5
AUCTION_DURATION_DAYS = 7
MAX_ACTIVE_PER_PLAYER = 10

def _serialize(a, viewer=None):
    qty_on_market = Auction.query.filter_by(item_id=a.item_id, status="active").count()
    dynamic_price = a.price
    if qty_on_market > 3:
        dynamic_price = int(a.price * (1.0 - 0.1 * (qty_on_market - 3)))
        dynamic_price = max(1, dynamic_price)

    return {
        "id": a.id,
        "seller": {"id": a.seller_id, "name": a.seller.name if a.seller else "?"},
        "buyer": ({"id": a.buyer_id, "name": a.buyer.name if a.buyer else "?"} if a.buyer_id else None),
        "item": {"id": a.item_id, "name": a.item.name if a.item else "?", "icon": a.item.icon if a.item else "📦", "rarity": a.item.rarity if a.item else "common"},
        "quantity": a.quantity,
        "price": dynamic_price,
        "original_price": a.price,
        "status": a.status,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "expires_at": a.expires_at.isoformat() if a.expires_at else None,
        "seconds_left": (max(0, int((a.expires_at - datetime.utcnow()).total_seconds())) if a.expires_at else 0),
        "is_mine": viewer is not None and a.seller_id == viewer.id,
    }

@auction_bp.get("/auction/list")
@login_required
def list_auctions():
    now = datetime.utcnow()
    rows = (Auction.query.filter_by(status="active").filter(Auction.expires_at > now).order_by(Auction.price.asc()).limit(100).all())
    return jsonify({"auctions": [_serialize(a, current_user) for a in rows], "commission_pct": COMMISSION_PCT})

@auction_bp.get("/auction/my")
@login_required
def my_auctions():
    rows = (Auction.query.filter_by(seller_id=current_user.id).order_by(Auction.created_at.desc()).limit(50).all())
    return jsonify({"auctions": [_serialize(a, current_user) for a in rows], "max_active": MAX_ACTIVE_PER_PLAYER})

@auction_bp.post("/auction/sell")
@login_required
def sell():
    data = request.get_json(silent=True) or {}
    inv_id = data.get("inv_id")
    price = int(data.get("price", 0))
    qty = int(data.get("qty", 1))

    if price < 1: return jsonify({"error": "bad_price"}), 400
    if qty < 1: return jsonify({"error": "bad_qty"}), 400

    if Auction.query.filter_by(seller_id=current_user.id, status="active").count() >= MAX_ACTIVE_PER_PLAYER:
        return jsonify({"error": "too_many_lots"}), 400

    inv = Inventory.query.filter_by(id=inv_id, character_id=current_user.id).first()
    if not inv: return jsonify({"error": "not_found"}), 404
    if inv.equipped_slot: return jsonify({"error": "unequip_first"}), 400
    if inv.quantity < qty: return jsonify({"error": "not_enough_quantity"}), 400
    if not inv.item.stackable and qty != 1: return jsonify({"error": "bad_qty"}), 400

    item_id = inv.item_id
    if inv.quantity > qty: inv.quantity -= qty
    else: db.session.delete(inv)

    auction = Auction(seller_id=current_user.id, item_id=item_id, quantity=qty, price=price, status="active", expires_at=datetime.utcnow() + timedelta(days=AUCTION_DURATION_DAYS))
    db.session.add(auction)
    db.session.commit()
    return jsonify({"ok": True, "auction_id": auction.id})

@auction_bp.post("/auction/buy/<int:auction_id>")
@login_required
def buy(auction_id):
    a = Auction.query.get_or_404(auction_id)
    if a.status != "active": return jsonify({"error": "auction_closed"}), 400
    if a.expires_at < datetime.utcnow(): return jsonify({"error": "auction_expired"}), 400
    if a.seller_id == current_user.id: return jsonify({"error": "own_auction"}), 400

    ser = _serialize(a)
    actual_price = ser["price"]

    if current_user.gold < actual_price: return jsonify({"error": "not_enough_gold", "need": actual_price}), 400

    commission = (actual_price * COMMISSION_PCT) // 100
    seller_gain = actual_price - commission

    current_user.gold -= actual_price
    seller = Character.query.get(a.seller_id)
    if seller: seller.gold += seller_gain

    add_to_inventory(current_user, a.item_id, a.quantity)
    a.status = "sold"
    a.buyer_id = current_user.id
    a.sold_at = datetime.utcnow()

    db.session.commit()
    return jsonify({"ok": True, "gold_left": current_user.gold, "commission": commission})

@auction_bp.post("/auction/cancel/<int:auction_id>")
@login_required
def cancel(auction_id):
    a = Auction.query.get_or_404(auction_id)
    if a.seller_id != current_user.id: return jsonify({"error": "not_your_auction"}), 403
    if a.status != "active": return jsonify({"error": "auction_closed"}), 400

    add_to_inventory(current_user, a.item_id, a.quantity)
    a.status = "cancelled"
    db.session.commit()
    return jsonify({"ok": True})

def expire_auctions(now):
    stale = Auction.query.filter(Auction.status == "active", Auction.expires_at <= now).all()
    for a in stale:
        seller = Character.query.get(a.seller_id)
        if seller: add_to_inventory(seller, a.item_id, a.quantity)
        a.status = "expired"
    return len(stale)