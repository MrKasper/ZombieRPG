from datetime import datetime
from flask import Blueprint, jsonify
from flask_login import current_user, login_required
from app.extensions import db
from app.models import LootPoint
from app.services.loot import collect_from_lootpoint

loot_bp = Blueprint("loot", __name__)


@loot_bp.post("/loot/pickup/<int:loot_id>")
@login_required
def pickup(loot_id):
    lp = LootPoint.query.get_or_404(loot_id)

    if lp.location_id != current_user.location_id:
        return jsonify({"error": "not_here"}), 400
    if lp.state != "available":
        return jsonify({"error": "already_looted"}), 400

    # протухший труп
    if lp.kind == "corpse" and lp.respawn_at and lp.respawn_at < datetime.utcnow():
        db.session.delete(lp)
        db.session.commit()
        return jsonify({"error": "too_late"}), 400

    dist = abs(lp.x - current_user.x) + abs(lp.y - current_user.y)
    if dist > 1:
        return jsonify({"error": "too_far"}), 400

    picked = collect_from_lootpoint(lp, current_user)
    db.session.commit()
    return jsonify({"ok": True, "loot": picked})