import random
from app.models import Zombie, Character, Obstacle


def cell_blocked(loc, nx, ny, exclude_char_id=None):
    # 1) стены/объекты
    obs = Obstacle.query.filter_by(location_id=loc.id, x=nx, y=ny).first()
    if obs and obs.is_blocking():
        return True

    # 2) зомби
    z = Zombie.query.filter_by(
        location_id=loc.id, state="alive", x=nx, y=ny
    ).first()
    if z:
        return True

    # 3) игроки
    q = Character.query.filter_by(location_id=loc.id, x=nx, y=ny)
    if exclude_char_id is not None:
        q = q.filter(Character.id != exclude_char_id)
    if q.first():
        return True
    return False


def find_free_cell(loc, exclude_char_id=None, prefer_center=False):
    candidates = []
    if prefer_center:
        candidates.append((loc.grid_w // 2, loc.grid_h // 2))
    for _ in range(100):
        candidates.append((
            random.randint(1, max(1, loc.grid_w - 2)),
            random.randint(1, max(1, loc.grid_h - 2)),
        ))
    for x, y in candidates:
        if not cell_blocked(loc, x, y, exclude_char_id):
            return x, y
    # надёжный fallback — перебираем всё поле
    for y in range(1, loc.grid_h - 1):
        for x in range(1, loc.grid_w - 1):
            if not cell_blocked(loc, x, y, exclude_char_id):
                return x, y
    return 1, 1