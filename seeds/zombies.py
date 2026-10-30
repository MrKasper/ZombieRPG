import random
from app.extensions import db
from app.models import ZombieType, Spawn, Zombie, Item, Location, Obstacle


ZOMBIES = [
    ("Walker", 1, 30, 3, 0, 8, 1, "🧟", "normal", 0.0,
     [{"item": "Бинт", "chance": 0.30, "qty": [1, 2]},
      {"item": "Ткань", "chance": 0.35, "qty": [1, 2]},
      {"item": "Кепка", "chance": 0.10, "qty": [1, 1]},
      {"item": "Консервы", "chance": 0.15, "qty": [1, 1]},
      {"item": "Футболка", "chance": 0.10, "qty": [1, 1]}]),
    ("Runner", 3, 25, 5, 0, 14, 2, "🧟‍♂️", "fast", 0.0,
     [{"item": "Энергетик", "chance": 0.25, "qty": [1, 1]},
      {"item": "Кеды", "chance": 0.10, "qty": [1, 1]},
      {"item": "Кожа", "chance": 0.30, "qty": [1, 2]},
      {"item": "Вода", "chance": 0.25, "qty": [1, 1]},
      {"item": "Шоколад", "chance": 0.15, "qty": [1, 1]}]),
    ("Crawler", 2, 18, 4, 0, 10, 1, "🦎", "fast", 0.0,
     [{"item": "Бинт", "chance": 0.20, "qty": [1, 1]},
      {"item": "Ткань", "chance": 0.30, "qty": [1, 1]},
      {"item": "Кожа", "chance": 0.25, "qty": [1, 1]}]),
    ("Spitter", 5, 45, 6, 2, 22, 4, "🧟‍♀️", "poison", 0.0,
     [{"item": "Обезболивающее", "chance": 0.20, "qty": [1, 1]},
      {"item": "Мачете", "chance": 0.05, "qty": [1, 1]},
      {"item": "Химикаты", "chance": 0.25, "qty": [1, 1]},
      {"item": "Антирад", "chance": 0.15, "qty": [1, 1]},
      {"item": "Стекло", "chance": 0.20, "qty": [1, 2]}]),
    ("Screamer", 6, 50, 7, 3, 30, 6, "😱", "stun", 0.40,
     [{"item": "Жгут", "chance": 0.25, "qty": [1, 1]},
      {"item": "Ткань", "chance": 0.30, "qty": [1, 2]},
      {"item": "Антибиотик", "chance": 0.10, "qty": [1, 1]},
      {"item": "Книга: Аптечка", "chance": 0.08, "qty": [1, 1]}]),
    ("Brute", 8, 90, 10, 5, 45, 8, "💪", "stun", 0.20,
     [{"item": "Аптечка", "chance": 0.30, "qty": [1, 1]},
      {"item": "Брюки карго", "chance": 0.10, "qty": [1, 1]},
      {"item": "Кожаная куртка", "chance": 0.10, "qty": [1, 1]},
      {"item": "Металл", "chance": 0.35, "qty": [1, 2]},
      {"item": "Топор", "chance": 0.08, "qty": [1, 1]}]),
    ("Tank", 15, 500, 20, 10, 300, 100, "🦍", "aoe", 0.0,
     [{"item": "Бронежилет", "chance": 0.40, "qty": [1, 1]},
      {"item": "Шлем военный", "chance": 0.30, "qty": [1, 1]},
      {"item": "Дробовик", "chance": 0.20, "qty": [1, 1]},
      {"item": "Книга: Граната", "chance": 0.15, "qty": [1, 1]},
      {"item": "Книга: Снайперский выстрел", "chance": 0.10, "qty": [1, 1]},
      {"item": "Электроника", "chance": 0.35, "qty": [1, 2]},
      {"item": "СВД", "chance": 0.10, "qty": [1, 1]},
      {"item": "РПГ", "chance": 0.02, "qty": [1, 1]}]),
    ("Patient Zero", 20, 800, 25, 15, 800, 500, "☣️", "aoe", 0.0,
     [{"item": "Вакцина", "chance": 1.0, "qty": [1, 1]},
      {"item": "Книга: Ярость", "chance": 0.50, "qty": [1, 1]},
      {"item": "Антибиотик", "chance": 1.0, "qty": [1, 2]},
      {"item": "Стимулятор", "chance": 1.0, "qty": [1, 2]},
      {"item": "Электроника", "chance": 0.8, "qty": [1, 2]}]),
]

