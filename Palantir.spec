# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('C:\\Users\\hilde\\Dev\\palantir-RR\\advanced_downloader.py', '.'), ('C:\\Users\\hilde\\Dev\\palantir-RR\\organize_folders.py', '.'), ('C:\\Users\\hilde\\Dev\\palantir-RR\\organize_folders_wrapper.py', '.'), ('C:\\Users\\hilde\\Dev\\palantir-RR\\categorias.py', '.'), ('C:\\Users\\hilde\\Dev\\palantir-RR\\downloads.db', '.'), ('C:\\Users\\hilde\\Dev\\palantir-RR\\config.json', '.'), ('C:\\Users\\hilde\\Dev\\palantir-RR\\aria2c.exe', '.'), ('C:\\Users\\hilde\\Dev\\palantir-RR\\Players\\mpv\\mpv.exe', 'Players/mpv'), ('C:\\Users\\hilde\\Dev\\palantir-RR\\Players\\VLCPortable\\VLCPortable.exe', 'Players/VLCPortable')]
binaries = []
hiddenimports = ['customtkinter', 'ttkthemes', 'aria2p', 'unidecode', 'PIL', 'requests', 'urllib3', 'sqlite3', 'logging', 'datetime', 'concurrent.futures']
tmp_ret = collect_all('customtkinter')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('ttkthemes')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['C:\\Users\\hilde\\Dev\\palantir-RR\\Palantir-windows.py'],
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
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\Users\\hilde\\Dev\\palantir-RR\\Palantir.ico'],
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
