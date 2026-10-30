import random
from app.extensions import db
from app.models import LootPoint, Location, Item, Zombie, Obstacle


KIND_TABLES = {
    "car": [
        {"item": "Бинт", "chance": 0.5, "qty": [1, 2]},
        {"item": "Энергетик", "chance": 0.4, "qty": [1, 1]},
        {"item": "Обезболивающее", "chance": 0.2, "qty": [1, 1]},
        {"item": "Пистолет", "chance": 0.05, "qty": [1, 1]},
        {"item": "Батарейка", "chance": 0.3, "qty": [1, 2]},
        {"item": "Фонарик", "chance": 0.1, "qty": [1, 1]},
        {"item": "Металл", "chance": 0.3, "qty": [1, 2]},
    ],
    "box": [
        {"item": "Бинт", "chance": 0.45, "qty": [1, 2]},
        {"item": "Аптечка", "chance": 0.15, "qty": [1, 1]},
        {"item": "Консервы", "chance": 0.3, "qty": [1, 2]},
        {"item": "Вода", "chance": 0.4, "qty": [1, 2]},
        {"item": "Ткань", "chance": 0.3, "qty": [1, 3]},
        {"item": "Книга: Точный выстрел", "chance": 0.05, "qty": [1, 1]},
    ],
    "shelf": [
        {"item": "Аптечка", "chance": 0.30, "qty": [1, 1]},
        {"item": "Обезболивающее", "chance": 0.35, "qty": [1, 1]},
        {"item": "Жгут", "chance": 0.25, "qty": [1, 1]},
        {"item": "Антибиотик", "chance": 0.1, "qty": [1, 1]},
        {"item": "Книга: Очередь", "chance": 0.08, "qty": [1, 1]},
        {"item": "Книга: Аптечка", "chance": 0.1, "qty": [1, 1]},
        {"item": "Документы", "chance": 0.35, "qty": [1, 2]},
    ],
    "corpse": [
        {"item": "Бинт", "chance": 0.30, "qty": [1, 1]},
        {"item": "Энергетик", "chance": 0.20, "qty": [1, 1]},
        {"item": "Кожа", "chance": 0.35, "qty": [1, 2]},
        {"item": "Ткань", "chance": 0.30, "qty": [1, 2]},
        {"item": "Кольцо удачи", "chance": 0.03, "qty": [1, 1]},
    ],
    "safe": [
        {"item": "Часы", "chance": 0.2, "qty": [1, 1]},
        {"item": "Пистолет", "chance": 0.35, "qty": [1, 1]},
        {"item": "Дробовик", "chance": 0.1, "qty": [1, 1]},
        {"item": "Книга: Адреналин", "chance": 0.15, "qty": [1, 1]},
        {"item": "Амулет", "chance": 0.05, "qty": [1, 1]},
        {"item": "Электроника", "chance": 0.3, "qty": [1, 1]},
        {"item": "Документы", "chance": 0.50, "qty": [1, 2]},
        {"item": "Ключ-карта", "chance": 0.15, "qty": [1, 1]},
    ],
    "military_crate": [
        {"item": "Шлем военный", "chance": 0.25, "qty": [1, 1]},
        {"item": "Армейские штаны", "chance": 0.25, "qty": [1, 1]},
        {"item": "Армейские ботинки", "chance": 0.25, "qty": [1, 1]},
        {"item": "Тактический жилет", "chance": 0.08, "qty": [1, 1]},
        {"item": "СВД", "chance": 0.05, "qty": [1, 1]},
        {"item": "Книга: Снайперский выстрел", "chance": 0.08, "qty": [1, 1]},
        {"item": "Стимулятор", "chance": 0.3, "qty": [1, 2]},
        {"item": "Металл", "chance": 0.4, "qty": [1, 3]},
        {"item": "Ключ-карта", "chance": 0.40, "qty": [1, 1]},
    ],
    "med_cabinet": [
        {"item": "Аптечка", "chance": 0.5, "qty": [1, 2]},
        {"item": "Жгут", "chance": 0.4, "qty": [1, 2]},
        {"item": "Антибиотик", "chance": 0.25, "qty": [1, 1]},
        {"item": "Стимулятор", "chance": 0.15, "qty": [1, 1]},
        {"item": "Антирад", "chance": 0.2, "qty": [1, 1]},
        {"item": "Химикаты", "chance": 0.2, "qty": [1, 2]},
        {"item": "Медицинский журнал", "chance": 0.30, "qty": [1, 1]},
    ],
    "fridge": [
        {"item": "Консервы", "chance": 0.6, "qty": [1, 2]},
        {"item": "Вода", "chance": 0.7, "qty": [1, 2]},
        {"item": "Шоколад", "chance": 0.35, "qty": [1, 1]},
        {"item": "Самогон", "chance": 0.15, "qty": [1, 1]},
        {"item": "Кофе", "chance": 0.2, "qty": [1, 1]},
    ],
    "locker": [
        {"item": "Футболка", "chance": 0.3, "qty": [1, 1]},
        {"item": "Рваные джинсы", "chance": 0.25, "qty": [1, 1]},
        {"item": "Кеды", "chance": 0.2, "qty": [1, 1]},
        {"item": "Ткань", "chance": 0.4, "qty": [1, 3]},
        {"item": "Кожа", "chance": 0.2, "qty": [1, 2]},
    ],
    "toolbox": [
        {"item": "Металл", "chance": 0.6, "qty": [1, 3]},
        {"item": "Дерево", "chance": 0.5, "qty": [1, 2]},
        {"item": "Труба", "chance": 0.15, "qty": [1, 1]},
        {"item": "Топор", "chance": 0.08, "qty": [1, 1]},
        {"item": "Стекло", "chance": 0.25, "qty": [1, 2]},
    ],
}


