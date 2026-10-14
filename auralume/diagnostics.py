"""Read-only environment diagnostics, available without a graphical session."""
import ctypes.util
import importlib.metadata
import platform
import sys

from . import __version__


def environment_report():
    versions = {}
    for name in ('PySide6', 'mpv', 'mutagen', 'yt-dlp'):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = 'metadata unavailable'
    return {'auralume': __version__, 'python': platform.python_version(),
            'system': platform.system(), 'architecture': platform.machine(),
            'glibc': platform.libc_ver(), 'frozen': bool(getattr(sys, 'frozen', False)),
            'libmpv': ctypes.util.find_library('mpv'), 'packages': versions}
