# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules


hiddenimports = (
    collect_submodules("companies")
    + collect_submodules("config")
    + collect_submodules("whitenoise")
)


a = Analysis(
    ["launcher.py"],
    pathex=[
        r"D:\Projects\titan_web",
    ],
    binaries=[],
    datas=[
        (
            r"companies\templates",
            r"companies\templates",
        ),
        (
            r"staticfiles",
            r"staticfiles",
        ),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)


pyz = PYZ(
    a.pure,
)


exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="TitanWeb",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
)


collect = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="TitanWeb",
)