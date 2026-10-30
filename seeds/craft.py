from app.extensions import db
from app.models import Recipe, Item


# (result_name, result_qty, [(ingredient_name, qty)], gold_cost)
RECIPES = [
    # ===== БАЗОВЫЕ =====
    ("Бинт", 2, [("Ткань", 1)], 0),
    ("Жгут", 1, [("Ткань", 2), ("Химикаты", 1)], 3),
    ("Обезболивающее", 1, [("Химикаты", 1), ("Ткань", 1)], 5),
    ("Аптечка", 1, [("Бинт", 2), ("Химикаты", 2)], 8),
    ("Антирад", 1, [("Химикаты", 2), ("Стекло", 1)], 15),
    ("Стимулятор", 1, [("Химикаты", 3), ("Стекло", 2)], 20),
    ("Антибиотик", 1, [("Химикаты", 4), ("Ткань", 2)], 30),
    ("Энергетик", 2, [("Химикаты", 1), ("Стекло", 1)], 5),
    ("Шоколад", 1, [("Химикаты", 1), ("Ткань", 1)], 3),

    # ===== ОРУЖИЕ =====
    ("Труба", 1, [("Металл", 2), ("Дерево", 1)], 5),
    ("Топор", 1, [("Металл", 3), ("Дерево", 2)], 15),
    ("Копьё", 1, [("Металл", 2), ("Дерево", 3)], 18),
    ("Мачете", 1, [("Металл", 4), ("Кожа", 1)], 25),
    ("Пистолет", 1, [("Металл", 6), ("Электроника", 2)], 60),
    ("Дробовик", 1, [("Металл", 10), ("Электроника", 3), ("Дерево", 2)], 120),
    ("Арбалет", 1, [("Дерево", 8), ("Металл", 4), ("Кожа", 2)], 90),

    # ===== БРОНЯ =====
    ("Кожаная куртка", 1, [("Кожа", 4), ("Ткань", 2)], 30),
    ("Рабочий комбинезон", 1, [("Ткань", 6)], 15),
    ("Мотокуртка", 1, [("Кожа", 6), ("Металл", 2)], 60),
    ("Бронежилет", 1, [("Металл", 8), ("Кожа", 4), ("Ткань", 3)], 180),
    ("Каска", 1, [("Металл", 3), ("Кожа", 1)], 25),
    ("Противогаз", 1, [("Металл", 2), ("Стекло", 2), ("Химикаты", 1)], 40),

    # ===== ИНСТРУМЕНТЫ =====
    ("Фонарик", 1, [("Металл", 2), ("Стекло", 2), ("Батарейка", 1)], 25),
    ("Рация", 1, [("Металл", 4), ("Электроника", 3), ("Батарейка", 2)], 80),
    ("Бинокль", 1, [("Стекло", 3), ("Металл", 2), ("Кожа", 1)], 50),
]


def seed_craft(force=False):
    if Recipe.query.count() > 0 and not force:
        print(f"Recipes: skipped ({Recipe.query.count()} exist)")
        return
    if force:
        Recipe.query.delete()
        db.session.flush()

    items_by_name = {i.name: i.id for i in Item.query.all()}

    count = 0
    for result_name, result_qty, ings, gold in RECIPES:
        if result_name not in items_by_name:
            continue
        ingredient_list = []
        skip = False
        for ing_name, qty in ings:
            if ing_name not in items_by_name:
                skip = True
                break
            ingredient_list.append({
                "item_id": items_by_name[ing_name],
                "qty": qty,
            })
        if skip:
            continue

        db.session.add(Recipe(
            result_item_id=items_by_name[result_name],
            result_qty=result_qty,
            ingredients=ingredient_list,
            gold_cost=gold,
        ))
        count += 1

    print(f"Recipes: seeded {count}")