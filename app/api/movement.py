from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from app.extensions import db
from app.models import Location, LocationExit, Combat, LootPoint, Obstacle, Inventory, Item
from app.services import tick, combat_engine
from app.services.progression import get_stats
from app.services.quest_service import progress_quests
from app.services.spawn import cell_blocked, find_free_cell
from app.services.loot import collect_from_lootpoint

movement_bp = Blueprint("movement", __name__)

def _ensure_not_in_combat():
    if current_user.in_combat_id:
        c = Combat.query.get(current_user.in_combat_id)
        if c and c.status == "active": return False
        current_user.in_combat_id = None
    return True

def _spawn_near_exit(new_loc, from_loc_id, exclude_id):
    back = LocationExit.query.filter_by(from_id=new_loc.id, to_id=from_loc_id).first()
    if back:
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
            nx, ny = back.x + dx, back.y + dy
            if 0 <= nx < new_loc.grid_w and 0 <= ny < new_loc.grid_h:
                if not cell_blocked(new_loc, nx, ny, exclude_id): return nx, ny
    return find_free_cell(new_loc, exclude_char_id=exclude_id, prefer_center=True)

@movement_bp.post("/move/step")
@login_required
def step():
    tick.run_lazy_tick()
    if not _ensure_not_in_combat(): return jsonify({"error": "in_combat"}), 400

    data = request.get_json(silent=True) or {}
    dx = int(data.get("dx", 0))
    dy = int(data.get("dy", 0))
    if abs(dx) + abs(dy) != 1: return jsonify({"error": "bad_step"}), 400

    loc = current_user.location
    nx = current_user.x + dx
    ny = current_user.y + dy

    if nx < 0 or ny < 0 or nx >= loc.grid_w or ny >= loc.grid_h: return jsonify({"error": "out_of_bounds"}), 400

    if cell_blocked(loc, nx, ny, exclude_char_id=current_user.id):
        obs = Obstacle.query.filter_by(location_id=loc.id, x=nx, y=ny).first()
        if obs and obs.kind == "door_locked":
            has_key = Inventory.query.filter(Inventory.character_id == current_user.id).join(Inventory.item).filter_by(name="Ключ-карта").first()
            if has_key:
                obs.kind = "door"
                db.session.commit()
                return jsonify({"ok": True, "msg": "unlocked"})
        return jsonify({"error": "cell_blocked"}), 400

    current_user.x = nx
    current_user.y = ny
    current_user.last_seen_at = datetime.utcnow()

    picked = []
    loot_picked_from = False
    lp = LootPoint.query.filter_by(location_id=loc.id, x=nx, y=ny, state="available").first()
    if lp:
        picked = collect_from_lootpoint(lp, current_user)
        loot_picked_from = True

    combat_triggered = combat_engine.check_zombie_aggro(current_user)
    db.session.commit()
    return jsonify({"ok": True, "x": nx, "y": ny, "picked": picked, "loot_picked_from": loot_picked_from, "combat_triggered": combat_triggered})

@movement_bp.post("/move")
@login_required
def move():
    tick.run_lazy_tick()
    if not _ensure_not_in_combat(): return jsonify({"error": "in_combat"}), 400

    data = request.get_json(silent=True) or {}
    direction = data.get("direction")
    to_id = data.get("to_id")

    exit_row = None
    if direction: exit_row = LocationExit.query.filter_by(from_id=current_user.location_id, direction=direction).first()
    elif to_id: exit_row = LocationExit.query.filter_by(from_id=current_user.location_id, to_id=to_id).first()

    if not exit_row: return jsonify({"error": "no_exit"}), 400

    dist = abs(current_user.x - exit_row.x) + abs(current_user.y - exit_row.y)
    if dist > 1: return jsonify({"error": "too_far_from_exit"}), 400

    from_loc_id = current_user.location_id
    new_loc = Location.query.get(exit_row.to_id)
    sx, sy = _spawn_near_exit(new_loc, from_loc_id, current_user.id)

    current_user.location_id = new_loc.id
    current_user.x = sx
    current_user.y = sy
    current_user.last_seen_at = datetime.utcnow()

    visited = list(current_user.visited_locations or [])
    if new_loc.id not in visited:
        visited.append(new_loc.id)
        current_user.visited_locations = visited

    progress_quests(current_user, "visit", new_loc.id, 1)

    healed = False
    if new_loc.is_safe_zone:
        stats = get_stats(current_user)
        current_user.hp = stats["max_hp"]
        current_user.mp = stats["max_mp"]
        healed = True

    db.session.commit()
    return jsonify({"ok": True, "location": {"id": new_loc.id, "name": new_loc.name, "is_safe_zone": new_loc.is_safe_zone}, "x": sx, "y": sy, "healed": healed})