# -*- mode: python ; coding: utf-8 -*-

bin=[('lib/x64/phidget22.dll','lib/x64')]  #.dll pour systeme 64bits

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=bin,
    datas=[
    ('graphic/images/icon-appli.ico','graphic/images'),\
    ('graphic/images/green-led-on.png','graphic/images'),\
    ('graphic/images/red-led-on.png','graphic/images'),\
    ('graphic/images/pause_icon.png','graphic/images'),\
    ('graphic/images/play_icon.png','graphic/images'),\
    ('config/app_default_settings.ini','config'),\
    ('config/CALlog.txt','config'),\
    ('config/device_id.ini','config'),\
    ('config/latest_cal.ini','config'),\
    ('lib/oceandirect/lib/OceanDirect.dll','lib/oceandirect/lib')],
    hiddenimports=[],
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
    exclude_binaries=False,
    name='Dommino',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    icon='graphic/images/icon-appli.ico',
    disable_windowed_traceback=True,
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
    name='Dommino',
    icon='graphic/images/icon-appli.ico'
)
