from app.extensions import db


def seed_all(force=False):
    from seeds.skills import seed_skills
    from seeds.items import seed_items
    from seeds.locations import seed_locations
    from seeds.obstacles import seed_obstacles
    from seeds.zombies import seed_zombies
    from seeds.npcs import seed_npcs
    from seeds.quests import seed_quests
    from seeds.loot import seed_loot
    from seeds.decorations import seed_decorations
    from seeds.craft import seed_craft
    from seeds.achievements import seed_achievements

    seed_skills(force=force);         db.session.flush()
    seed_items(force=force);          db.session.flush()
    seed_locations(force=force);      db.session.flush()
    seed_obstacles(force=force);      db.session.flush()
    seed_zombies(force=force);        db.session.flush()
    seed_npcs(force=force);           db.session.flush()
    seed_quests(force=force);         db.session.flush()
    seed_loot(force=force);           db.session.flush()
    seed_decorations(force=force);    db.session.flush()
    seed_craft(force=force);          db.session.flush()
    seed_achievements(force=force)
    db.session.commit()
    print("✅ Seed complete")