LOOT_LAYOUT = {
    "Улица":        [("car", 3), ("box", 2), ("locker", 1)],
    "Аптека":       [("shelf", 3), ("med_cabinet", 2), ("box", 1)],
    "Супермаркет":  [("shelf", 4), ("fridge", 3), ("box", 2), ("locker", 1)],
    "Заправка":     [("car", 2), ("box", 2), ("toolbox", 1)],
    "Больница":     [("med_cabinet", 3), ("shelf", 2), ("box", 2), ("locker", 1)],
    "Морг":         [("box", 2), ("corpse", 3), ("locker", 1)],
    "Школа":        [("shelf", 2), ("box", 3), ("locker", 2)],
    "Лесополоса":   [("box", 2), ("corpse", 2), ("toolbox", 1)],
    "Военная база": [("military_crate", 2), ("box", 2), ("safe", 1), ("toolbox", 1)],
    "Радиовышка":   [("box", 2), ("safe", 1), ("toolbox", 1)],
    "Парк":             [("box", 2), ("corpse", 2), ("toolbox", 1)],
    "Кинотеатр":        [("box", 2), ("locker", 1), ("shelf", 1)],
    "Подвал кинотеатра":[("box", 3), ("toolbox", 1), ("corpse", 1)],
    "Метро":            [("box", 2), ("locker", 2), ("safe", 1)],
    "Канализация":      [("box", 2), ("toolbox", 2), ("corpse", 2)],
    "Кладбище":         [("corpse", 3), ("box", 1), ("toolbox", 1)],
    "Отель «Приют»":    [("safe", 2), ("locker", 2), ("fridge", 1)],
    "Крыша отеля":      [("box", 2), ("toolbox", 1)],
    "Лаборатория":      [("med_cabinet", 3), ("safe", 2), ("toolbox", 1)],
    "Аэропорт":         [("military_crate", 3), ("safe", 2), ("locker", 2)],
}


def _build_loot_table(items, kind):
    table = []
    for e in KIND_TABLES.get(kind, []):
        if e["item"] in items:
            table.append({
                "item_id": items[e["item"]],
                "chance": e["chance"],
                "qty": e["qty"],
            })
    return table


def seed_loot(force=False):
    if LootPoint.query.count() > 0 and not force:
        print(f"LootPoints: skipped ({LootPoint.query.count()} exist)")
        return
    if force:
        LootPoint.query.delete()
        db.session.flush()

    items = {i.name: i.id for i in Item.query.all()}
    locs = {l.name: l for l in Location.query.all()}

    total = 0
    for loc_name, specs in LOOT_LAYOUT.items():
        if loc_name not in locs:
            continue
        loc = locs[loc_name]

        taken = {(z.x, z.y) for z in Zombie.query.filter_by(location_id=loc.id).all()}
        taken |= {(e.x, e.y) for e in loc.exits}
        # избегаем стен/зданий
        taken |= {(o.x, o.y) for o in Obstacle.query.filter_by(location_id=loc.id).all()}

        for kind, count in specs:
            table = _build_loot_table(items, kind)
            if not table:
                continue
            for _ in range(count):
                x, y = loc.grid_w // 2, loc.grid_h // 2
                placed = False
                for _ in range(120):
                    nx = random.randint(1, max(1, loc.grid_w - 2))
                    ny = random.randint(1, max(1, loc.grid_h - 2))
                    if (nx, ny) not in taken:
                        x, y = nx, ny
                        placed = True
                        break
                if not placed:
                    # fallback — перебор
                    for ny in range(1, loc.grid_h - 1):
                        for nx in range(1, loc.grid_w - 1):
                            if (nx, ny) not in taken:
                                x, y = nx, ny
                                placed = True
                                break
                        if placed:
                            break
                if not placed:
                    continue
                taken.add((x, y))
                db.session.add(LootPoint(
                    location_id=loc.id, x=x, y=y, kind=kind,
                    loot_table=table, state="available",
                ))
                total += 1

    print(f"LootPoints: seeded {total}")