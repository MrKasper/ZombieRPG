from flask import Blueprint, jsonify
from flask_login import current_user, login_required
from app.extensions import db
from app.models import (Quest, CharacterQuest, NPC, Item, Location)
from app.services.quest_service import is_complete, grant_rewards
from app.services.loot import count_in_inventory

quest_bp = Blueprint("quest", __name__)


def _target_name(req_type, target):
    try:
        if req_type == "kill":
            from app.models import ZombieType
            zt = ZombieType.query.get(int(target))
            return zt.name if zt else "?"
        if req_type == "collect":
            it = Item.query.get(int(target))
            return it.name if it else "?"
        if req_type == "visit":
            loc = Location.query.get(int(target))
            return loc.name if loc else "?"
    except (ValueError, TypeError):
        pass
    return "?"


@quest_bp.get("/quests")
@login_required
def list_quests():
    active_rows = (CharacterQuest.query
                   .filter_by(character_id=current_user.id, status="active").all())
    active = []
    for cq in active_rows:
        q = cq.quest
        if not q:
            continue
        active.append({
            "cq_id": cq.id, "id": q.id, "name": q.name,
            "description": q.description,
            "req_type": q.req_type,
            "target_name": _target_name(q.req_type, q.req_target),
            "progress": cq.progress, "required": q.req_count,
            "complete": is_complete(cq),
            "reward_xp": q.xp_reward, "reward_gold": q.gold_reward,
            "reward_item": (Item.query.get(q.item_reward_id).name
                            if q.item_reward_id else None),
        })

    npcs_here = NPC.query.filter_by(
        location_id=current_user.location_id, role="quest_giver"
    ).all()
    npc_ids = [n.id for n in npcs_here]

    all_cq = CharacterQuest.query.filter_by(character_id=current_user.id).all()
    taken_ids = {cq.quest_id for cq in all_cq}
    turned_in_ids = {cq.quest_id for cq in all_cq if cq.status == "turned_in"}

    available = []
    for q in Quest.query.filter(Quest.npc_id.in_(npc_ids)).all():
        if q.id in taken_ids:
            continue
        if q.requires_quest_id and q.requires_quest_id not in turned_in_ids:
            continue
        available.append({
            "id": q.id, "name": q.name, "description": q.description,
            "req_type": q.req_type,
            "target_name": _target_name(q.req_type, q.req_target),
            "required": q.req_count,
            "reward_xp": q.xp_reward, "reward_gold": q.gold_reward,
            "reward_item": (Item.query.get(q.item_reward_id).name
                            if q.item_reward_id else None),
        })

    return jsonify({"active": active, "available": available})


@quest_bp.post("/quest/accept/<int:quest_id>")
@login_required
def accept(quest_id):
    q = Quest.query.get_or_404(quest_id)
    if CharacterQuest.query.filter_by(
        character_id=current_user.id, quest_id=quest_id
    ).first():
        return jsonify({"error": "already_taken"}), 400

    if q.requires_quest_id:
        prev = CharacterQuest.query.filter_by(
            character_id=current_user.id,
            quest_id=q.requires_quest_id,
            status="turned_in",
        ).first()
        if not prev:
            return jsonify({"error": "prereq_not_done"}), 400

    npc = NPC.query.get(q.npc_id)
    if not npc or npc.location_id != current_user.location_id:
        return jsonify({"error": "npc_not_here"}), 400

    # авто-прогресс для collect: считаем уже имеющееся
    initial = 0
    if q.req_type == "collect":
        try:
            target_item_id = int(q.req_target)
            initial = min(q.req_count,
                          count_in_inventory(current_user, target_item_id))
        except (ValueError, TypeError):
            pass

    cq = CharacterQuest(character_id=current_user.id, quest_id=quest_id,
                        progress=initial, status="active")
    db.session.add(cq)
    db.session.commit()
    return jsonify({"ok": True, "cq_id": cq.id})


@quest_bp.post("/quest/turnin/<int:cq_id>")
@login_required
def turnin(cq_id):
    cq = CharacterQuest.query.filter_by(
        id=cq_id, character_id=current_user.id
    ).first()
    if not cq:
        return jsonify({"error": "not_found"}), 404
    if cq.status != "active":
        return jsonify({"error": "not_active"}), 400
    if not cq.quest:
        return jsonify({"error": "quest_broken"}), 500
    if not is_complete(cq):
        return jsonify({"error": "not_complete",
                        "progress": cq.progress,
                        "required": cq.quest.req_count}), 400

    npc = NPC.query.get(cq.quest.npc_id)
    if npc and npc.location_id != current_user.location_id:
        return jsonify({"error": "npc_not_here"}), 400

    grant_rewards(current_user, cq.quest)
    cq.status = "turned_in"

    current_user.quests_done = (current_user.quests_done or 0) + 1
    from app.services.achievements import check_achievements
    check_achievements(current_user)

    db.session.commit()
    return jsonify({"ok": True,
                    "gold": current_user.gold, "level": current_user.level})