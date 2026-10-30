from app.extensions import db
from app.models import Location, LocationExit

LOCATIONS = [
    # существующие
    ("Бункер выживших", "Здесь пахнет порохом и кофе. Выжившие торгуют, чинят снаряжение и делятся слухами.",
     True, 0, "#2a3a2a", 20, 15, "bunker"),
    ("Улица", "Разбитый асфальт, брошенные машины, тишина. Слишком тихо.",
     False, 1, "#3a3a3a", 26, 18, "street"),
    ("Аптека", "Полки перевёрнуты, но что-то ещё можно найти.",
     False, 1, "#3a2a3a", 18, 14, "pharmacy"),
    ("Супермаркет", "Холодильники давно не работают. И шорох в глубине зала.",
     False, 2, "#3a3a2a", 24, 18, "market"),
    ("Заправка", "Ржавые колонки, перевёрнутая цистерна. Хорошее место для засады.",
     False, 2, "#3a2a2a", 22, 16, "gas"),
    ("Больница", "Здесь начался ад. Коридоры в крови, пищит аппарат на резервном питании.",
     False, 3, "#2a2a3a", 26, 20, "hospital"),
    ("Морг", "Холодильники открыты. Некоторые тела… не лежат.",
     False, 5, "#1a1a2a", 18, 14, "morgue"),
    ("Школа", "Детские рисунки на стенах. И тени в классах.",
     False, 4, "#2a2a3a", 24, 20, "school"),
    ("Лесополоса", "Деревья скрывают многое. Здесь слышен хруст веток.",
     False, 3, "#1a2a1a", 28, 20, "forest"),
    ("Военная база", "Заброшенный блокпост. И что-то большое в ангаре.",
     False, 7, "#2a2a2a", 28, 22, "base"),
    ("Радиовышка", "Если забраться наверх — можно поймать сигнал. Но внизу кто-то ходит.",
     False, 6, "#2a1a2a", 22, 18, "tower"),

    # ========== 10 НОВЫХ ==========
    ("Парк", "Детская площадка поросла бурьяном. Качели скрипят без ветра.",
     False, 2, "#1a3a1a", 26, 20, "park"),
    ("Кинотеатр", "Афиши выцвели. В зале темно, экран потрескался. Кто-то ходит между рядами.",
     False, 3, "#2a1a2a", 22, 18, "cinema"),
    ("Подвал кинотеатра", "Сыро и темно. Пахнет плесенью и… чем-то живым.",
     False, 3, "#1a1a1a", 18, 14, "basement"),
    ("Метро", "Тоннели уходят в темноту. Эхо шагов возвращается не сразу.",
     False, 4, "#1a1a2a", 30, 22, "metro"),
    ("Канализация", "По колено в воде. Что-то плывёт навстречу.",
     False, 5, "#1a2a1a", 24, 18, "sewer"),
    ("Кладбище", "Могилы разрыты изнутри. Кто-то копал не снаружи.",
     False, 5, "#1a1a1a", 26, 22, "cemetery"),
    ("Отель «Приют»", "Роскошь давно выцвела. В коридорах — тишина и запах гнили.",
     False, 4, "#2a2a2a", 24, 20, "hotel"),
    ("Крыша отеля", "Ветер, антенны, разбитый бассейн. И тени на другой стороне.",
     False, 6, "#1a1a2a", 22, 18, "rooftop"),
    ("Лаборатория", "Стерильные коридоры. Ни одного тела. Только записи и… что-то живое.",
     False, 8, "#2a3a3a", 24, 20, "lab"),
    ("Аэропорт", "Огромный терминал. Пустые стойки, разбитые табло. И ОНИ.",
     False, 9, "#2a2a1a", 30, 24, "airport"),
]

EXITS = [
    # существующие
    ("Бункер выживших", "Улица", "north"),
    ("Улица", "Бункер выживших", "south"),
    ("Улица", "Больница", "north"),
    ("Больница", "Улица", "south"),
    ("Улица", "Супермаркет", "east"),
    ("Супермаркет", "Улица", "west"),
    ("Улица", "Аптека", "west"),
    ("Аптека", "Улица", "east"),
    ("Аптека", "Заправка", "west"),
    ("Заправка", "Аптека", "east"),
    ("Заправка", "Лесополоса", "west"),
    ("Лесополоса", "Заправка", "east"),
    ("Лесополоса", "Радиовышка", "north"),
    ("Радиовышка", "Лесополоса", "south"),
    ("Больница", "Морг", "east"),
    ("Морг", "Больница", "west"),
    ("Супермаркет", "Школа", "east"),
    ("Школа", "Супермаркет", "west"),
    ("Школа", "Военная база", "north"),
    ("Военная база", "Школа", "south"),

    # новые
    ("Лесополоса", "Парк", "west"),
    ("Парк", "Лесополоса", "east"),
    ("Супермаркет", "Кинотеатр", "north"),
    ("Кинотеатр", "Супермаркет", "south"),
    ("Кинотеатр", "Подвал кинотеатра", "north"),
    ("Подвал кинотеатра", "Кинотеатр", "south"),
    ("Заправка", "Отель «Приют»", "north"),
    ("Отель «Приют»", "Заправка", "south"),
    ("Отель «Приют»", "Крыша отеля", "north"),
    ("Крыша отеля", "Отель «Приют»", "south"),
    ("Лесополоса", "Кладбище", "south"),
    ("Кладбище", "Лесополоса", "north"),
    ("Больница", "Лаборатория", "north"),
    ("Лаборатория", "Больница", "south"),
    ("Больница", "Метро", "west"),
    ("Метро", "Больница", "east"),
    ("Метро", "Канализация", "west"),
    ("Канализация", "Метро", "east"),
    ("Военная база", "Аэропорт", "north"),
    ("Аэропорт", "Военная база", "south"),
]


def _exit_position(loc, direction):
    if direction == "north":
        return loc.grid_w // 2, 0
    if direction == "south":
        return loc.grid_w // 2, loc.grid_h - 1
    if direction == "east":
        return loc.grid_w - 1, loc.grid_h // 2
    if direction == "west":
        return 0, loc.grid_h // 2
    return loc.grid_w // 2, loc.grid_h // 2


def seed_locations(force=False):
    if Location.query.count() > 0 and not force:
        print(f"Locations: skipped ({Location.query.count()} exist)")
        return
    if force:
        LocationExit.query.delete()
        Location.query.delete()
        db.session.flush()

    by_name = {}
    for name, desc, safe, danger, color, gw, gh, tilemap in LOCATIONS:
        loc = Location(name=name, description=desc, is_safe_zone=safe,
                       danger_level=danger, bg_color=color,
                       grid_w=gw, grid_h=gh, tilemap_id=tilemap)
        db.session.add(loc)
        db.session.flush()
        by_name[name] = loc

    for frm, to, d in EXITS:
        frm_loc = by_name[frm]
        pos_x, pos_y = _exit_position(frm_loc, d)
        occupied = {(e.x, e.y) for e in frm_loc.exits}
        while (pos_x, pos_y) in occupied:
            if d in ("north", "south"):
                pos_x = (pos_x + 1) % frm_loc.grid_w
            else:
                pos_y = (pos_y + 1) % frm_loc.grid_h
        db.session.add(LocationExit(
            from_id=frm_loc.id, to_id=by_name[to].id,
            direction=d, x=pos_x, y=pos_y,
        ))

    print(f"Locations: seeded {len(LOCATIONS)} locations, {len(EXITS)} exits")