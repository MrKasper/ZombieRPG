from datetime import datetime, timedelta
from flask import Blueprint, jsonify
from flask_login import current_user, login_required
from app.extensions import db
from app.models import Duel, Character
from app.services.progression import get_stats

duel_bp = Blueprint("duel", __name__)

DUEL_TIMEOUT_SEC = 60
MAX_ROUNDS = 30


def _serialize(d, viewer=None):
    return {
        "id": d.id,
        "challenger": {"id": d.challenger_id,
                       "name": d.challenger.name if d.challenger else "?",
                       "level": d.challenger.level if d.challenger else 0},
        "target": {"id": d.target_id,
                   "name": d.target.name if d.target else "?",
                   "level": d.target.level if d.target else 0},
        "status": d.status,
        "winner_id": d.winner_id,
        "winner_name": d.winner.name if d.winner else None,
        "rounds": d.rounds,
        "log": d.log or [],
        "is_challenger": viewer is not None and d.challenger_id == viewer.id,
        "is_target": viewer is not None and d.target_id == viewer.id,
    }


@duel_bp.post("/duel/challenge/<int:target_id>")
@login_required
def challenge(target_id):
    if target_id == current_user.id:
        return jsonify({"error": "self_duel"}), 400

    target = Character.query.get(target_id)
    if not target:
        return jsonify({"error": "no_such_character"}), 404
    if target.location_id != current_user.location_id:
        return jsonify({"error": "not_same_location"}), 400
    if not current_user.location.is_safe_zone:
        return jsonify({"error": "duel_only_in_safe_zone"}), 400
    if current_user.in_combat_id or target.in_combat_id:
        return jsonify({"error": "in_combat"}), 400

    existing = Duel.query.filter(
        Duel.status == "pending",
        db.or_(
            db.and_(Duel.challenger_id == current_user.id,
                    Duel.target_id == target.id),
            db.and_(Duel.challenger_id == target.id,
                    Duel.target_id == current_user.id),
        )
    ).first()
    if existing:
        return jsonify({"ok": True, "duel_id": existing.id})

    duel = Duel(
        challenger_id=current_user.id,
        target_id=target.id,
        status="pending",
        expires_at=datetime.utcnow() + timedelta(seconds=DUEL_TIMEOUT_SEC),
    )
    db.session.add(duel)
    db.session.commit()
    return jsonify({"ok": True, "duel_id": duel.id})


@duel_bp.post("/duel/accept/<int:duel_id>")
@login_required
def accept(duel_id):
    duel = Duel.query.get_or_404(duel_id)
    if duel.status != "pending":
        return jsonify({"error": "duel_closed"}), 400
    if duel.target_id != current_user.id:
        return jsonify({"error": "not_your_duel"}), 403
    if duel.expires_at and duel.expires_at < datetime.utcnow():
        duel.status = "expired"
        db.session.commit()
        return jsonify({"error": "duel_expired"}), 400

    # автобой
    _resolve_duel(duel)
    db.session.commit()
    return jsonify({"ok": True, "duel": _serialize(duel, current_user)})


@duel_bp.post("/duel/decline/<int:duel_id>")
@login_required
def decline(duel_id):
    duel = Duel.query.get_or_404(duel_id)
    if duel.status != "pending":
        return jsonify({"error": "duel_closed"}), 400
    if current_user.id not in (duel.challenger_id, duel.target_id):
        return jsonify({"error": "not_participant"}), 403
    duel.status = "declined"
    duel.finished_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"ok": True})


@duel_bp.get("/duel/current")
@login_required
def current():
    now = datetime.utcnow()

    pending = (Duel.query
               .filter_by(status="pending")
               .filter(db.or_(Duel.challenger_id == current_user.id,
                              Duel.target_id == current_user.id))
               .filter(Duel.expires_at > now)
               .order_by(Duel.id.desc())
               .first())

    recent = (Duel.query
              .filter_by(status="finished")
              .filter(db.or_(Duel.challenger_id == current_user.id,
                             Duel.target_id == current_user.id))
              .order_by(Duel.finished_at.desc())
              .limit(1)
              .first())

    return jsonify({
        "pending": _serialize(pending, current_user) if pending else None,
        "recent": _serialize(recent, current_user) if recent else None,
    })


@duel_bp.get("/duel/leaderboard")
@login_required
def leaderboard():
    rows = (Character.query
            .filter(Character.pvp_wins > 0)
            .order_by(Character.pvp_wins.desc())
            .limit(10).all())
    return jsonify({
        "leaders": [
            {"id": c.id, "name": c.name, "level": c.level,
             "wins": c.pvp_wins or 0, "losses": c.pvp_losses or 0}
            for c in rows
        ],
    })


def _resolve_duel(duel):
    ch = Character.query.get(duel.challenger_id)
    tg = Character.query.get(duel.target_id)

    ch_stats = get_stats(ch)
    tg_stats = get_stats(tg)

    ch_hp = ch_stats["max_hp"]
    tg_hp = tg_stats["max_hp"]

    log = [f"⚔️ Дуэль: {ch.name} vs {tg.name}"]
    import random

    def calc_hit(atk, dfn, eva):
        if eva > 0 and random.random() * 100 < eva:
            return None  # промах
        raw = atk * random.uniform(0.9, 1.1)
        mitigated = raw * (100 / (100 + max(0, dfn)))
        return max(1, round(mitigated))

    for rnd in range(1, MAX_ROUNDS + 1):
        duel.rounds = rnd

        # A бьёт B
        dmg = calc_hit(ch_stats["attack"], tg_stats["defense"],
                       tg_stats["evasion"])
        if dmg is None:
            log.append(f"💨 {tg.name} уклоняется")
        else:
            tg_hp -= dmg
            log.append(f"🗡️ {ch.name} наносит {dmg} → {tg.name} ({tg_hp} HP)")
        if tg_hp <= 0:
            duel.winner_id = ch.id
            break

        # B бьёт A
        dmg = calc_hit(tg_stats["attack"], ch_stats["defense"],
                       ch_stats["evasion"])
        if dmg is None:
            log.append(f"💨 {ch.name} уклоняется")
        else:
            ch_hp -= dmg
            log.append(f"🗡️ {tg.name} наносит {dmg} → {ch.name} ({ch_hp} HP)")
        if ch_hp <= 0:
            duel.winner_id = tg.id
            break

    if duel.winner_id is None:
        log.append("🤝 Ничья")
    else:
        winner = Character.query.get(duel.winner_id)
        loser = tg if winner.id == ch.id else ch
        winner.pvp_wins = (winner.pvp_wins or 0) + 1
        loser.pvp_losses = (loser.pvp_losses or 0) + 1
        winner.add_xp(50 + loser.level * 5)
        log.append(f"🏆 Победитель: {winner.name}!")

    duel.log = log
    duel.status = "finished"
    duel.finished_at = datetime.utcnow()