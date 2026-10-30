import random
from datetime import datetime, timedelta
from app.extensions import db
from app.models import (Character, Zombie, Combat, CombatParticipant,
                        CharacterSkill, Skill, Party, Spawn, Location,
                        CombatEffect, Inventory, LootPoint, Item)
from app.services.progression import get_stats
from app.services.loot import roll_loot, add_to_inventory
from app.services.events import get_bounty_multiplier
from config import Config


def calc_damage(attacker_attack, defender_defense, multiplier=1.0):
    raw = attacker_attack * multiplier * random.uniform(0.9, 1.1)
    mitigated = raw * (100 / (100 + max(0, defender_defense)))
    return max(1, round(mitigated))


# ---------- эффекты ----------

def tick_effects(combat, now):
    for p in combat.participants:
        if p.is_dead:
            continue
        for e in list(p.effects or []):
            if e.turns_left <= 0:
                continue
            if e.type in ("bleed", "poison"):
                char = p.character
                char.hp -= e.value
                combat.append_log(
                    f"{'🩸' if e.type == 'bleed' else '☠️'} "
                    f"{char.name} теряет {e.value} HP ({e.type})"
                )
                e.turns_left -= 1
                if char.hp <= 0:
                    char.hp = 0
                    p.is_dead = True
                    combat.append_log(f"💀 {char.name} повержен эффектом!")
            elif e.type in ("buff_attack", "buff_defense"):
                e.turns_left -= 1

            if e.turns_left <= 0:
                db.session.delete(e)


def apply_effect(participant, eff_type, value=0, turns=1):
    existing = CombatEffect.query.filter_by(
        participant_id=participant.id, type=eff_type
    ).first()
    if existing:
        existing.turns_left = max(existing.turns_left, turns)
        existing.value = max(existing.value, value)
    else:
        db.session.add(CombatEffect(
            participant_id=participant.id, type=eff_type,
            value=value, turns_left=turns,
        ))


def get_stun(participant):
    return (CombatEffect.query
            .filter_by(participant_id=participant.id, type="stun")
            .filter(CombatEffect.turns_left > 0).first())


def get_buff(participant, eff_type):
    return (CombatEffect.query
            .filter_by(participant_id=participant.id, type=eff_type)
            .filter(CombatEffect.turns_left > 0).first())


# ---------- вход/выход ----------

def join_combat(character, zombie, now=None):
    now = now or datetime.utcnow()

    if zombie.engaged_combat_id:
        existing = Combat.query.get(zombie.engaged_combat_id)
        if existing and existing.status == "active":
            party_ids = {
                p.character.party_id for p in existing.participants
                if not p.is_dead and p.character.party_id
            }
            if character.party_id is None or character.party_id not in party_ids:
                return {"error": "zombie_busy"}
            return _add_participant(existing, character, now)
        zombie.engaged_combat_id = None
        zombie.state = "alive"
        zombie.hp = zombie.max_hp

    if zombie.state != "alive" or zombie.hp <= 0:
        return {"error": "zombie_dead"}
    if character.hp <= 0:
        return {"error": "you_are_dead"}

    combat = Combat(
        zombie_id=zombie.id,
        status="active",
        log=[f"⚔️ {character.name} атакует {zombie.type.name}!"],
        next_zombie_attack_at=now + timedelta(
            seconds=Config.ZOMBIE_ATTACK_INTERVAL_SEC
        ),
        last_activity_at=now,
    )
    db.session.add(combat)
    db.session.flush()

    zombie.state = "engaged"
    zombie.engaged_combat_id = combat.id
    _add_participant(combat, character, now, silent=True)

    if character.party_id:
        party = Party.query.get(character.party_id)
        if party:
            for member in party.members:
                if member.id == character.id:
                    continue
                if member.in_combat_id or member.hp <= 0:
                    continue
                if member.location_id != character.location_id:
                    continue
                _add_participant(combat, member, now)

    return {"ok": True, "combat_id": combat.id}


