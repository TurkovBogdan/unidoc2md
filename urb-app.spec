# -*- mode: python ; coding: utf-8 -*-

import os

exe_name = "unidoc2md"

# Абсолютный путь к иконке (Windows иначе может не подхватить иконку exe)
_spec_dir = os.path.dirname(os.path.abspath(SPEC))
_icon_path = os.path.join(_spec_dir, 'assets', 'icon.ico')
_assets_fonts = os.path.join(_spec_dir, 'assets', 'fonts')
_assets_data = os.path.join(_spec_dir, 'assets', 'data')

_datas = []
if os.path.isfile(_icon_path):
    _datas.append((_icon_path, 'assets'))
if os.path.isdir(_assets_fonts):
    _datas.append((_assets_fonts, 'assets/fonts'))
if os.path.isdir(_assets_data):
    _datas.append((_assets_data, 'assets/data'))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=_datas,
    hiddenimports=[
        'src.project',
        'src.project.manager',
        'src.project.config_io',
        'src.project.models',
        'src.project.config_models',
        'src.project.model_resolver',
        'src.project.validator',
        'src.gui.styles',
        'src.gui.state',
        'src.gui.adapters',
        'src.gui.adapters.backend',
        'src.gui.adapters.registry_options',
        'src.gui.screens',
        'src.gui.screens.settings_screen',
        'src.gui.screens.loading_screen',
        'src.gui.screens.model_settings',
        'src.gui.screens.project_detail',
        'src.gui.screens.home_screen',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=2,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=exe_name,
    icon=_icon_path,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
