from app.extensions import db
from app.models import CharacterQuest, Quest


def progress_quests(character, req_type, target, amount=1):
    """Двигает все активные квесты игрока, подходящие под событие."""
    rows = (CharacterQuest.query
            .join(Quest, Quest.id == CharacterQuest.quest_id)
            .filter(CharacterQuest.character_id == character.id,
                    CharacterQuest.status == "active",
                    Quest.req_type == req_type,
                    Quest.req_target == str(target))
            .all())
    for cq in rows:
        if not cq.quest:
            continue
        cq.progress = min(cq.quest.req_count, cq.progress + amount)
    return rows


def is_complete(cq):
    if not cq or not cq.quest:
        return False
    return cq.progress >= cq.quest.req_count


def grant_rewards(character, quest):
    from app.services.loot import add_to_inventory
    if not quest:
        return
    character.add_xp(quest.xp_reward)
    character.gold += quest.gold_reward
    if quest.item_reward_id:
        add_to_inventory(character, quest.item_reward_id, 1)