def _add_participant(combat, character, now, silent=False):
    existing = CombatParticipant.query.filter_by(
        combat_id=combat.id, character_id=character.id
    ).first()
    if existing:
        if existing.is_dead:
            existing.is_dead = False
            existing.last_action_at = now
            if not silent:
                combat.append_log(f"↩️ {character.name} возвращается в бой")
        return {"ok": True, "combat_id": combat.id}

    db.session.add(CombatParticipant(
        combat_id=combat.id,
        character_id=character.id,
        last_action_at=now,
        auto_mode=False,
    ))
    character.in_combat_id = combat.id
    if not silent:
        combat.append_log(f"➕ {character.name} вступает в бой")
    return {"ok": True, "combat_id": combat.id}


# ---------- ход игрока ----------

def player_attack(combat, participant, skill_id=None, now=None):
    now = now or datetime.utcnow()
    if combat.status != "active":
        return {"error": "combat_finished"}
    if participant.is_dead:
        return {"error": "you_are_dead"}

    stun = get_stun(participant)
    if stun:
        participant.last_action_at = now
        combat.append_log(f"💫 {participant.character.name} оглушён и пропускает ход")
        stun.turns_left -= 1
        if stun.turns_left <= 0:
            db.session.delete(stun)
        combat.last_activity_at = now
        return {"ok": True, "damage": 0, "stunned": True}

    cooldown = timedelta(seconds=Config.COMBAT_ACTION_COOLDOWN_SEC)
    if now - participant.last_action_at < cooldown:
        return {"error": "cooldown"}

    char = participant.character
    stats = get_stats(char)

    cs = None
    skill = None
    if skill_id:
        cs = CharacterSkill.query.filter_by(
            character_id=char.id, skill_id=skill_id
        ).first()
        if not cs:
            return {"error": "skill_not_learned"}
        if cs.cooldown_until and cs.cooldown_until > now:
            return {"error": "skill_cooldown"}
        skill = cs.skill
        if char.mp < skill.mp_cost:
            return {"error": "not_enough_mp"}

    if skill:
        char.mp -= skill.mp_cost
        cs.cooldown_until = now + timedelta(seconds=skill.cooldown_sec)

    multiplier = skill.damage_mult if skill else 1.0
    buff = get_buff(participant, "buff_attack")
    if buff:
        multiplier *= (1 + buff.value / 100)

    dmg = calc_damage(stats["attack"], combat.zombie.type.defense, multiplier)
    combat.zombie.hp -= dmg
    participant.damage_dealt += dmg

    skill_name = f" ({skill.name})" if skill else ""
    combat.append_log(
        f"🗡️ {char.name} наносит {dmg} урона {combat.zombie.type.name}{skill_name}"
    )

    if cs:
        cs.level = min(10.0, cs.level + 0.1)

    participant.last_action_at = now
    combat.last_activity_at = now

    if combat.zombie.hp <= 0:
        combat.zombie.hp = 0
        resolve_victory(combat)
        return {"ok": True, "damage": dmg, "victory": True}

    return {"ok": True, "damage": dmg}


def auto_action(combat, participant, now):
    char = participant.character
    stats = get_stats(char)

    if char.hp < stats["max_hp"] * 0.3:
        heal = _find_skill(char, now, effect="heal")
        if heal:
            return _try_skill_or_basic(combat, participant, heal, now)

    dmg_skill = _find_skill(char, now, effect="damage")
    if dmg_skill:
        return _try_skill_or_basic(combat, participant, dmg_skill, now)

    return player_attack(combat, participant, skill_id=None, now=now)


def _find_skill(char, now, effect="damage"):
    rows = (CharacterSkill.query
            .join(Skill, Skill.id == CharacterSkill.skill_id)
            .filter(CharacterSkill.character_id == char.id,
                    Skill.effect_type == effect,
                    Skill.mp_cost <= char.mp)
            .all())
    available = [cs for cs in rows
                 if not cs.cooldown_until or cs.cooldown_until <= now]
    if not available:
        return None
    return min(available, key=lambda cs: cs.skill.mp_cost).skill.id


def _try_skill_or_basic(combat, participant, skill_id, now):
    res = player_attack(combat, participant, skill_id=skill_id, now=now)
    if "error" in res and res["error"] in ("not_enough_mp", "skill_cooldown"):
        return player_attack(combat, participant, skill_id=None, now=now)
    return res


# ---------- ход зомби ----------