SPAWNS = [
    ("Улица", "Walker", 3, 45),
    ("Аптека", "Walker", 2, 60),
    ("Супермаркет", "Walker", 2, 45),
    ("Супермаркет", "Runner", 2, 60),
    ("Заправка", "Runner", 3, 45),
    ("Больница", "Walker", 2, 45),
    ("Больница", "Runner", 2, 50),
    ("Больница", "Spitter", 1, 90),
    ("Морг", "Spitter", 2, 60),
    ("Морг", "Brute", 1, 120),
    ("Морг", "Patient Zero", 1, 600),
    ("Школа", "Runner", 3, 40),
    ("Школа", "Brute", 1, 150),
    ("Лесополоса", "Runner", 2, 45),
    ("Лесополоса", "Spitter", 2, 60),
    ("Военная база", "Brute", 2, 90),
    ("Военная база", "Tank", 1, 300),
    ("Радиовышка", "Spitter", 2, 60),
    ("Радиовышка", "Brute", 2, 90),
    ("Парк", "Walker", 3, 45),
    ("Парк", "Runner", 2, 50),
    ("Кинотеатр", "Runner", 2, 45),
    ("Кинотеатр", "Walker", 2, 55),
    ("Кинотеатр", "Crawler", 2, 40),
    ("Подвал кинотеатра", "Crawler", 3, 35),
    ("Подвал кинотеатра", "Brute", 1, 120),
    ("Метро", "Runner", 3, 40),
    ("Метро", "Spitter", 1, 70),
    ("Метро", "Crawler", 2, 45),
    ("Канализация", "Spitter", 2, 60),
    ("Канализация", "Brute", 2, 90),
    ("Канализация", "Crawler", 3, 40),
    ("Кладбище", "Walker", 3, 45),
    ("Кладбище", "Screamer", 2, 80),
    ("Кладбище", "Brute", 2, 90),
    ("Отель «Приют»", "Runner", 2, 45),
    ("Отель «Приют»", "Brute", 1, 100),
    ("Отель «Приют»", "Screamer", 1, 90),
    ("Крыша отеля", "Runner", 3, 40),
    ("Крыша отеля", "Spitter", 2, 60),
    ("Крыша отеля", "Screamer", 2, 80),
    ("Лаборатория", "Brute", 2, 90),
    ("Лаборатория", "Spitter", 2, 60),
    ("Лаборатория", "Tank", 1, 300),
    ("Аэропорт", "Brute", 3, 80),
    ("Аэропорт", "Tank", 1, 280),
    ("Аэропорт", "Screamer", 2, 70),
    ("Аэропорт", "Spitter", 2, 60),
]


def _free_cell(loc, taken):
    for _ in range(120):
        x = random.randint(1, max(1, loc.grid_w - 2))
        y = random.randint(1, max(1, loc.grid_h - 2))
        if (x, y) not in taken:
            return x, y
    # fallback: перебор всей сетки
    for y in range(1, loc.grid_h - 1):
        for x in range(1, loc.grid_w - 1):
            if (x, y) not in taken:
                return x, y
    return loc.grid_w // 2, loc.grid_h // 2


def seed_zombies(force=False):
    if ZombieType.query.count() > 0 and not force:
        print(f"Zombies: skipped ({ZombieType.query.count()} types exist)")
        return
    if force:
        Zombie.query.delete()
        Spawn.query.delete()
        ZombieType.query.delete()
        db.session.flush()

    items_by_name = {i.name: i.id for i in Item.query.all()}
    locs_by_name = {l.name: l for l in Location.query.all()}

    types_by_name = {}
    for name, lvl, hp, atk, df, xp, gold, icon, atk_type, stun, loot in ZOMBIES:
        loot_table = []
        for entry in loot:
            if entry["item"] in items_by_name:
                loot_table.append({
                    "item_id": items_by_name[entry["item"]],
                    "chance": entry["chance"],
                    "qty": entry["qty"],
                })
        zt = ZombieType(name=name, level=lvl, max_hp=hp, attack=atk, defense=df,
                        xp_reward=xp, gold_reward=gold, icon=icon,
                        attack_type=atk_type, stun_chance=stun,
                        loot_table=loot_table)
        db.session.add(zt)
        db.session.flush()
        types_by_name[name] = zt.id

    total = 0
    for loc_name, z_name, max_count, respawn in SPAWNS:
        if loc_name not in locs_by_name or z_name not in types_by_name:
            continue
        loc = locs_by_name[loc_name]
        zt_id = types_by_name[z_name]

        db.session.add(Spawn(location_id=loc.id, zombie_type_id=zt_id,
                             max_count=max_count, respawn_sec=respawn))

        zt = ZombieType.query.get(zt_id)
        existing = Zombie.query.filter_by(location_id=loc.id, state="alive").all()
        taken = {(z.x, z.y) for z in existing}

        # избегаем стен/зданий
        taken |= {(o.x, o.y) for o in Obstacle.query.filter_by(location_id=loc.id).all()}
        # избегаем выходов
        taken |= {(e.x, e.y) for e in loc.exits}

        for _ in range(max_count):
            x, y = _free_cell(loc, taken)
            taken.add((x, y))
            db.session.add(Zombie(
                type_id=zt_id, location_id=loc.id,
                hp=zt.max_hp, max_hp=zt.max_hp,
                x=x, y=y, state="alive",
            ))
            total += 1

    print(f"Zombies: seeded {len(ZOMBIES)} types, {len(SPAWNS)} spawn groups, {total} instances")