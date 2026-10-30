from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from app.extensions import db
from app.models import Contract, CharacterQuest, Quest

contract_bp = Blueprint("contract", __name__)


@contract_bp.post("/contracts/accept/<int:contract_id>")
@login_required
def accept_contract(contract_id):
    c = Contract.query.get_or_404(contract_id)

    # Упрощенно: создаем скрытый квест
    q = Quest(
        npc_id=c.npc_id, name=c.title, description=c.description,
        req_type=c.req_type, req_target=c.req_target, req_count=c.req_count,
        xp_reward=c.reward_xp, gold_reward=c.reward_gold
    )
    db.session.add(q)
    db.session.flush()

    cq = CharacterQuest(character_id=current_user.id, quest_id=q.id, progress=0, status="active")
    db.session.add(cq)
    db.session.commit()
    return jsonify({"ok": True})