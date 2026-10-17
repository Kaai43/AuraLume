# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import copy_metadata
import os
from pathlib import Path
import sys

windows = sys.platform == 'win32'
datas = [('packaging/auralume.svg', 'packaging'), ('LICENSE', 'licenses')]
if windows:
    # Avoid presenting host Ubuntu/Python notices as the Windows native inventory.
    for path in Path('packaging/licenses').iterdir():
        if not path.name.startswith(('Ubuntu-', 'Python-', 'Qt-')):
            datas.append((str(path), 'licenses/' + path.name if path.is_dir() else 'licenses'))
else:
    datas.append(('packaging/licenses', 'licenses'))
binaries = []
if windows:
    native = Path(os.environ.get('AURALUME_MPV_DIR', 'vendor/mpv')).resolve()
    for name in ('libmpv-2.dll', 'vulkan-1.dll'):
        if not (native / name).is_file():
            raise RuntimeError(f'Missing {name}; run scripts/windows_native.py first')
        binaries.append((str(native / name), 'native'))
    datas += [(str(native / 'native-manifest.json'), 'native'),
              (str(native / 'licenses'), 'licenses/windows-native'),
              ('packaging/windows', 'licenses/windows-build')]
for package in ('PySide6', 'shiboken6', 'mpv', 'mutagen', 'yt-dlp'):
    datas += copy_metadata(package)

a = Analysis(
    ['run.py'], pathex=[], binaries=binaries, datas=datas,
    hiddenimports=['mpv', 'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets'],
    hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=['tkinter', 'pytest', 'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets',
              'PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.QtMultimedia'],
    noarchive=False,
)
# Keep host libmpv/codecs and other system libraries external. Qt wheel libraries
# and the Python runtime remain in the folder (documented PyInstaller API).
if not windows:
    a.exclude_system_libraries()
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='Auralume',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=True, disable_windowed_traceback=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='Auralume')
