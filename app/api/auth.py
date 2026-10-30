from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models import Character, Location
from app.services.spawn import find_free_cell

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/auth/register")
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    name = (data.get("name") or "").strip()

    if not (3 <= len(username) <= 32):
        return jsonify({"error": "username_length"}), 400
    if len(password) < 6:
        return jsonify({"error": "password_short"}), 400
    if not (2 <= len(name) <= 32):
        return jsonify({"error": "name_length"}), 400
    if Character.query.filter_by(username=username).first():
        return jsonify({"error": "username_taken"}), 400
    if Character.query.filter_by(name=name).first():
        return jsonify({"error": "name_taken"}), 400

    start = Location.query.filter_by(is_safe_zone=True).first()
    if not start:
        return jsonify({"error": "no_start_location"}), 500

    sx, sy = find_free_cell(start, prefer_center=False)

    char = Character(username=username, name=name,
                     location_id=start.id, x=sx, y=sy, hp=50, mp=20)
    char.set_password(password)
    db.session.add(char)
    db.session.commit()
    login_user(char, remember=True)
    return jsonify({"ok": True, "id": char.id, "name": char.name})


@auth_bp.post("/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    char = Character.query.filter_by(username=username).first()
    if not char or not char.check_password(password):
        return jsonify({"error": "invalid_credentials"}), 401
    login_user(char, remember=True)
    return jsonify({"ok": True, "id": char.id, "name": char.name})


@auth_bp.post("/auth/logout")
@login_required
def logout():
    logout_user()
    return jsonify({"ok": True})


@auth_bp.get("/auth/me")
def me():
    if not current_user.is_authenticated:
        return jsonify({"authenticated": False})
    return jsonify({
        "authenticated": True,
        "id": current_user.id,
        "name": current_user.name,
        "username": current_user.username,
    })