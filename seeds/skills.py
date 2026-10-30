from app.extensions import db
from app.models import Skill


SKILLS = [
    # name, icon, mp, cd, learn_lvl, effect, dmg_mult, heal_pct, buff_pct, buff_turns, outside, desc
    ("Удар прикладом", "🔨", 0, 3, 1, "damage", 0.9, 0, 0, 0, False,
     "Быстрый удар без затрат маны."),
    ("Точный выстрел", "🎯", 5, 3, 1, "damage", 1.5, 0, 0, 0, False,
     "Прицельный выстрел, +50% урона."),
    ("Аптечка", "🩹", 10, 15, 2, "heal", 0, 0.30, 0, 0, True,
     "Восстанавливает 30% HP. Можно применять вне боя."),
    ("Очередь", "💥", 15, 8, 5, "damage", 1.3, 0, 0, 0, False,
     "Шквальный огонь."),
    ("Адреналин", "💉", 15, 25, 7, "buff", 0, 0, 0.20, 3, False,
     "+20% к атаке на 3 раунда."),
    ("Граната", "💣", 20, 15, 10, "damage", 2.2, 0, 0, 0, False,
     "Взрыв с высоким уроном."),
    ("Снайперский выстрел", "🔭", 25, 12, 15, "damage", 3.0, 0, 0, 0, False,
     "Убойный выстрел в голову."),
    ("Ярость", "🔥", 30, 40, 20, "buff", 0, 0, 0.50, 3, False,
     "+50% к атаке на 3 раунда."),
]


def seed_skills(force=False):
    if Skill.query.count() > 0 and not force:
        print(f"Skills: skipped ({Skill.query.count()} exist)")
        return
    if force:
        Skill.query.delete()

    for name, icon, mp, cd, lvl, effect, dmult, hpct, bpct, bturns, outside, desc in SKILLS:
        db.session.add(Skill(
            name=name, icon=icon, mp_cost=mp, cooldown_sec=cd,
            learn_level=lvl, effect_type=effect, damage_mult=dmult,
            heal_percent=hpct, buff_attack_pct=bpct, buff_turns=bturns,
            can_use_outside=outside, description=desc,
        ))
    db.session.flush()
    print(f"Skills: seeded {len(SKILLS)}")