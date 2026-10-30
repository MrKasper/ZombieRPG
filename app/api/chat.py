from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from app.extensions import db
from app.models import ChatMessage

chat_bp = Blueprint("chat", __name__)


@chat_bp.post("/chat/send")
@login_required
def send():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    scope = data.get("scope", "location")

    if not message or len(message) > 300:
        return jsonify({"error": "bad_message"}), 400
    if scope not in ("location", "global"):
        return jsonify({"error": "bad_scope"}), 400

    msg = ChatMessage(
        location_id=current_user.location_id if scope == "location" else None,
        character_id=current_user.id,
        scope=scope,
        message=message,
    )
    db.session.add(msg)
    db.session.commit()
    return jsonify({"ok": True, "id": msg.id})


@chat_bp.get("/chat/history")
@login_required
def history():
    scope = request.args.get("scope", "location")
    limit = min(int(request.args.get("limit", 30)), 100)

    q = ChatMessage.query
    if scope == "location":
        q = q.filter_by(scope="location", location_id=current_user.location_id)
    else:
        q = q.filter_by(scope="global")
    rows = q.order_by(ChatMessage.id.desc()).limit(limit).all()

    return jsonify({"messages": [
        {
            "id": m.id, "character_id": m.character_id,
            "name": m.character.name if m.character else "?",
            "message": m.message, "scope": m.scope,
            "created_at": m.created_at.isoformat(),
        }
        for m in reversed(rows)
    ]})