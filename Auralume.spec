# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import copy_metadata

datas = [('packaging/licenses', 'licenses')]
for package in ('PySide6', 'shiboken6', 'mpv', 'mutagen', 'yt-dlp'):
    datas += copy_metadata(package)

a = Analysis(
    ['run.py'], pathex=[], binaries=[], datas=datas,
    hiddenimports=['PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets'],
    hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=['tkinter', 'pytest', 'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets',
              'PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.QtMultimedia'],
    noarchive=False,
)
# Keep host libmpv/codecs and other system libraries external. Qt wheel libraries
# and the Python runtime remain in the folder (documented PyInstaller API).
a.exclude_system_libraries()
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='Auralume',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=True, disable_windowed_traceback=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='Auralume')
