from app.extensions import db
from app.models import Achievement, CharacterAchievement, Item


# (code, name, description, icon, cond_type, cond_value, xp, gold, reward_item)
ACHIEVEMENTS = [
    # базовые
    ("first_kill", "Первая кровь", "Убей первого зомби",
     "🩸", "kills_total", 1, 20, 10, None),
    ("killer_10", "Охотник", "Убей 10 зомби",
     "🎯", "kills_total", 10, 80, 40, None),
    ("killer_50", "Истребитель", "Убей 50 зомби",
     "💀", "kills_total", 50, 300, 150, "Аптечка"),
    ("killer_100", "Легенда улиц", "Убей 100 зомби",
     "🔥", "kills_total", 100, 800, 400, "Книга: Очередь"),
    ("killer_250", "Кошмар зомби", "Убей 250 зомби",
     "☠️", "kills_total", 250, 2000, 1000, "Книга: Ярость"),

    # боссы
    ("boss_first", "Убийца Танка", "Победи Танка",
     "🦍", "boss_kills", 1, 500, 300, None),
    ("boss_three", "Гроза боссов", "Убей трёх Танков",
     "🏆", "boss_kills", 3, 1500, 800, "Шлем военный"),
    ("boss_ten", "Кровь Титанов", "Убей десять Танков",
     "👑", "boss_kills", 10, 5000, 3000, "Амулет"),

    # уровни
    ("level_5", "Опытный", "Достигни 5 уровня",
     "⭐", "level", 5, 50, 30, None),
    ("level_10", "Ветеран", "Достигни 10 уровня",
     "🌟", "level", 10, 200, 100, None),
    ("level_20", "Мастер", "Достигни 20 уровня",
     "✨", "level", 20, 800, 500, None),
    ("level_30", "Элита", "Достигни 30 уровня",
     "💫", "level", 30, 2000, 1500, "Бронежилет"),
    ("level_40", "Легенда", "Достигни 40 уровня",
     "⚡", "level", 40, 5000, 3000, "Тактический жилет"),
    ("level_50", "Титан апокалипсиса", "Достигни 50 уровня",
     "🌠", "level", 50, 15000, 10000, "РПГ"),

    # богатство
    ("rich_100", "Богач", "Накопи 100 золота",
     "💰", "gold", 100, 50, 0, None),
    ("rich_1000", "Скрудж", "Накопи 1000 золота",
     "💎", "gold", 1000, 300, 0, None),
    ("rich_5000", "Магнат", "Накопи 5000 золота",
     "👑", "gold", 5000, 1500, 0, "Амулет"),

    # квесты
    ("quest_1", "Первый заказ", "Сдай первый квест",
     "📜", "quests_done", 1, 30, 20, None),
    ("quest_5", "Квест-мастер", "Сдай 5 квестов",
     "📋", "quests_done", 5, 200, 100, None),
    ("quest_15", "Легенда квестов", "Сдай 15 квестов",
     "🗞️", "quests_done", 15, 1000, 500, "Книга: Граната"),

    # смерти
    ("die_1", "Первый раз", "Умри впервые",
     "☠️", "deaths", 1, 0, 5, None),
    ("die_10", "Живучий мертвец", "Умри 10 раз",
     "💀", "deaths", 10, 100, 50, "Антибиотик"),
]


def seed_achievements(force=False):
    if Achievement.query.count() > 0 and not force:
        print(f"Achievements: skipped ({Achievement.query.count()} exist)")
        return
    if force:
        CharacterAchievement.query.delete()
        Achievement.query.delete()
        db.session.flush()

    items = {i.name: i.id for i in Item.query.all()}

    for code, name, desc, icon, cond_type, cond_val, xp, gold, reward_item in ACHIEVEMENTS:
        db.session.add(Achievement(
            code=code, name=name, description=desc, icon=icon,
            condition_type=cond_type, condition_value=cond_val,
            reward_xp=xp, reward_gold=gold,
            reward_item_id=items.get(reward_item) if reward_item else None,
        ))

    print(f"Achievements: seeded {len(ACHIEVEMENTS)}")