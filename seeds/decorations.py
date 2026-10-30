import random
from app.extensions import db
from app.models import Decoration, Location, Zombie, LootPoint, Obstacle


DECO_LAYOUT = {
    "Бункер выживших": [
        ("plant", 3, 0.7), ("chair", 2, 0.7), ("tv", 1, 0.7),
        ("brick", 4, 0.5), ("window", 2, 0.6), ("mailbox", 1, 0.7),
    ],
    "Улица": [
        ("old_car", 3, 0.85), ("street_lamp", 3, 0.9), ("trash", 5, 0.6),
        ("blood", 4, 0.4), ("papers", 4, 0.5), ("rock", 2, 0.6),
        ("tire", 2, 0.7), ("glass", 3, 0.5),
    ],
    "Аптека": [
        ("brick", 3, 0.5), ("blood", 3, 0.4), ("papers", 3, 0.5),
        ("glass", 3, 0.5), ("trash", 2, 0.5), ("sign", 2, 0.7),
        ("plant", 1, 0.7),
    ],
    "Супермаркет": [
        ("trash", 5, 0.6), ("papers", 4, 0.5), ("brick", 2, 0.5),
        ("glass", 3, 0.5), ("blood", 3, 0.4), ("sign", 2, 0.7),
        ("chair", 2, 0.6),
    ],
    "Заправка": [
        ("barrel", 3, 0.8), ("old_car", 2, 0.85), ("tire", 3, 0.7),
        ("blood", 2, 0.4), ("papers", 2, 0.5), ("trash", 3, 0.6),
        ("street_lamp", 2, 0.9),
    ],
    "Больница": [
        ("brick", 4, 0.5), ("blood", 6, 0.4), ("papers", 4, 0.5),
        ("glass", 3, 0.5), ("chair", 2, 0.6), ("sign", 3, 0.7),
        ("window", 2, 0.6), ("plant", 1, 0.6),
    ],
    "Морг": [
        ("blood", 7, 0.4), ("corpse", 4, 0.6), ("papers", 2, 0.4),
        ("brick", 2, 0.4), ("glass", 2, 0.5), ("chair", 1, 0.6),
    ],
    "Школа": [
        ("chair", 6, 0.6), ("brick", 3, 0.5), ("papers", 6, 0.5),
        ("graffiti", 3, 0.6), ("blood", 2, 0.4), ("window", 3, 0.6),
        ("trash", 2, 0.5),
    ],
    "Лесополоса": [
        ("tree", 10, 0.8), ("dead_tree", 3, 0.7), ("bush", 6, 0.6),
        ("rock", 4, 0.6), ("blood", 2, 0.4),
    ],
    "Военная база": [
        ("old_car", 3, 0.85), ("barrel", 4, 0.8), ("brick", 3, 0.5),
        ("sign", 2, 0.7), ("blood", 3, 0.4), ("papers", 2, 0.5),
        ("trash", 2, 0.6), ("flag", 1, 0.9),
    ],
    "Радиовышка": [
        ("rock", 4, 0.6), ("brick", 3, 0.5), ("old_car", 2, 0.85),
        ("papers", 3, 0.5), ("trash", 3, 0.6), ("blood", 2, 0.4),
        ("flag", 1, 0.9),
    ],
    "Парк": [
        ("tree", 8, 0.8), ("bush", 6, 0.6), ("bench", 3, 0.7),
        ("plant", 4, 0.7), ("trash", 3, 0.6), ("blood", 1, 0.4),
    ],
    "Кинотеатр": [
        ("chair", 6, 0.6), ("papers", 4, 0.5), ("glass", 3, 0.5),
        ("blood", 2, 0.4), ("sign", 2, 0.7), ("trash", 2, 0.5),
    ],
    "Подвал кинотеатра": [
        ("brick", 4, 0.5), ("papers", 3, 0.5), ("blood", 3, 0.4),
        ("barrel", 2, 0.7), ("corpse", 2, 0.5),
    ],
    "Метро": [
        ("brick", 5, 0.5), ("papers", 5, 0.5), ("trash", 4, 0.6),
        ("blood", 3, 0.4), ("chair", 3, 0.6), ("sign", 2, 0.7),
        ("barrel", 2, 0.7),
    ],
    "Канализация": [
        ("puddle", 8, 0.5), ("brick", 5, 0.5), ("trash", 4, 0.6),
        ("blood", 3, 0.4), ("barrel", 2, 0.7), ("corpse", 2, 0.5),
    ],
    "Кладбище": [
        ("corpse", 6, 0.6), ("dead_tree", 4, 0.7), ("blood", 4, 0.4),
        ("rock", 3, 0.6), ("bush", 3, 0.5),
    ],
    "Отель «Приют»": [
        ("chair", 4, 0.6), ("plant", 3, 0.7), ("papers", 3, 0.5),
        ("blood", 2, 0.4), ("window", 3, 0.6), ("brick", 2, 0.5),
        ("sign", 2, 0.7),
    ],
    "Крыша отеля": [
        ("puddle", 4, 0.5), ("rock", 3, 0.6), ("brick", 3, 0.5),
        ("barrel", 2, 0.7), ("flag", 1, 0.9), ("papers", 3, 0.5),
    ],
    "Лаборатория": [
        ("glass", 5, 0.5), ("papers", 5, 0.5), ("blood", 3, 0.4),
        ("plant", 2, 0.6), ("brick", 3, 0.5), ("sign", 2, 0.7),
        ("trash", 3, 0.5),
    ],
    "Аэропорт": [
        ("chair", 6, 0.6), ("trash", 5, 0.6), ("papers", 5, 0.5),
        ("glass", 4, 0.5), ("blood", 3, 0.4), ("sign", 3, 0.7),
        ("old_car", 2, 0.85),
    ],
}


def seed_decorations(force=False):
    if Decoration.query.count() > 0 and not force:
        print(f"Decorations: skipped ({Decoration.query.count()} exist)")
        return
    if force:
        Decoration.query.delete()
        db.session.flush()

    locs = {l.name: l for l in Location.query.all()}

    total = 0
    for loc_name, items in DECO_LAYOUT.items():
        if loc_name not in locs:
            continue
        loc = locs[loc_name]

        taken = {(z.x, z.y) for z in Zombie.query.filter_by(location_id=loc.id).all()}
        taken |= {(lp.x, lp.y) for lp in LootPoint.query.filter_by(location_id=loc.id).all()}
        taken |= {(e.x, e.y) for e in loc.exits}
        # избегаем стен/зданий
        taken |= {(o.x, o.y) for o in Obstacle.query.filter_by(location_id=loc.id).all()}

        for kind, count, alpha in items:
            placed = 0
            attempts = 0
            while placed < count and attempts < count * 30:
                attempts += 1
                x = random.randint(0, max(1, loc.grid_w - 1))
                y = random.randint(0, max(1, loc.grid_h - 1))
                if (x, y) in taken:
                    continue
                if (x, y) == (loc.grid_w // 2, loc.grid_h // 2):
                    continue
                taken.add((x, y))
                db.session.add(Decoration(
                    location_id=loc.id, x=x, y=y, kind=kind, alpha=alpha,
                ))
                placed += 1
                total += 1

    print(f"Decorations: seeded {total}")