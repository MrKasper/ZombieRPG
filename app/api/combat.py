from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from app.extensions import db
from app.models import Zombie, Combat, CombatParticipant
from app.services import tick, combat_engine

combat_bp = Blueprint("combat", __name__)


@combat_bp.post("/combat/start/<int:zombie_id>")
@login_required
def start_combat(zombie_id):
    tick.run_lazy_tick()

    # сброс «висящего» законченного боя
    if current_user.in_combat_id:
        old = Combat.query.get(current_user.in_combat_id)
        if old and old.status == "active":
            return jsonify({"error": "already_in_combat"}), 400
        current_user.in_combat_id = None

    zombie = Zombie.query.get_or_404(zombie_id)
    result = combat_engine.join_combat(current_user, zombie)
    db.session.commit()

    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@combat_bp.post("/combat/action")
@login_required
def combat_action():
    tick.run_lazy_tick()

    if not current_user.in_combat_id:
        return jsonify({"error": "not_in_combat"}), 400
    combat = Combat.query.get(current_user.in_combat_id)
    if not combat or combat.status != "active":
        return jsonify({"error": "combat_finished"}), 400

    participant = CombatParticipant.query.filter_by(
        combat_id=combat.id, character_id=current_user.id
    ).first()
    if not participant:
        return jsonify({"error": "not_participant"}), 400

    data = request.get_json(silent=True) or {}
    action = data.get("action", "attack")

    if action == "attack":
        result = combat_engine.player_attack(
            combat, participant, skill_id=data.get("skill_id")
        )
    elif action == "auto":
        participant.auto_mode = bool(data.get("enabled", True))
        result = {"ok": True, "auto_mode": participant.auto_mode}
    elif action == "flee":
        result = combat_engine.flee_combat(combat, participant)
    else:
        return jsonify({"error": "unknown_action"}), 400

    db.session.commit()
    if "error" in result:
        return jsonify(result), 400

    return jsonify({
        "result": result,
        "combat": {
            "status": combat.status,
            "zombie_hp": combat.zombie.hp,
            "log_tail": (combat.log or [])[-8:],
        },
    })


@combat_bp.post("/combat/dismiss")
@login_required
def dismiss_combat():
    """Закрыть экран результата после победы/поражения."""
    if current_user.in_combat_id:
        c = Combat.query.get(current_user.in_combat_id)
        if not c or c.status != "active":
            current_user.in_combat_id = None
            db.session.commit()
    return jsonify({"ok": True})