def zombie_attack(combat, now):
    if combat.status != "active":
        return
    z = combat.zombie
    if z.hp <= 0:
        return

    alive = [p for p in combat.participants
             if not p.is_dead and p.character.hp > 0]
    if not alive:
        resolve_defeat(combat)
        return

    zt = z.type
    attack_type = zt.attack_type or "normal"

    if attack_type == "aoe":
        for target in alive:
            _apply_zombie_hit(combat, z, target, 1.0)
            if combat.status != "active":
                break

    elif attack_type == "fast":
        target = random.choice(alive)
        _apply_zombie_hit(combat, z, target, 1.0)
        if not target.is_dead and combat.status == "active":
            _apply_zombie_hit(combat, z, target, 0.7)

    elif attack_type == "poison":
        target = random.choice(alive)
        _apply_zombie_hit(combat, z, target, 1.0)
        if not target.is_dead and random.random() < 0.4:
            apply_effect(target, "poison", value=3, turns=3)
            combat.append_log(f"☠️ {target.character.name} отравлен!")

    elif attack_type == "stun":
        target = random.choice(alive)
        _apply_zombie_hit(combat, z, target, 1.0)
        stun_chance = zt.stun_chance or 0.2
        if not target.is_dead and random.random() < stun_chance:
            apply_effect(target, "stun", value=0, turns=1)
            combat.append_log(f"💫 {target.character.name} оглушён!")

    else:
        target = random.choice(alive)
        _apply_zombie_hit(combat, z, target, 1.0)

    if combat.status != "active":
        return

    combat.next_zombie_attack_at = now + timedelta(
        seconds=Config.ZOMBIE_ATTACK_INTERVAL_SEC
    )
    combat.last_activity_at = now

    if all(p.is_dead for p in combat.participants):
        resolve_defeat(combat)


def _apply_zombie_hit(combat, zombie, target, mult=1.0):
    char = target.character
    stats = get_stats(char)

    # уворот
    evasion = stats.get("evasion", 0)
    if evasion > 0 and random.random() * 100 < evasion:
        combat.append_log(f"💨 {char.name} уклоняется от {zombie.type.name}!")
        return

    defense = stats["defense"]
    buff = get_buff(target, "buff_defense")
    if buff:
        defense += buff.value

    dmg = calc_damage(zombie.type.attack, defense, mult)
    char.hp -= dmg
    combat.append_log(f"🧟 {zombie.type.name} бьёт {char.name} на {dmg}")

    if char.hp <= 0:
        char.hp = 0
        target.is_dead = True
        combat.append_log(f"💀 {char.name} повержен!")


# ---------- разрешение боя ----------

def resolve_victory(combat):
    if combat.status != "active":
        return
    from app.services.quest_service import progress_quests
    from app.services.achievements import check_achievements

    z = combat.zombie
    ztype = z.type
    combat.status = "victory"
    combat.append_log(f"🏆 {ztype.name} повержен!")

    if z.is_event_zombie:
        db.session.delete(z)
    else:
        spawn = Spawn.query.filter_by(
            location_id=z.location_id, zombie_type_id=z.type_id
        ).first()
        respawn_sec = spawn.respawn_sec if spawn else 60
        z.state = "dead"
        z.respawn_at = datetime.utcnow() + timedelta(seconds=respawn_sec)
        z.engaged_combat_id = None

    for p in combat.participants:
        if p.is_dead:
            continue
        char = p.character

        bounty_mult = get_bounty_multiplier(ztype.id)
        xp_gain = ztype.xp_reward * bounty_mult
        gold_gain = ztype.gold_reward * bounty_mult

        char.add_xp(xp_gain)
        char.gold += gold_gain
        if bounty_mult > 1:
            combat.append_log(f"🎯 Бонус охоты: ×{bounty_mult}!")

        char.kills_total = (char.kills_total or 0) + 1
        if ztype.name in ("Tank", "Patient Zero"):
            char.boss_kills = (char.boss_kills or 0) + 1

        progress_quests(char, "kill", ztype.id, 1)
        combat.append_log(f"✨ {char.name} получает {xp_gain} XP")
        for drop in roll_loot(ztype):
            add_to_inventory(char, drop["item_id"], drop["qty"])

        for e in list(p.effects or []):
            db.session.delete(e)

    for p in combat.participants:
        if not p.is_dead:
            check_achievements(p.character)


