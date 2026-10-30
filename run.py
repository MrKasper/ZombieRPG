"""
Zombie MMO launcher.

    python run.py                  обычный запуск
    python run.py --reset          полный сброс БД
    python run.py --port 5001      другой порт
    python run.py --no-debug       без debug
    python run.py --no-seed        схема без наполнения
    python run.py --no-browser     не открывать браузер
    python run.py --force          игнорировать блокировку (2 сервера на 1 ПК!)
"""
import os
import sys
import socket
import sqlite3
import argparse
import threading
import webbrowser
from datetime import datetime
from sqlalchemy import inspect

from app import create_app
from app.extensions import db


app = create_app()
IS_FROZEN = getattr(sys, "frozen", False)


# ---------- утилиты ----------

def _db_path():
    return app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "")


def _expected_tables():
    return {t.name for t in db.metadata.tables.values()}


def _existing_tables():
    with app.app_context():
        return set(inspect(db.engine).get_table_names())


def _create_missing():
    with app.app_context():
        missing = _expected_tables() - _existing_tables()
        if missing:
            print(f"→ Создаём {len(missing)} таблиц: {', '.join(sorted(missing))}")
            db.create_all()
            return True
        return False


def _world_is_empty():
    with app.app_context():
        from app.models import Location
        return Location.query.count() == 0


def _seed(force=False):
    from seeds import seed_all
    with app.app_context():
        seed_all(force=force)


# ---------- целостность ----------

def _db_integrity_ok(path):
    if not os.path.exists(path):
        return None
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            row = conn.execute("PRAGMA integrity_check").fetchone()
            return row is not None and row[0] == "ok"
        finally:
            conn.close()
    except sqlite3.DatabaseError as e:
        print(f"  ⚠ БД не открывается: {e}")
        return False
    except Exception as e:
        print(f"  ⚠ Ошибка проверки БД: {e}")
        return False


def _quarantine_db(path):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    for suf in ("", "-wal", "-shm"):
        p = path + suf
        if os.path.exists(p):
            broken = f"{p}.broken-{ts}"
            try:
                os.replace(p, broken)
                print(f"  → {os.path.basename(p)} → {os.path.basename(broken)}")
            except OSError as e:
                print(f"  ⚠ Не смог переименовать {p}: {e}")


def _ensure_healthy_db():
    path = _db_path()
    ok = _db_integrity_ok(path)
    if ok is None:
        print("→ БД ещё нет — создадим при первом запуске")
        return
    if ok is True:
        print("✓ БД цела")
        return
    print("✗ БД повреждена — переношу в карантин и создаю новую")
    with app.app_context():
        db.session.remove()
        db.engine.dispose()
    _quarantine_db(path)


# ---------- bootstrap ----------

def _reset():
    print("→ Полный сброс БД...")
    with app.app_context():
        db.session.remove()
        db.engine.dispose()

    path = _db_path()
    for suf in ("", "-wal", "-shm"):
        p = path + suf
        if os.path.exists(p):
            try:
                os.remove(p)
                print(f"  удалён {os.path.basename(p)}")
            except OSError as e:
                print(f"  не удалось удалить {os.path.basename(p)}: {e}")
                raise

    _create_missing()
    _seed(force=True)


def _bootstrap(no_seed=False):
    _ensure_healthy_db()
    created = _create_missing()
    if no_seed:
        print("✓ Схема готова (seed пропущен)")
        return
    if created or _world_is_empty():
        print("→ Наполняем мир...")
        _seed(force=False)
    else:
        print("✓ БД готова")


# ---------- single-instance lock ----------

def _acquire_lock():
    """
    Файл-lock рядом с БД. Не даёт запустить два сервера на одной машине.
    Возвращает открытый файл (держать) или None, если уже занято.
    """
    lock_path = os.path.join(os.path.dirname(_db_path()), "mmorpg.lock")
    try:
        f = open(lock_path, "a+b")
        f.seek(0)
        if f.read(1) == b"":
            f.write(b"0")
            f.flush()
        f.seek(0)
        if sys.platform.startswith("win"):
            import msvcrt
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return f
    except (OSError, IOError):
        return None


