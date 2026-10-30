from datetime import datetime, timedelta
from flask import Blueprint, jsonify
from flask_login import current_user, login_required
from app.extensions import db
from app.models import (Character, Zombie, Combat, ChatMessage, Party,
                        PartyInvite, CharacterQuest, LootPoint, Decoration,
                        CharacterAchievement, Achievement, Auction, Duel,
                        Obstacle, LoreNote, Contract, ZombieType, Item, Location)
from app.services import tick, combat_engine
from app.services.progression import get_stats
from app.services.quest_service import is_complete
from app.services.events import get_active_events
from config import Config

state_bp = Blueprint("state", __name__)


@state_bp.get("/state")
@login_required
def get_state():
    tick.run_lazy_tick()
    current_user.last_seen_at = datetime.utcnow()
    combat_engine.check_zombie_aggro(current_user)
    db.session.commit()
    return jsonify(_build_state(current_user))


def _target_info(req_type, target):
    try:
        if req_type == "kill":
            zt = ZombieType.query.get(int(target))
            return {"name": zt.name if zt else "?", "icon": zt.icon if zt else "🧟"}
        if req_type == "collect":
            it = Item.query.get(int(target))
            return {"name": it.name if it else "?", "icon": it.icon if it else "📦"}
        if req_type == "visit":
            loc = Location.query.get(int(target))
            return {"name": loc.name if loc else "?", "icon": "🚩"}
    except (ValueError, TypeError):
        pass
    return {"name": "?", "icon": "❓"}


