# PyInstaller spec for the community PoE2 loot filter updater.
# Build with: pyinstaller client_updater/updater.spec
# Output lands in client_updater/pyinstaller_dist/ (see .gitignore).

# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ["run_updater.py"],
    pathex=["."],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="PoE2LootFilterUpdater",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    # Keep a console so `install`/`run`/`uninstall` output is actually visible when a player
    # double-clicks the exe or runs it from a shortcut; means the scheduled background check
    # will briefly flash a console window every interval — an acceptable MVP trade-off.
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
