from datetime import datetime, timedelta
from app.extensions import db
from app.models import Zombie, Combat, LootPoint, Character
from app.services import combat_engine, events
from app.api.auction import expire_auctions
from config import Config


def run_lazy_tick():
    now = datetime.utcnow()
    _respawn_zombies(now)
    _respawn_loot(now)
    _tick_survival(now)
    events.tick_events(now)
    expire_auctions(now)
    _tick_active_combats(now)


def _tick_survival(now):
    chars = Character.query.filter(Character.hp > 0).all()
    for c in chars:
        if not c.last_seen_at: continue
        delta_sec = (now - c.last_seen_at).total_seconds()
        if delta_sec < 30: continue

        minutes = int(delta_sec // 60)
        if minutes > 0:
            c.hunger = max(0, c.hunger - minutes)
            c.thirst = max(0, c.thirst - (minutes * 2))

            if c.hunger == 0: c.hp -= (minutes * 1)
            if c.thirst == 0: c.hp -= (minutes * 2)

            if c.hp <= 0: c.hp = 0
            c.last_seen_at = now


def _respawn_zombies(now):
    dead = Zombie.query.filter(
        Zombie.state == "dead",
        Zombie.respawn_at.isnot(None),
        Zombie.respawn_at <= now,
        Zombie.is_event_zombie == False
    ).all()
    for z in dead:
        z.state = "alive"
        z.hp = z.max_hp
        z.respawn_at = None
        z.engaged_combat_id = None


def _respawn_loot(now):
    LootPoint.query.filter(
        LootPoint.kind != "corpse",
        LootPoint.kind != "airdrop",
        LootPoint.state == "looted",
        LootPoint.respawn_at.isnot(None),
        LootPoint.respawn_at <= now,
    ).update({"state": "available", "respawn_at": None}, synchronize_session=False)

    expired = LootPoint.query.filter(
        LootPoint.kind == "corpse",
        LootPoint.respawn_at.isnot(None),
        LootPoint.respawn_at <= now,
    ).all()
    for lp in expired:
        LootPoint.query.filter_by(id=lp.id).delete()


def _tick_active_combats(now):
    for combat in Combat.query.filter_by(status="active").all():
        _tick_combat(combat, now)


def _tick_combat(combat, now):
    if (now - combat.last_activity_at).total_seconds() > Config.COMBAT_ABANDON_SEC:
        combat_engine.abandon_combat(combat)
        return

    combat_engine.tick_effects(combat, now)

    if combat.zombie.hp <= 0:
        combat_engine.resolve_victory(combat)
        return

    if all(p.is_dead for p in combat.participants):
        combat_engine.resolve_defeat(combat)
        return

    if combat.next_zombie_attack_at and now >= combat.next_zombie_attack_at:
        combat_engine.zombie_attack(combat, now)
        if combat.status != "active":
            return

    cooldown = timedelta(seconds=Config.COMBAT_ACTION_COOLDOWN_SEC)
    for p in combat.participants:
        if combat.status != "active": break
        if p.is_dead or not p.auto_mode: continue
        if now - p.last_action_at < cooldown: continue
        combat_engine.auto_action(combat, p, now)