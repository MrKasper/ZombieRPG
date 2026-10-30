import os
import sys
from flask import Flask, render_template, jsonify
from app.extensions import db, login_manager, migrate
from config import Config

IS_FROZEN = getattr(sys, "frozen", False)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    uri = app.config["SQLALCHEMY_DATABASE_URI"]
    db_path = uri.replace("sqlite:///", "").replace("sqlite://", "")
    data_dir = os.path.dirname(db_path)
    if data_dir:
        os.makedirs(data_dir, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    @login_manager.unauthorized_handler
    def unauthorized():
        return jsonify({"error": "unauthorized"}), 401

    from app import models  # noqa: F401

    from app.api.auth import auth_bp
    from app.api.state import state_bp
    from app.api.movement import movement_bp
    from app.api.combat import combat_bp
    from app.api.inventory import inventory_bp
    from app.api.character import character_bp
    from app.api.chat import chat_bp
    from app.api.party import party_bp
    from app.api.shop import shop_bp
    from app.api.quest import quest_bp
    from app.api.trade import trade_bp
    from app.api.loot import loot_bp
    from app.api.craft import craft_bp
    from app.api.achievements import achievements_bp
    from app.api.auction import auction_bp
    from app.api.duel import duel_bp
    from app.api.contract import contract_bp # <-- НОВОЕ

    for bp in (auth_bp, state_bp, movement_bp, combat_bp,
               inventory_bp, character_bp, chat_bp, party_bp,
               shop_bp, quest_bp, trade_bp, loot_bp, craft_bp,
               achievements_bp, auction_bp, duel_bp, contract_bp): # <-- НОВОЕ
        app.register_blueprint(bp, url_prefix="/api")

    from sqlalchemy import event
    from sqlalchemy.engine import Engine

    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    @app.route("/")
    def index():
        return render_template("index.html")

    return app