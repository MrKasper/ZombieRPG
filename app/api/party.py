from datetime import datetime
from flask import Blueprint, jsonify
from flask_login import current_user, login_required
from app.extensions import db
from app.models import Party, PartyInvite, Character, Location
from config import Config

party_bp = Blueprint("party", __name__)


@party_bp.post("/party/create")
@login_required
def create_party():
    if current_user.party_id:
        return jsonify({"error": "already_in_party"}), 400
    party = Party(leader_id=current_user.id, name=f"Отряд {current_user.name}")
    db.session.add(party)
    db.session.flush()
    current_user.party_id = party.id
    db.session.commit()
    return jsonify({"ok": True, "party_id": party.id})


@party_bp.post("/party/invite/<int:character_id>")
@login_required
def invite(character_id):
    if not current_user.party_id:
        return jsonify({"error": "not_in_party"}), 400
    party = Party.query.get(current_user.party_id)
    if not party:
        return jsonify({"error": "party_not_found"}), 404
    if party.leader_id != current_user.id:
        return jsonify({"error": "not_leader"}), 403

    target = Character.query.get(character_id)
    if not target:
        return jsonify({"error": "no_such_character"}), 404
    if target.id == current_user.id:
        return jsonify({"error": "self_invite"}), 400
    if target.party_id:
        return jsonify({"error": "target_in_party"}), 400
    if len(party.members) >= Config.MAX_PARTY_SIZE:
        return jsonify({"error": "party_full"}), 400

    if PartyInvite.query.filter_by(
        party_id=party.id, to_id=target.id, status="pending"
    ).first():
        return jsonify({"error": "already_invited"}), 400

    inv = PartyInvite(party_id=party.id, from_id=current_user.id, to_id=target.id)
    db.session.add(inv)
    db.session.commit()
    return jsonify({"ok": True, "invite_id": inv.id})


@party_bp.get("/party/invites")
@login_required
def my_invites():
    rows = (PartyInvite.query
            .filter_by(to_id=current_user.id, status="pending")
            .order_by(PartyInvite.id.desc()).limit(10).all())
    inviter_names = {c.id: c.name for c in
                     Character.query.filter(Character.id.in_([i.from_id for i in rows])).all()}
    return jsonify({"invites": [
        {"id": i.id, "from_name": inviter_names.get(i.from_id, "?"),
         "created_at": i.created_at.isoformat()} for i in rows
    ]})


@party_bp.post("/party/accept/<int:invite_id>")
@login_required
def accept_invite(invite_id):
    inv = PartyInvite.query.filter_by(
        id=invite_id, to_id=current_user.id, status="pending"
    ).first()
    if not inv:
        return jsonify({"error": "invite_not_found"}), 404
    if current_user.party_id:
        return jsonify({"error": "already_in_party"}), 400

    party = Party.query.get(inv.party_id)
    if not party:
        inv.status = "expired"
        db.session.commit()
        return jsonify({"error": "party_gone"}), 404
    if len(party.members) >= Config.MAX_PARTY_SIZE:
        inv.status = "declined"
        db.session.commit()
        return jsonify({"error": "party_full"}), 400

    current_user.party_id = party.id
    inv.status = "accepted"
    db.session.commit()
    return jsonify({"ok": True, "party_id": party.id})


@party_bp.post("/party/decline/<int:invite_id>")
@login_required
def decline_invite(invite_id):
    inv = PartyInvite.query.filter_by(
        id=invite_id, to_id=current_user.id, status="pending"
    ).first()
    if not inv:
        return jsonify({"error": "invite_not_found"}), 404
    inv.status = "declined"
    db.session.commit()
    return jsonify({"ok": True})


@party_bp.post("/party/leave")
@login_required
def leave():
    if not current_user.party_id:
        return jsonify({"error": "not_in_party"}), 400
    party = Party.query.get(current_user.party_id)
    was_leader = party and party.leader_id == current_user.id
    current_user.party_id = None

    if party:
        remaining = [m for m in party.members if m.id != current_user.id]
        if was_leader:
            if remaining:
                party.leader_id = remaining[0].id
            else:
                for m in remaining:
                    m.party_id = None
                db.session.delete(party)

    db.session.commit()
    return jsonify({"ok": True})


@party_bp.post("/party/kick/<int:character_id>")
@login_required
def kick(character_id):
    if not current_user.party_id:
        return jsonify({"error": "not_in_party"}), 400
    party = Party.query.get(current_user.party_id)
    if not party or party.leader_id != current_user.id:
        return jsonify({"error": "not_leader"}), 403

    target = Character.query.filter_by(id=character_id, party_id=party.id).first()
    if not target:
        return jsonify({"error": "not_in_party"}), 404

    target.party_id = None
    db.session.commit()
    return jsonify({"ok": True})


@party_bp.post("/party/disband")
@login_required
def disband():
    if not current_user.party_id:
        return jsonify({"error": "not_in_party"}), 400
    party = Party.query.get(current_user.party_id)
    if not party or party.leader_id != current_user.id:
        return jsonify({"error": "not_leader"}), 403

    for m in list(party.members):
        m.party_id = None
    db.session.delete(party)
    db.session.commit()
    return jsonify({"ok": True})