"""
Zombie MMO — сборка exe через PyInstaller.

Запуск из корня проекта:
    python compiler/build.py
"""
import os
import sys
import shutil
import sqlite3
import subprocess
from pathlib import Path


COMPILER_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = COMPILER_DIR.parent
OUTPUT_DIR = COMPILER_DIR / "mmorpg"
BUILD_DIR = COMPILER_DIR / "_build"


def log(msg):
    print(f"[build] {msg}", flush=True)


def ensure_pyinstaller():
    try:
        import PyInstaller
        log(f"PyInstaller {PyInstaller.__version__} найден")
    except ImportError:
        log("PyInstaller не найден — устанавливаю...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "pyinstaller"]
        )
        log("PyInstaller установлен")


def clean():
    for p in (OUTPUT_DIR, BUILD_DIR):
        if p.exists():
            log(f"Удаляю {p}")
            shutil.rmtree(p)


def db_is_healthy(path):
    if not path.exists():
        return None
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            row = conn.execute("PRAGMA integrity_check").fetchone()
            return row is not None and row[0] == "ok"
        finally:
            conn.close()
    except sqlite3.DatabaseError:
        return False


def build():
    sep = ";" if sys.platform.startswith("win") else ":"
    add_data = [
        (PROJECT_ROOT / "app" / "templates", "app/templates"),
        (PROJECT_ROOT / "app" / "static",    "app/static"),
    ]

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "mmorpg",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--console",
        "--distpath", str(COMPILER_DIR),
        "--workpath", str(BUILD_DIR),
        "--specpath", str(COMPILER_DIR),
        "--paths", str(PROJECT_ROOT),
        "--collect-submodules", "seeds",
        "--collect-submodules", "app",
        "--hidden-import", "sqlalchemy.dialects.sqlite",
        "--hidden-import", "flask_login",
        "--hidden-import", "werkzeug.middleware.proxy_fix",
    ]

    for src, dest in add_data:
        cmd += ["--add-data", f"{src}{sep}{dest}"]

    cmd.append(str(PROJECT_ROOT / "run.py"))

    log("PyInstaller запуск...")
    subprocess.check_call(cmd)


def prepare_output_data():
    """
    Создаёт пустую data/ рядом с exe.
    Копирует project/data/game.db, только если он цел.
    """
    data_dir = OUTPUT_DIR / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    src = PROJECT_ROOT / "data" / "game.db"
    dst = data_dir / "game.db"

    healthy = db_is_healthy(src)

    if healthy is None:
        log("В проекте нет data/game.db — exe создаст её при первом запуске")
        return
    if not healthy:
        log("⚠ data/game.db в проекте повреждена — не копирую, exe создаст заново")
        return

    log(f"Копирую целую БД: {src.name} → {dst}")
    shutil.copy2(src, dst)


def write_readme():
    text = (
        "Zombie MMO — готовый билд\n"
        "==========================\n\n"
        "Запуск:\n"
        "  Двойной клик на mmorpg.exe.\n"
        "  Браузер откроется сам на http://localhost:5000/\n\n"
        "Играть с друзьями по локальной сети:\n"
        "  - Узнайте IP: ipconfig  (строка «IPv4-адрес»)\n"
        "  - Друзья откроют http://<ваш-IP>:5000/\n"
        "  - В брандмауэре Windows разрешите mmorpg.exe\n\n"
        "Данные:\n"
        "  - БД: data/game.db рядом с exe\n"
        "  - Если БД повреждена, игра сама перенесёт её\n"
        "    в карантин и создаст новую при следующем запуске.\n"
        "  - Полный сброс: удалите data/game.db* или запустите\n"
        "    mmorpg.exe --reset\n\n"
        "ВАЖНО:\n"
        "  Не запускайте два mmorpg.exe одновременно.\n"
        "  Не перемещайте папку data вручную.\n\n"
        "Аргументы:\n"
        "  --port 5001      другой порт\n"
        "  --reset          полный сброс БД\n"
        "  --no-browser     не открывать браузер\n"
    )
    (OUTPUT_DIR / "README.txt").write_text(text, encoding="utf-8")


def main():
    log(f"Проект: {PROJECT_ROOT}")
    log(f"Результат: {OUTPUT_DIR}")

    ensure_pyinstaller()
    clean()
    build()
    prepare_output_data()
    write_readme()

    exe = OUTPUT_DIR / ("mmorpg.exe" if sys.platform.startswith("win") else "mmorpg")
    if not exe.exists():
        raise RuntimeError(f"Сборка не создала {exe}")

    log(f"✅ Готово: {exe}")


if __name__ == "__main__":
    main()