def resolve_defeat(combat):
    if combat.status != "active":
        return
    from app.services.spawn import find_free_cell
    from app.services.achievements import check_achievements

    combat.status = "defeat"
    combat.append_log("💀 Партия разбита...")

    safe = Location.query.filter_by(is_safe_zone=True).first()

    for p in combat.participants:
        char = p.character
        loc = char.location
        stats = get_stats(char)
        char.hp = max(1, stats["max_hp"] // 4)
        char.mp = stats["max_mp"] // 4
        penalty = max(1, int(char.xp_for_next_level() * 0.05))
        char.xp = max(0, char.xp - penalty)

        char.deaths = (char.deaths or 0) + 1

        lost_gold = int(char.gold * 0.3)
        char.gold -= lost_gold

        dropped_items = []
        equipped = Inventory.query.filter_by(character_id=char.id).filter(
            Inventory.equipped_slot.isnot(None)
        ).all()
        if equipped and random.random() < 0.5:
            inv = random.choice(equipped)
            dropped_items.append((inv.item_id, inv.quantity))
            db.session.delete(inv)
            from app.services.progression import invalidate_stats
            invalidate_stats(char)

        if (lost_gold > 0 or dropped_items) and loc:
            loot_table = []
            for item_id, qty in dropped_items:
                loot_table.append({
                    "item_id": item_id, "chance": 1.0, "qty": [qty, qty],
                })

            taken = {(lp.x, lp.y) for lp in
                     LootPoint.query.filter_by(location_id=loc.id).all()}
            x, y = loc.grid_w // 2, loc.grid_h // 2
            for _ in range(40):
                nx = random.randint(1, max(1, loc.grid_w - 2))
                ny = random.randint(1, max(1, loc.grid_h - 2))
                if (nx, ny) not in taken:
                    x, y = nx, ny
                    break

            db.session.add(LootPoint(
                location_id=loc.id, x=x, y=y, kind="corpse",
                loot_table=loot_table, gold=lost_gold,
                state="available",
                respawn_at=datetime.utcnow() + timedelta(minutes=10),
            ))

        for e in list(p.effects or []):
            db.session.delete(e)

        if safe:
            sx, sy = find_free_cell(safe, exclude_char_id=char.id,
                                    prefer_center=True)
            char.location_id = safe.id
            char.x = sx
            char.y = sy

    z = combat.zombie
    z.hp = z.max_hp
    z.state = "alive"
    z.engaged_combat_id = None

    for p in combat.participants:
        check_achievements(p.character)


def flee_combat(combat, participant):
    if combat.status != "active":
        return {"error": "combat_finished"}
    char = participant.character
    participant.is_dead = True
    char.in_combat_id = None
    combat.append_log(f"🏃 {char.name} сбежал из боя")

    for e in list(participant.effects or []):
        db.session.delete(e)

    if all(p.is_dead for p in combat.participants):
        combat.status = "fled"
        z = combat.zombie
        z.hp = z.max_hp
        z.state = "alive"
        z.engaged_combat_id = None
    return {"ok": True}


def abandon_combat(combat):
    if combat.status != "active":
        return
    combat.status = "abandoned"
    combat.append_log("⏳ Бой заброшен (таймаут)")
    for p in combat.participants:
        p.character.in_combat_id = None
        for e in list(p.effects or []):
            db.session.delete(e)
    z = combat.zombie
    z.hp = z.max_hp
    z.state = "alive"
    z.engaged_combat_id = None


# ---------- аггро ----------

def check_zombie_aggro(character):
    if character.in_combat_id or character.hp <= 0:
        return None

    loc = character.location
    if not loc or loc.is_safe_zone:
        return None

    zombies = Zombie.query.filter_by(location_id=loc.id, state="alive").all()
    nearest = None
    nearest_dist = 999
    for z in zombies:
        dist = abs(z.x - character.x) + abs(z.y - character.y)
        if dist <= 2 and dist < nearest_dist:
            nearest = z
            nearest_dist = dist

    if not nearest:
        return None

    result = join_combat(character, nearest)
    if "ok" in result:
        return {
            "combat_id": result["combat_id"],
            "zombie_id": nearest.id,
            "zombie_name": nearest.type.name,
        }
    return None