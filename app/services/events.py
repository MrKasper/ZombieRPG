import random
import time
from datetime import datetime, timedelta
from app.extensions import db
from app.models import (GameEvent, Location, Zombie, ZombieType, Spawn,
                        LootPoint, Item)


EVENT_DEFS = [
    {"type": "airdrop",      "interval_min": 30, "offset_min": 5,
     "duration_sec": 300, "needs_location": True},
    {"type": "zombie_night", "interval_min": 60, "offset_min": 20,
     "duration_sec": 300, "needs_location": True},
    {"type": "bounty",       "interval_min": 45, "offset_min": 10,
     "duration_sec": 480, "needs_location": False},
]


# ---------- планировщик ----------

def _should_be_active(interval_min, offset_min, duration_sec):
    total = int(time.time())
    cycle = interval_min * 60
    offset = offset_min * 60
    into_cycle = (total - offset) % cycle
    return into_cycle < duration_sec


def tick_events(now=None):
    now = now or datetime.utcnow()

    # 1. закрываем протухшие
    expired = GameEvent.query.filter(
        GameEvent.state == "active",
        GameEvent.ends_at <= now,
    ).all()
    for ev in expired:
        _finish_event(ev)

    # 2. запускаем новые
    active_types = {ev.type for ev in
                    GameEvent.query.filter_by(state="active").all()}

    for defn in EVENT_DEFS:
        if defn["type"] in active_types:
            continue
        if not _should_be_active(defn["interval_min"],
                                 defn["offset_min"],
                                 defn["duration_sec"]):
            continue
        _start_event(defn, now)


def _start_event(defn, now):
    ev = GameEvent(
        type=defn["type"],
        started_at=now,
        ends_at=now + timedelta(seconds=defn["duration_sec"]),
        state="active",
        data_json={},
    )

    loc = None
    if defn.get("needs_location"):
        locs = Location.query.filter_by(is_safe_zone=False).all()
        if not locs:
            return
        loc = random.choice(locs)
        ev.location_id = loc.id

    db.session.add(ev)
    db.session.flush()

    if ev.type == "airdrop":
        _start_airdrop(ev, loc)
    elif ev.type == "zombie_night":
        _start_zombie_night(ev, loc)
    elif ev.type == "bounty":
        _start_bounty(ev)

    db.session.flush()


def _start_airdrop(ev, loc):
    items = {i.name: i.id for i in Item.query.all()}
    candidates = [
        ("Дробовик", 0.3), ("Арбалет", 0.2), ("Катана", 0.2),
        ("СВД", 0.1), ("Бронежилет", 0.3), ("Шлем военный", 0.2),
        ("Тактический жилет", 0.05),
        ("Книга: Граната", 0.15), ("Книга: Снайперский выстрел", 0.1),
        ("Книга: Ярость", 0.05),
        ("Стимулятор", 0.4), ("Антибиотик", 0.3), ("Антирад", 0.3),
        ("Электроника", 0.4), ("Металл", 0.5),
    ]
    table = []
    for name, chance in candidates:
        if name in items:
            table.append({"item_id": items[name],
                          "chance": chance, "qty": [1, 1]})

    taken = {(lp.x, lp.y) for lp in
             LootPoint.query.filter_by(location_id=loc.id).all()}
    x, y = loc.grid_w // 2, loc.grid_h // 2
    for _ in range(40):
        nx = random.randint(1, max(1, loc.grid_w - 2))
        ny = random.randint(1, max(1, loc.grid_h - 2))
        if (nx, ny) not in taken:
            x, y = nx, ny
            break

    lp = LootPoint(
        location_id=loc.id, x=x, y=y, kind="airdrop",
        loot_table=table, gold=random.randint(50, 150),
        state="available",
    )
    db.session.add(lp)
    db.session.flush()

    ev.data_json = {"loot_point_id": lp.id}


def _start_zombie_night(ev, loc):
    existing = Zombie.query.filter_by(location_id=loc.id, state="alive").all()
    taken = {(z.x, z.y) for z in existing}

    spawns = Spawn.query.filter_by(location_id=loc.id).all()
    if not spawns:
        return

    spawned_ids = []
    for sp in spawns:
        zt = ZombieType.query.get(sp.zombie_type_id)
        if not zt:
            continue
        for _ in range(sp.max_count):
            x, y = loc.grid_w // 2, loc.grid_h // 2
            for _ in range(40):
                nx = random.randint(1, max(1, loc.grid_w - 2))
                ny = random.randint(1, max(1, loc.grid_h - 2))
                if (nx, ny) not in taken:
                    x, y = nx, ny
                    break
            taken.add((x, y))
            z = Zombie(
                type_id=zt.id, location_id=loc.id,
                hp=zt.max_hp, max_hp=zt.max_hp,
                x=x, y=y, state="alive", is_event_zombie=True,
            )
            db.session.add(z)
            db.session.flush()
            spawned_ids.append(z.id)

    ev.data_json = {"zombie_ids": spawned_ids}


def _start_bounty(ev):
    types = ZombieType.query.all()
    if not types:
        return
    zt = random.choice(types)
    ev.data_json = {
        "zombie_type_id": zt.id,
        "zombie_name": zt.name,
        "multiplier": 3,
    }


def _finish_event(ev):
    ev.state = "finished"

    if ev.type == "airdrop":
        lp_id = (ev.data_json or {}).get("loot_point_id")
        if lp_id:
            lp = LootPoint.query.get(lp_id)
            if lp and lp.state == "available":
                db.session.delete(lp)

    elif ev.type == "zombie_night":
        ids = (ev.data_json or {}).get("zombie_ids", [])
        if ids:
            zombies = Zombie.query.filter(Zombie.id.in_(ids)).all()
            for z in zombies:
                if z.state == "alive" and z.engaged_combat_id is None:
                    db.session.delete(z)


# ---------- чтение для API ----------

def get_active_events():
    now = datetime.utcnow()
    events = GameEvent.query.filter(
        GameEvent.state == "active",
        GameEvent.ends_at > now,
    ).all()

    result = []
    for ev in events:
        data = ev.data_json or {}
        entry = {
            "id": ev.id,
            "type": ev.type,
            "ends_at": ev.ends_at.isoformat(),
            "seconds_left": max(0, int((ev.ends_at - now).total_seconds())),
        }
        if ev.location_id:
            loc = Location.query.get(ev.location_id)
            if loc:
                entry["location"] = {"id": loc.id, "name": loc.name}
        if ev.type == "bounty":
            entry["zombie_name"] = data.get("zombie_name")
            entry["multiplier"] = data.get("multiplier", 2)
        result.append(entry)
    return result


def get_bounty_multiplier(zombie_type_id):
    now = datetime.utcnow()
    ev = GameEvent.query.filter(
        GameEvent.type == "bounty",
        GameEvent.state == "active",
        GameEvent.ends_at > now,
    ).first()
    if not ev:
        return 1
    data = ev.data_json or {}
    if data.get("zombie_type_id") == zombie_type_id:
        return data.get("multiplier", 1)
    return 1