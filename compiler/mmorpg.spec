# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ['sqlalchemy.dialects.sqlite', 'flask_login', 'werkzeug.middleware.proxy_fix']
hiddenimports += collect_submodules('seeds')
hiddenimports += collect_submodules('app')


a = Analysis(
    ['C:/Users/Student.IZHKOOP/Documents/mmorpg_app/run.py'],
    pathex=['C:/Users/Student.IZHKOOP/Documents/mmorpg_app'],
    binaries=[],
    datas=[('C:/Users/Student.IZHKOOP/Documents/mmorpg_app/app/templates', 'app/templates'), ('C:/Users/Student.IZHKOOP/Documents/mmorpg_app/app/static', 'app/static')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='mmorpg',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='mmorpg',
)
