from app.models import Inventory


def get_stats(character):
    cache = getattr(character, "_stats_cache", None)
    if cache is not None:
        return cache

    bonus_attack = bonus_defense = bonus_hp = bonus_mp = bonus_evasion = 0
    equipped = character.inventory.filter(Inventory.equipped_slot.isnot(None)).all()
    for inv in equipped:
        if inv.item:
            bonus_attack += inv.item.attack or 0
            bonus_defense += inv.item.defense or 0
            bonus_hp += inv.item.hp_bonus or 0
            bonus_mp += inv.item.mp_bonus or 0
            bonus_evasion += inv.item.evasion or 0

    evasion = (character.base_evasion or 0) + bonus_evasion
    evasion = max(0, min(40, evasion))   # кап 40%

    result = {
        "max_hp": character.base_hp + bonus_hp,
        "max_mp": character.base_mp + bonus_mp,
        "attack": character.base_attack + bonus_attack,
        "defense": character.base_defense + bonus_defense,
        "speed": character.base_speed,
        "evasion": evasion,
    }
    character._stats_cache = result
    return result


def invalidate_stats(character):
    character._stats_cache = None