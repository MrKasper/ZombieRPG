from app.extensions import db
from app.models import Quest, CharacterQuest, NPC, ZombieType, Item, Location


# (npc_name, name, desc, req_type, target, count, xp, gold, reward_item, requires_name)
QUESTS = [
    # === ОБЫЧНЫЕ ===
    ("Сержант Волков", "Зачистка улиц",
     "Улица кишит ходячими. Убери пятерых — и я поверю, что ты не бесполезен.",
     "kill", ("zombie", "Walker"), 5, 60, 30, None, None),
    ("Сержант Волков", "Бегуны на районе",
     "Разведка донесла: на заправке завелись бегуны. Десять штук — и путь чист.",
     "kill", ("zombie", "Runner"), 10, 120, 60, None, None),
    ("Сержант Волков", "Медикаменты",
     "В аптеке остались бинты. Принеси три штуки — заплачу и дам аптечку.",
     "collect", ("item", "Бинт"), 3, 80, 40, "Аптечка", None),
    ("Сержант Волков", "Разведка больницы",
     "Сходи в больницу. Просто дойди и вернись живым. Это важнее, чем кажется.",
     "visit", ("location", "Больница"), 1, 100, 50, None, None),
    ("Сержант Волков", "Металлолом",
     "Нам нужен металл. Принеси пять кусков — получишь топор.",
     "collect", ("item", "Металл"), 5, 150, 80, "Топор", None),
    ("Сержант Волков", "Тихая гавань",
     "Проверь радиовышку. Говорят, оттуда шёл сигнал. Или шёпот.",
     "visit", ("location", "Радиовышка"), 1, 200, 120, "Фонарик", None),
    ("Сержант Волков", "Чистка морга",
     "В морге три плевуна. Не хочу знать, что там происходит.",
     "kill", ("zombie", "Spitter"), 3, 250, 150, "Книга: Точный выстрел", None),
    ("Сержант Волков", "Крысиная охота",
     "Пятнадцать бегунов. Школа превратилась в их гнездо.",
     "kill", ("zombie", "Runner"), 15, 300, 180, "Кожаная куртка", None),
    ("Сержант Волков", "Химия",
     "Медик Анна просит химикатов. Три штуки — и она даст тебе стимулятор.",
     "collect", ("item", "Химикаты"), 3, 220, 100, "Стимулятор", None),
    ("Сержант Волков", "Убить Танка",
     "На военной базе — Танк. Один не справишься. Собери отряд.",
     "kill", ("zombie", "Tank"), 1, 500, 300, "Книга: Граната", None),
    ("Сержант Волков", "Громилы",
     "Три громилы. Тяжёлые, тупые, но опасные. На военной базе.",
     "kill", ("zombie", "Brute"), 3, 350, 200, "Мотокуртка", None),
    ("Сержант Волков", "Электроника",
     "Ремонт рации требует электроники. Принеси две штуки.",
     "collect", ("item", "Электроника"), 2, 400, 250, "Рация", None),
    ("Сержант Волков", "Школьные ужасы",
     "Дойди до школы. Не заходи в спортзал.",
     "visit", ("location", "Школа"), 1, 300, 180, "Книга: Очередь", None),
    ("Сержант Волков", "Полный комплект",
     "Мне нужны части: ткань, кожа, металл — по пять штук.",
     "collect", ("item", "Ткань"), 5, 200, 120, "Респиратор", None),
    ("Сержант Волков", "Великая охота",
     "Двадцать ходячих. Вернись — дам книгу ярости.",
     "kill", ("zombie", "Walker"), 20, 600, 400, "Книга: Ярость", None),

    # === СЮЖЕТНАЯ ЛИНИЯ ===
    ("Учёный Петров", "Странный слух",
     "Сержант говорил про записи в аптеке. Сходи туда, осмотрись.",
     "visit", ("location", "Аптека"), 1, 100, 30, None, None),
    ("Учёный Петров", "Бумаги",
     "В аптеке были записи о первых заражённых. Принеси три документа.",
     "collect", ("item", "Документы"), 3, 150, 50, None, "Странный слух"),
    ("Учёный Петров", "Пятна на стенах",
     "Записи указывают на больницу. Убей пять плевунов — это их гнездо.",
     "kill", ("zombie", "Spitter"), 5, 250, 100, None, "Бумаги"),
    ("Учёный Петров", "Журнал",
     "В больнице должен быть медицинский журнал. Найди его — там ключ.",
     "collect", ("item", "Медицинский журнал"), 1, 300, 120, None, "Пятна на стенах"),
    ("Учёный Петров", "Ключ-карта",
     "Журнал ведёт на военную базу. Найди ключ-карту в военном ящике.",
     "collect", ("item", "Ключ-карта"), 1, 400, 150, None, "Журнал"),
    ("Учёный Петров", "Пациент Ноль",
     "Он в морге. Тот, с кого всё началось. Убей его — и вакцина твоя.",
     "kill", ("zombie", "Patient Zero"), 1, 1000, 800,
     "Книга: Ярость", "Ключ-карта"),
]


def seed_quests(force=False):
    if Quest.query.count() > 0 and not force:
        print(f"Quests: skipped ({Quest.query.count()} exist)")
        return
    if force:
        CharacterQuest.query.delete()
        Quest.query.delete()
        db.session.flush()

    npcs = {n.name: n.id for n in NPC.query.all()}
    zombies = {z.name: z.id for z in ZombieType.query.all()}
    items = {i.name: i.id for i in Item.query.all()}
    locs = {l.name: l.id for l in Location.query.all()}

    created = {}
    for row in QUESTS:
        (npc_name, name, desc, req_type, target, count_req,
         xp, gold, reward_item, requires_name) = row
        if npc_name not in npcs:
            continue

        if req_type == "kill":
            _, zname = target
            if zname not in zombies:
                continue
            target_id = zombies[zname]
        elif req_type == "collect":
            _, iname = target
            if iname not in items:
                continue
            target_id = items[iname]
        elif req_type == "visit":
            _, lname = target
            if lname not in locs:
                continue
            target_id = locs[lname]
        else:
            continue

        q = Quest(
            npc_id=npcs[npc_name], name=name, description=desc,
            req_type=req_type, req_target=str(target_id), req_count=count_req,
            xp_reward=xp, gold_reward=gold,
            item_reward_id=items.get(reward_item) if reward_item else None,
        )
        db.session.add(q)
        db.session.flush()
        created[name] = q

    # связываем цепочку
    for row in QUESTS:
        requires_name = row[-1]
        q_name = row[1]
        if requires_name and q_name in created and requires_name in created:
            created[q_name].requires_quest_id = created[requires_name].id

    print(f"Quests: seeded {len(created)}")