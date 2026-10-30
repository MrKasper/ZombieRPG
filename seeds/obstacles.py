from app.extensions import db
from app.models import Obstacle, Location


# (x, y, w, h, door_x, door_y, материал)
BUILDINGS = {
    "Улица": [
        (2, 3, 5, 4, 4, 6, "brick"),
        (15, 2, 5, 4, 17, 5, "wood"),
        (20, 10, 4, 5, 21, 14, "concrete"),
    ],
    "Заправка": [
        (3, 3, 4, 3, 5, 5, "metal"),
    ],
    "Лесополоса": [
        (10, 5, 4, 3, 12, 7, "wood"),
    ],
    "Военная база": [
        (4, 4, 6, 5, 7, 8, "concrete"),
        (18, 14, 5, 5, 20, 18, "concrete"),
    ],
    "Радиовышка": [
        (3, 3, 3, 3, 5, 5, "wood"),
    ],
    "Парк": [
        (10, 8, 4, 3, 12, 10, "wood"),
    ],
    "Кладбище": [
        (15, 5, 3, 3, 16, 7, "concrete"),
    ],
    "Крыша отеля": [
        (15, 3, 3, 2, 16, 4, "metal"),
    ],
    "Аэропорт": [
        (5, 5, 10, 6, 10, 10, "metal"),
        (20, 15, 3, 3, 21, 17, "metal"),
    ],
}

# одиночные объекты: (x, y, kind, variant)
EXTRA_OBSTACLES = {
    "Улица": [
        (10, 12, "barrel", ""), (11, 12, "barrel", ""),
        (12, 10, "car", ""),    (13, 10, "car", ""),
    ],
    "Заправка": [
        (15, 10, "barrel", ""), (16, 10, "barrel", ""),
        (15, 11, "barrel", ""), (16, 11, "barrel", ""),
    ],
    "Военная база": [
        (15, 5, "crate", ""), (16, 5, "crate", ""),
        (15, 8, "barrel", ""),
    ],
    "Аэропорт": [
        (15, 12, "car", ""), (16, 12, "car", ""),
        (15, 13, "car", ""),
    ],
}


def _rect_perimeter(x, y, w, h):
    cells = set()
    for i in range(w):
        cells.add((x + i, y))
        cells.add((x + i, y + h - 1))
    for j in range(h):
        cells.add((x, y + j))
        cells.add((x + w - 1, y + j))
    return cells


def seed_obstacles(force=False):
    if Obstacle.query.count() > 0 and not force:
        print(f"Obstacles: skipped ({Obstacle.query.count()} exist)")
        return
    if force:
        Obstacle.query.delete()
        db.session.flush()

    locs = {l.name: l for l in Location.query.all()}
    total = 0

    for loc_name, buildings in BUILDINGS.items():
        loc = locs.get(loc_name)
        if not loc:
            continue
        exit_cells = {(e.x, e.y) for e in loc.exits}
        for bx, by, bw, bh, dx, dy, mat in buildings:
            for cx, cy in _rect_perimeter(bx, by, bw, bh):
                if not (0 <= cx < loc.grid_w and 0 <= cy < loc.grid_h):
                    continue
                if (cx, cy) in exit_cells:
                    continue
                kind = "door" if (cx, cy) == (dx, dy) else "wall"
                db.session.add(Obstacle(
                    location_id=loc.id, x=cx, y=cy,
                    kind=kind, variant=mat,
                ))
                total += 1

    for loc_name, cells in EXTRA_OBSTACLES.items():
        loc = locs.get(loc_name)
        if not loc:
            continue
        for cx, cy, kind, variant in cells:
            if not (0 <= cx < loc.grid_w and 0 <= cy < loc.grid_h):
                continue
            db.session.add(Obstacle(
                location_id=loc.id, x=cx, y=cy,
                kind=kind, variant=variant,
            ))
            total += 1

    db.session.flush()
    print(f"Obstacles: seeded {total}")