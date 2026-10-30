from app.extensions import db
from app.models import Achievement, CharacterAchievement
from app.services.loot import add_to_inventory


CONDITION_FIELDS = {
    "kills_total": "kills_total",
    "boss_kills": "boss_kills",
    "deaths": "deaths",
    "level": "level",
    "gold": "gold",
    "quests_done": "quests_done",
}


def check_achievements(character):
    """Проверяет и выдаёт новые достижения. Возвращает список dict-ов новых."""
    unlocked = {ca.achievement_id for ca in
                CharacterAchievement.query.filter_by(character_id=character.id).all()}

    new_unlocks = []
    for ach in Achievement.query.all():
        if ach.id in unlocked:
            continue
        if _is_satisfied(ach, character):
            db.session.add(CharacterAchievement(
                character_id=character.id, achievement_id=ach.id,
            ))
            if ach.reward_xp:
                character.add_xp(ach.reward_xp)
            if ach.reward_gold:
                character.gold += ach.reward_gold
            if ach.reward_item_id:
                add_to_inventory(character, ach.reward_item_id, 1)
            new_unlocks.append({
                "id": ach.id,
                "code": ach.code,
                "name": ach.name,
                "icon": ach.icon,
                "description": ach.description,
                "reward_xp": ach.reward_xp,
                "reward_gold": ach.reward_gold,
            })
    return new_unlocks


def _is_satisfied(ach, character):
    field = CONDITION_FIELDS.get(ach.condition_type)
    if not field:
        return False
    value = getattr(character, field, 0) or 0
    return value >= ach.condition_value