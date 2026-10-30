from app.extensions import db
from app.models import Item, Skill


# (name, type, slot, rarity, atk, def, hp_b, mp_b, evasion, heal_hp, heal_mp,
#  icon, price, stack, desc, learn_skill_name)
ITEMS = [
    # ============ ОРУЖИЕ ============
    ("Ржавый нож", "weapon", "weapon", "common", 2, 0, 0, 0, 0, 0, 0,
     "🔪", 5, False, "Сойдёт против одного зомби.", None),
    ("Труба", "weapon", "weapon", "common", 3, 0, 0, 0, 0, 0, 0,
     "🔧", 12, False, "Тяжёлая, но рабочая.", None),
    ("Кастет", "weapon", "weapon", "common", 3, 0, 0, 0, 0, 0, 0,
     "🥊", 15, False, "Быстро и близко.", None),
    ("Бейсбольная бита", "weapon", "weapon", "common", 4, 0, 0, 0, 0, 0, 0,
     "🪵", 20, False, "Классика жанра.", None),
    ("Топор", "weapon", "weapon", "uncommon", 6, 0, 0, 0, 0, 0, 0,
     "🪓", 55, False, "И дрова, и зомби.", None),
    ("Мачете", "weapon", "weapon", "uncommon", 7, 0, 0, 0, 0, 0, 0,
     "🗡️", 60, False, "Оставляет глубокие раны.", None),
    ("Копьё", "weapon", "weapon", "uncommon", 9, 0, 0, 0, 0, 0, 0,
     "🔱", 90, False, "Держи зомби на расстоянии.", None),
    ("Пистолет", "weapon", "weapon", "uncommon", 10, 0, 0, 0, 0, 0, 0,
     "🔫", 150, False, "Надёжный 9мм.", None),
    ("Арбалет", "weapon", "weapon", "rare", 12, 0, 0, 0, 0, 0, 0,
     "🏹", 280, False, "Тихий и точный.", None),
    ("Катана", "weapon", "weapon", "rare", 14, 0, 0, 0, 0, 0, 0,
     "⚔️", 380, False, "Глубокий порез.", None),
    ("Дробовик", "weapon", "weapon", "rare", 15, 0, 0, 0, 0, 0, 0,
     "💥", 400, False, "Разносит всё вблизи.", None),
    ("СВД", "weapon", "weapon", "epic", 18, 0, 0, 0, 0, 0, 0,
     "🎯", 900, False, "Издалека и наверняка.", None),
    ("Автомат", "weapon", "weapon", "epic", 22, 0, 0, 0, 0, 0, 0,
     "🎖️", 1200, False, "Трофей с военной базы.", None),
    ("РПГ", "weapon", "weapon", "legendary", 35, 0, 0, 0, 0, 0, 0,
     "🚀", 3000, False, "Один выстрел — один квартал.", None),

    # ============ БРОНЯ: BODY ============
    ("Футболка", "armor", "body", "common", 0, 1, 0, 0, 0, 0, 0,
     "👕", 5, False, "Лучше, чем ничего.", None),
    ("Рваная куртка", "armor", "body", "common", 0, 2, 0, 0, 1, 0, 0,
     "🧥", 10, False, "Хоть что-то.", None),
    ("Рабочий комбинезон", "armor", "body", "common", 0, 3, 5, 0, 1, 0, 0,
     "🥼", 30, False, "Плотная ткань.", None),
    ("Кожаная куртка", "armor", "body", "uncommon", 0, 5, 5, 0, 2, 0, 0,
     "🧥", 70, False, "Плотная кожа.", None),
    ("Мотокуртка", "armor", "body", "uncommon", 0, 7, 0, 0, 3, 0, 0,
     "🏍️", 120, False, "Спасёт от асфальта.", None),
    ("Бронежилет", "armor", "body", "rare", 0, 12, 10, 0, -2, 0, 0,
     "🦺", 350, False, "Военный трофей. Тяжёлый.", None),
    ("Тактический жилет", "armor", "body", "epic", 0, 18, 15, 5, 0, 0, 0,
     "🎽", 900, False, "Максимум защиты.", None),

    # ============ БРОНЯ: ГОЛОВА ============
    ("Кепка", "armor", "head", "common", 0, 1, 0, 0, 2, 0, 0,
     "🧢", 5, False, "Почти ничего.", None),
    ("Респиратор", "armor", "head", "common", 0, 2, 3, 0, 1, 0, 0,
     "😷", 25, False, "Пыль не пройдёт.", None),
    ("Каска", "armor", "head", "uncommon", 0, 4, 0, 0, 3, 0, 0,
     "⛑️", 50, False, "Строительная.", None),
    ("Противогаз", "armor", "head", "uncommon", 0, 5, 5, 0, 4, 0, 0,
     "🥽", 80, False, "Защита от дыма.", None),
    ("Шлем мотоциклиста", "armor", "head", "rare", 0, 6, 8, 0, 6, 0, 0,
     "🏍️", 180, False, "Крепкий.", None),
    ("Шлем военный", "armor", "head", "rare", 0, 8, 5, 0, 5, 0, 0,
     "🪖", 250, False, "Военный.", None),

    # ============ БРОНЯ: НОГИ ============
    ("Рваные джинсы", "armor", "legs", "common", 0, 1, 0, 0, 0, 0, 0,
     "👖", 5, False, "Дырявые.", None),
    ("Брюки карго", "armor", "legs", "uncommon", 0, 3, 0, 0, 1, 0, 0,
     "👖", 40, False, "Много карманов.", None),
    ("Армейские штаны", "armor", "legs", "rare", 0, 6, 5, 0, 1, 0, 0,
     "🩳", 150, False, "Прочные.", None),

    # ============ БРОНЯ: ОБУВЬ ============
    ("Кеды", "armor", "feet", "common", 0, 1, 0, 0, 4, 0, 0,
     "👟", 5, False, "Удобно бегать от зомби.", None),
    ("Берцы", "armor", "feet", "uncommon", 0, 3, 0, 0, 3, 0, 0,
     "🥾", 50, False, "Тяжёлые, но прочные.", None),
    ("Армейские ботинки", "armor", "feet", "rare", 0, 4, 3, 0, 5, 0, 0,
     "🥾", 130, False, "На любой грунт.", None),

    # ============ АКСЕССУАРЫ ============
    ("Кольцо удачи", "accessory", "accessory_1", "uncommon", 1, 1, 0, 0, 3, 0, 0,
     "💍", 200, False, "Капля везения.", None),
    ("Часы", "accessory", "accessory_1", "rare", 0, 0, 10, 0, 0, 0, 0,
     "⌚", 250, False, "Время — ресурс.", None),
    ("Амулет", "accessory", "accessory_1", "epic", 2, 2, 15, 5, 5, 0, 0,
     "🔮", 700, False, "Тёплый на ощупь.", None),

    # ============ РАСХОДНИКИ ============
    ("Бинт", "consumable", None, "common", 0, 0, 0, 0, 0, 15, 0,
     "🩹", 5, True, "Восстанавливает 15 HP.", None),
    ("Аптечка", "consumable", None, "uncommon", 0, 0, 0, 0, 0, 40, 0,
     "💊", 20, True, "Восстанавливает 40 HP.", None),
    ("Жгут", "consumable", None, "uncommon", 0, 0, 0, 0, 0, 25, 0,
     "🩸", 15, True, "Останавливает кровь.", None),
    ("Энергетик", "consumable", None, "common", 0, 0, 0, 0, 0, 0, 30,
     "⚡", 15, True, "Восстанавливает 30 MP.", None),
    ("Обезболивающее", "consumable", None, "uncommon", 0, 0, 0, 0, 0, 25, 10,
     "💊", 25, True, "+25 HP, +10 MP.", None),
    ("Стимулятор", "consumable", None, "rare", 0, 0, 0, 0, 0, 60, 40,
     "💉", 80, True, "Мощный коктейль.", None),
    ("Антирад", "consumable", None, "uncommon", 0, 0, 0, 0, 0, 20, 20,
     "☢️", 40, True, "Спасение от радиации.", None),
    ("Антибиотик", "consumable", None, "rare", 0, 0, 0, 0, 0, 50, 0,
     "💊", 60, True, "Лечит всё.", None),
    ("Консервы", "consumable", None, "common", 0, 0, 0, 0, 0, 10, 0,
     "🥫", 8, True, "Сытно.", None),
    ("Вода", "consumable", None, "common", 0, 0, 0, 0, 0, 5, 15,
     "💧", 6, True, "Утоляет жажду.", None),
    ("Шоколад", "consumable", None, "common", 0, 0, 0, 0, 0, 8, 5,
     "🍫", 12, True, "Психическое здоровье тоже важно.", None),
    ("Кофе", "consumable", None, "uncommon", 0, 0, 0, 0, 0, 0, 25,
     "☕", 15, True, "Бодрит.", None),
    ("Самогон", "consumable", None, "uncommon", 0, 0, 0, 0, 0, 20, 0,
     "🍺", 20, True, "Смелость на время.", None),

    # ============ МАТЕРИАЛЫ ============
    ("Ткань", "material", None, "common", 0, 0, 0, 0, 0, 0, 0,
     "🧵", 3, True, "Материал для крафта.", None),
    ("Кожа", "material", None, "common", 0, 0, 0, 0, 0, 0, 0,
     "🟫", 5, True, "Материал для крафта.", None),
    ("Дерево", "material", None, "common", 0, 0, 0, 0, 0, 0, 0,
     "🪵", 4, True, "Материал для крафта.", None),
    ("Металл", "material", None, "uncommon", 0, 0, 0, 0, 0, 0, 0,
     "⚙️", 10, True, "Материал для крафта.", None),
    ("Стекло", "material", None, "common", 0, 0, 0, 0, 0, 0, 0,
     "🔷", 3, True, "Материал для крафта.", None),
    ("Электроника", "material", None, "rare", 0, 0, 0, 0, 0, 0, 0,
     "🔌", 25, True, "Материал для крафта.", None),
    ("Химикаты", "material", None, "rare", 0, 0, 0, 0, 0, 0, 0,
     "🧪", 20, True, "Материал для крафта.", None),

    # ============ ОСОБЫЕ ============
    ("Фонарик", "material", None, "uncommon", 0, 0, 0, 0, 0, 0, 0,
     "🔦", 50, False, "Для тёмных локаций.", None),
    ("Батарейка", "material", None, "common", 0, 0, 0, 0, 0, 0, 0,
     "🔋", 8, True, "Питание.", None),
    ("Рация", "material", None, "rare", 0, 0, 0, 0, 0, 0, 0,
     "📻", 100, False, "Связь на расстоянии.", None),
    ("Бинокль", "material", None, "rare", 0, 0, 0, 0, 0, 0, 0,
     "🔭", 90, False, "Видеть далеко.", None),

    # ============ СЮЖЕТНЫЕ ПРЕДМЕТЫ ============
    ("Документы", "material", None, "uncommon", 0, 0, 0, 0, 0, 0, 0,
     "📃", 30, True, "Записи о первых заражённых.", None),
    ("Медицинский журнал", "material", None, "rare", 0, 0, 0, 0, 0, 0, 0,
     "📔", 80, True, "Журнал наблюдений. Важен для учёного.", None),
    ("Ключ-карта", "material", None, "rare", 0, 0, 0, 0, 0, 0, 0,
     "🗝️", 100, True, "Открывает доступ к лаборатории.", None),
    ("Вакцина", "accessory", "accessory_1", "legendary", 25, 25, 100, 50, 10, 0, 0,
     "💉", 8000, False,
     "Сыворотка, созданная до катастрофы. Даёт невероятную силу.", None),

    # ============ КНИГИ СКИЛЛОВ ============
    ("Книга: Точный выстрел", "book", None, "uncommon", 0, 0, 0, 0, 0, 0, 0,
     "📕", 60, False, "Учит скиллу «Точный выстрел».", "Точный выстрел"),
    ("Книга: Очередь", "book", None, "rare", 0, 0, 0, 0, 0, 0, 0,
     "📗", 150, False, "Учит скиллу «Очередь».", "Очередь"),
    ("Книга: Граната", "book", None, "epic", 0, 0, 0, 0, 0, 0, 0,
     "📘", 400, False, "Учит скиллу «Граната».", "Граната"),
    ("Книга: Аптечка", "book", None, "uncommon", 0, 0, 0, 0, 0, 0, 0,
     "📙", 80, False, "Учит скиллу «Аптечка».", "Аптечка"),
    ("Книга: Адреналин", "book", None, "rare", 0, 0, 0, 0, 0, 0, 0,
     "📔", 200, False, "Учит скиллу «Адреналин».", "Адреналин"),
    ("Книга: Снайперский выстрел", "book", None, "epic", 0, 0, 0, 0, 0, 0, 0,
     "📓", 550, False, "Учит скиллу «Снайперский выстрел».", "Снайперский выстрел"),
    ("Книга: Ярость", "book", None, "legendary", 0, 0, 0, 0, 0, 0, 0,
     "📒", 1200, False, "Учит скиллу «Ярость».", "Ярость"),
]


def seed_items(force=False):
    if Item.query.count() > 0 and not force:
        print(f"Items: skipped ({Item.query.count()} exist)")
        return
    if force:
        Item.query.delete()
        db.session.flush()

    skills_by_name = {s.name: s.id for s in Skill.query.all()}

    for (name, typ, slot, rarity, atk, df, hpb, mpb, eva, hhp, hmp,
         icon, price, stack, desc, skill_name) in ITEMS:
        db.session.add(Item(
            name=name, type=typ, slot=slot, rarity=rarity,
            attack=atk, defense=df, hp_bonus=hpb, mp_bonus=mpb,
            evasion=eva, heal_hp=hhp, heal_mp=hmp,
            icon=icon, base_price=price,
            stackable=stack, description=desc,
            learn_skill_id=skills_by_name.get(skill_name) if skill_name else None,
        ))
    db.session.flush()
    print(f"Items: seeded {len(ITEMS)}")