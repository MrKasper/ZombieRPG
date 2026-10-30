import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "data", "game.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {"timeout": 5},
        "pool_pre_ping": True,
    }
    REMEMBER_COOKIE_DURATION = timedelta(days=30)

    # Игровые константы
    MAX_LEVEL = 50
    MAX_PARTY_SIZE = 4
    COMBAT_ACTION_COOLDOWN_SEC = 1.5      # пауза между ударами игрока
    ZOMBIE_ATTACK_INTERVAL_SEC = 2.0      # пауза между ударами зомби
    COMBAT_ABANDON_SEC = 60               # бой «брошен» через N сек без активности
    CHAT_HISTORY_LIMIT = 50
    STATE_POLL_INTERVAL_MS = 1500