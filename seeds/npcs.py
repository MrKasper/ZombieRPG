from app.extensions import db
from app.models import NPC, Location, ShopStock, Item


NPCS = [
    # (loc_name, name, role, icon, faction, dialogue)
    ("Бункер выживших", "Торговец Кузнец", "merchant", "🧔", "neutral",
     "Оружие, броня, расходники. Всё по-честному."),
    ("Бункер выживших", "Медик Анна", "merchant", "👩‍⚕️", "neutral",
     "Раны, ожоги, укусы? У меня есть всё."),
    ("Бункер выживших", "Мастерская", "crafter", "🛠️", "neutral",
     "Приноси материалы — сделаю что хочешь."),
    ("Бункер выживших", "Учёный Петров", "quest_giver", "👨‍🔬", "scientists",
     "Все ответы — в записях. Только не спрашивай, что было в морге."),
    ("Бункер выживших", "Сержант Волков", "quest_giver", "🎖️", "military",
     "Есть работёнка. Если выживешь — заплачу."),
]

STOCK = {
    "Торговец Кузнец": [
        ("Ржавый нож", 8), ("Труба", 15), ("Бейсбольная бита", 25),
        ("Топор", 65), ("Мачете", 70), ("Пистолет", 180), ("Дробовик", 450),
        ("Футболка", 8), ("Рваная куртка", 15), ("Рабочий комбинезон", 40),
        ("Кожаная куртка", 80), ("Кепка", 8), ("Респиратор", 30), ("Каска", 60),
        ("Рваные джинсы", 8), ("Брюки карго", 45), ("Кеды", 8), ("Берцы", 60),
        ("Ткань", 5), ("Металл", 15), ("Дерево", 6), ("Кожа", 8),
        ("Стекло", 5), ("Батарейка", 10), ("Фонарик", 60),
    ],
    "Медик Анна": [
        ("Бинт", 8), ("Аптечка", 25), ("Жгут", 18), ("Энергетик", 20),
        ("Обезболивающее", 30), ("Антибиотик", 70), ("Антирад", 45),
        ("Консервы", 10), ("Вода", 8), ("Шоколад", 15), ("Кофе", 18),
        ("Самогон", 25), ("Книга: Аптечка", 90), ("Книга: Адреналин", 220),
    ],
}


def seed_npcs(force=False):
    if NPC.query.count() > 0 and not force:
        print(f"NPCs: skipped ({NPC.query.count()} exist)")
        return
    if force:
        ShopStock.query.delete()
        NPC.query.delete()
        db.session.flush()

    locs = {l.name: l.id for l in Location.query.all()}
    items = {i.name: i.id for i in Item.query.all()}

    npc_by_name = {}
    for loc_name, name, role, icon, faction, dialogue in NPCS:
        if loc_name not in locs:
            continue
        npc = NPC(location_id=locs[loc_name], name=name, role=role,
                  icon=icon, faction=faction, dialogue=dialogue)
        db.session.add(npc)
        db.session.flush()
        npc_by_name[name] = npc.id

    count_stock = 0
    for npc_name, entries in STOCK.items():
        if npc_name not in npc_by_name:
            continue
        for item_name, price in entries:
            if item_name not in items:
                continue
            db.session.add(ShopStock(
                npc_id=npc_by_name[npc_name],
                item_id=items[item_name],
                price=price, stock=-1,
            ))
            count_stock += 1

    db.session.flush()
    print(f"NPCs: seeded {len(NPCS)} npcs, {count_stock} shop items")