# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('advanced_downloader.py', '.'), ('organize_folders.py', '.'), ('categorias.py', '.'), ('downloads.db', '.'), ('config.json', '.'), ('Palantir.ico', '.'), ('database_manager.py', '.'), ('download_manager.py', '.'), ('m3u_handler.py', '.'), ('network_utils.py', '.'), ('player_manager.py', '.'), ('config_manager.py', '.'), ('search_engine.py', '.'), ('aria2c.exe', '.'), ('Players/mpv/mpv.exe', 'Players/mpv'), ('Players/VLCPortable/VLCPortable.exe', 'Players/VLCPortable')]
binaries = []
hiddenimports = ['customtkinter', 'ttkthemes', 'aria2p', 'unidecode', 'PIL', 'requests', 'urllib3', 'sqlite3', 'logging', 'datetime', 'concurrent.futures']
tmp_ret = collect_all('customtkinter')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('ttkthemes')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['Palantir-windows.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
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
    name='Palantir',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['Palantir.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Palantir',
)