def _build_state(character):
    stats = get_stats(character)
    loc = character.location

    players_here = [p for p in Character.query.filter_by(location_id=loc.id).all() if p.id != character.id]
    zombies = Zombie.query.filter_by(location_id=loc.id, state="alive").all()
    loot_points = LootPoint.query.filter_by(location_id=loc.id).all()
    decorations = Decoration.query.filter_by(location_id=loc.id).all()
    obstacles = Obstacle.query.filter_by(location_id=loc.id).all()
    lore_notes = LoreNote.query.filter_by(location_id=loc.id).all()
    contracts = Contract.query.join(Contract.npc).filter_by(location_id=loc.id).all()

    combat_data = None
    if character.in_combat_id:
        c = Combat.query.get(character.in_combat_id)
        if c:
            combat_data = _serialize_combat(c, character)

    pending_invites = (
        PartyInvite.query.filter_by(to_id=character.id, status="pending").order_by(PartyInvite.id.desc()).limit(
            5).all())
    invite_names = {c.id: c.name for c in
                    Character.query.filter(Character.id.in_([i.from_id for i in pending_invites])).all()}

    def _msgs(scope, loc_id=None):
        q = ChatMessage.query.filter_by(scope=scope)
        if loc_id: q = q.filter_by(location_id=loc_id)
        rows = q.order_by(ChatMessage.id.desc()).limit(20).all()
        return [{"name": m.character.name if m.character else "?", "message": m.message,
                 "created_at": m.created_at.isoformat()} for m in reversed(rows)]

    active_quests_rows = CharacterQuest.query.filter_by(character_id=character.id, status="active").all()
    active_quests_data = []
    for cq in active_quests_rows:
        q = cq.quest
        if not q: continue
        info = _target_info(q.req_type, q.req_target)
        active_quests_data.append({
            "cq_id": cq.id,
            "name": q.name,
            "description": q.description,
            "req_type": q.req_type,
            "target_name": info["name"],
            "target_icon": info["icon"],
            "progress": cq.progress,
            "required": q.req_count,
            "complete": cq.progress >= q.req_count
        })

    quests_summary = {
        "active_count": len(active_quests_data),
        "ready_count": sum(1 for q in active_quests_data if q["complete"]),
    }

    unlocked_ach = CharacterAchievement.query.filter_by(character_id=character.id).all()
    achievements_summary = {
        "unlocked_count": len(unlocked_ach),
        "total": Achievement.query.count(),
        "new_unlocks": []
    }

    now_utc = datetime.utcnow()
    pending_duel_row = (Duel.query.filter_by(status="pending").filter(
        db.or_(Duel.challenger_id == character.id, Duel.target_id == character.id)).filter(
        Duel.expires_at > now_utc).order_by(Duel.id.desc()).first())

    pending_duel = None
    if pending_duel_row:
        pending_duel = {
            "id": pending_duel_row.id,
            "challenger_name": pending_duel_row.challenger.name,
            "target_name": pending_duel_row.target.name,
            "is_target": pending_duel_row.target_id == character.id,
            "seconds_left": max(0, int((pending_duel_row.expires_at - now_utc).total_seconds())),
        }

    return {
        "character": {
            "id": character.id, "name": character.name,
            "title": character.title or "Выживший",
            "level": character.level, "xp": character.xp, "xp_next": character.xp_for_next_level(),
            "hp": character.hp, "mp": character.mp, "gold": character.gold,
            "hunger": character.hunger, "thirst": character.thirst, "temperature": character.temperature,
            "stat_points": character.stat_points, "skill_points": character.skill_points, "stats": stats,
            "x": character.x, "y": character.y,
            "reputation": character.reputation_json or {},
            "visited_locations": character.visited_locations or [],
        },
        "location": {
            "id": loc.id, "name": loc.name, "description": loc.description,
            "is_safe_zone": loc.is_safe_zone, "danger_level": loc.danger_level,
            "grid_w": loc.grid_w, "grid_h": loc.grid_h, "tilemap_id": loc.tilemap_id,
            "exit_markers": [
                {"id": e.id, "to_id": e.to_id, "direction": e.direction, "to_name": e.to_loc.name, "x": e.x, "y": e.y}
                for e in loc.exits],
            "loot_points": [{"id": lp.id, "x": lp.x, "y": lp.y, "kind": lp.kind, "state": lp.state} for lp in
                            loot_points],
            "decorations": [{"id": d.id, "x": d.x, "y": d.y, "kind": d.kind, "alpha": d.alpha or 0.6} for d in
                            decorations],
            "obstacles": [{"id": o.id, "x": o.x, "y": o.y, "kind": o.kind, "variant": o.variant or "", "hp": o.hp or 0,
                           "max_hp": o.max_hp or 0} for o in obstacles],
            "lore_notes": [{"id": n.id, "x": n.x, "y": n.y, "title": n.title, "text": n.text} for n in lore_notes],
            # Добавлен npc_id для контрактов
            "contracts": [
                {"id": c.id, "npc_id": c.npc_id, "title": c.title, "desc": c.description, "req_type": c.req_type,
                 "req_target": c.req_target, "req_count": c.req_count, "gold": c.reward_gold, "xp": c.reward_xp} for c
                in contracts],
            "players": [{"id": p.id, "name": p.name, "level": p.level, "x": p.x, "y": p.y} for p in players_here],
            "zombies": [{"id": z.id, "name": z.type.name, "icon": z.type.icon, "level": z.type.level, "hp": z.hp,
                         "max_hp": z.max_hp, "x": z.x, "y": z.y} for z in zombies],
            "npcs": [{"id": n.id, "name": n.name, "role": n.role, "icon": n.icon} for n in loc.npcs],
        },
        "combat": combat_data,
        "party": None,
        "party_invites": [],
        "quests_summary": quests_summary,
        "active_quests": active_quests_data,
        "achievements": achievements_summary,
        "events": get_active_events(),
        "auction_active_count": Auction.query.filter_by(seller_id=character.id, status="active").count(),
        "pvp": {"wins": character.pvp_wins or 0, "losses": character.pvp_losses or 0, "pending_duel": pending_duel},
        "chat": {"location": _msgs("location", loc.id), "global": _msgs("global")},
    }


def _serialize_combat(combat, viewer):
    z = combat.zombie
    participants = []
    for p in combat.participants:
        entry = {
            "id": p.character.id, "name": p.character.name, "hp": p.character.hp,
            "max_hp": get_stats(p.character)["max_hp"], "is_dead": p.is_dead,
            "is_me": p.character_id == viewer.id, "auto_mode": p.auto_mode,
            "effects": [{"type": e.type, "value": e.value, "turns_left": e.turns_left} for e in (p.effects or []) if
                        e.turns_left > 0],
        }
        if p.character_id == viewer.id:
            elapsed = (datetime.utcnow() - p.last_action_at).total_seconds()
            entry["action_cd_remaining"] = round(max(0, Config.COMBAT_ACTION_COOLDOWN_SEC - elapsed), 2)
        participants.append(entry)

    return {
        "id": combat.id, "status": combat.status, "is_active": combat.status == "active",
        "round": combat.round,
        "zombie": {"id": z.id, "name": z.type.name, "icon": z.type.icon, "level": z.type.level, "hp": z.hp,
                   "max_hp": z.max_hp, "attack_type": z.type.attack_type or "normal"},
        "participants": participants,
        "log": (combat.log or [])[-30:],
        "next_zombie_attack_in": round(max(0, (combat.next_zombie_attack_at - datetime.utcnow()).total_seconds()),
                                       1) if combat.next_zombie_attack_at else 0,
    }