# ---------- сетевые адреса ----------

def _local_ips():
    """Список не-loopback IPv4-адресов этой машины."""
    ips = set()
    try:
        hostname = socket.gethostname()
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if not ip.startswith("127."):
                ips.add(ip)
    except Exception:
        pass

    # второй способ — через фиктивное UDP-соединение
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.add(s.getsockname()[0])
        s.close()
    except Exception:
        pass

    return sorted(ips)


def _print_addresses(port):
    print("")
    print("═" * 56)
    print("  Зомби-MMO запущена")
    print("═" * 56)
    print(f"  Хост (эта машина):  http://localhost:{port}/")

    ips = _local_ips()
    if ips:
        print("")
        print("  Для друзей по локальной сети — открой у себя в браузере:")
        for ip in ips:
            print(f"    http://{ip}:{port}/")
        print("")
        print("  Раздай эту ссылку. Им exe запускать НЕ нужно.")
    else:
        print("")
        print("  ⚠ Не удалось определить локальный IP.")
        print("    Проверь подключение и выполни в консоли: ipconfig")
        print("    Ищи строку «IPv4-адрес» и дай друзьям:")
        print(f"      http://<твой-IP>:{port}/")

    print("")
    print("  Если друзья не заходят — разреши mmorpg.exe в брандмауэре")
    print("  Windows для частных сетей.")
    print("═" * 56)
    print("")


# ---------- browser ----------

def _open_browser_later(port):
    def _open():
        try:
            webbrowser.open(f"http://localhost:{port}/")
        except Exception:
            pass
    threading.Timer(1.5, _open).start()


# ---------- main ----------

def main():
    parser = argparse.ArgumentParser(description="Zombie MMO launcher")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--no-seed", action="store_true")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--no-debug", action="store_true")
    parser.add_argument("--force", action="store_true",
                        help="игнорировать блокировку (опасно: два сервера на 1 ПК)")
    args = parser.parse_args()

    debug = not args.no_debug and not IS_FROZEN
    is_reloader_child = os.environ.get("WERKZEUG_RUN_MAIN") == "true"

    lock_handle = None

    if not is_reloader_child:
        if not args.force:
            lock_handle = _acquire_lock()
            if lock_handle is None:
                print("")
                print("═" * 56)
                print("  Сервер уже запущен на этом компьютере.")
                print("═" * 56)
                print("")
                print("  Тебе не нужно запускать второй exe — сервер уже работает.")
                print("")
                print("  ▸ Если ты хочешь ИГРАТЬ сам — открой в браузере:")
                print(f"      http://localhost:{args.port}/")
                print("")
                print("  ▸ Если друзья хотят играть — они открывают в браузере:")
                ips = _local_ips()
                if ips:
                    for ip in ips:
                        print(f"      http://{ip}:{args.port}/")
                else:
                    print(f"      http://<твой-IP>:{args.port}/")
                print("")
                print("  ▸ Если ты реально хочешь второй сервер на этой машине —")
                print("    запусти с флагом --force и другим портом:")
                print(f"      mmorpg.exe --force --port {args.port + 1}")
                print("    ⚠ Два сервера на одной БД = порча данных.")
                print("    Используй --force только если уверен.")
                print("═" * 56)
                print("")
                if IS_FROZEN:
                    try:
                        input("Нажми Enter, чтобы выйти...")
                    except Exception:
                        pass
                sys.exit(1)

        try:
            if args.reset:
                _reset()
            else:
                _bootstrap(no_seed=args.no_seed)

            _print_addresses(args.port)

            if IS_FROZEN and not args.no_browser:
                _open_browser_later(args.port)

            app.run(host="0.0.0.0", port=args.port, debug=debug)
        except KeyboardInterrupt:
            print("\n→ Остановлено")
        finally:
            if lock_handle:
                try:
                    lock_handle.close()
                except Exception:
                    pass
    else:
        app.run(host="0.0.0.0", port=args.port, debug=debug)


if __name__ == "__main__":
    main()