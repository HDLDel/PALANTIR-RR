# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['/home/del/Dev/Palantir/PalantirCLI.py'],
    pathex=[],
    binaries=[],
    datas=[('organize_folders.py', '.'), ('categorias.py', '.'), ('download_textual.css', '.'), ('assets', 'assets')],
    hiddenimports=['npyscreen', 'sqlite3', 're', 'requests', 'threading', 'concurrent.futures', 'charset_normalizer', 'certifi', 'idna', 'urllib3', 'json', 'time', 'os', 'sys', 'shutil', 'unicodedata', 'subprocess', 'platform', 'pathlib', 'asyncio', 'textual', 'textual.driver', 'textual.drivers', 'textual.widgets', 'textual.containers', 'rich', 'rich.console', 'rich.theme'],
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
    a.binaries,
    a.datas,
    [],
    name='palantircli',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['Palantir.ico'],
)
