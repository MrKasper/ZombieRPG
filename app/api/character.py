from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from app.extensions import db
from app.services.progression import get_stats, invalidate_stats

character_bp = Blueprint("character", __name__)


@character_bp.post("/character/allocate")
@login_required
def allocate():
    if current_user.stat_points <= 0:
        return jsonify({"error": "no_points"}), 400
    stat = (request.get_json(silent=True) or {}).get("stat")
    if stat == "hp":
        current_user.base_hp += 3
    elif stat == "mp":
        current_user.base_mp += 2
    elif stat == "attack":
        current_user.base_attack += 1
    elif stat == "defense":
        current_user.base_defense += 1
    else:
        return jsonify({"error": "unknown_stat"}), 400
    current_user.stat_points -= 1
    invalidate_stats(current_user)
    db.session.commit()
    return jsonify({"ok": True, "stats": get_stats(current_user),
                    "stat_points": current_user.stat_points})

@character_bp.get("/skills")
@login_required
def list_skills():
    from app.models import CharacterSkill, Skill
    rows = (CharacterSkill.query
            .join(Skill, Skill.id == CharacterSkill.skill_id)
            .filter(CharacterSkill.character_id == current_user.id).all())
    return jsonify({"skills": [
        {
            "id": cs.skill_id,
            "name": cs.skill.name,
            "icon": cs.skill.icon,
            "mp_cost": cs.skill.mp_cost,
            "cooldown_sec": cs.skill.cooldown_sec,
            "cooldown_until": cs.cooldown_until.isoformat() if cs.cooldown_until else None,
            "effect_type": cs.skill.effect_type,
            "level": cs.level,
            "description": cs.skill.description,
        }
        for cs in rows
    ]})