from flask import Blueprint, jsonify
from flask_login import current_user, login_required
from app.models import Achievement, CharacterAchievement

achievements_bp = Blueprint("achievements", __name__)


@achievements_bp.get("/achievements")
@login_required
def list_achievements():
    all_ach = Achievement.query.order_by(Achievement.id).all()
    unlocked_map = {ca.achievement_id: ca.unlocked_at
                    for ca in CharacterAchievement.query
                    .filter_by(character_id=current_user.id).all()}

    return jsonify({
        "total": len(all_ach),
        "unlocked_count": len(unlocked_map),
        "achievements": [
            {
                "id": a.id, "code": a.code, "name": a.name,
                "description": a.description, "icon": a.icon,
                "unlocked": a.id in unlocked_map,
                "unlocked_at": (unlocked_map[a.id].isoformat()
                                if a.id in unlocked_map else None),
                "reward_xp": a.reward_xp,
                "reward_gold": a.reward_gold,
                "condition_type": a.condition_type,
                "condition_value": a.condition_value,
            }
            for a in all_ach
        ],
    })