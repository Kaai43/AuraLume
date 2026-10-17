"""Read-only environment diagnostics, available without a graphical session."""
import importlib.metadata
import platform
import sys

from . import __version__
from .native import probe_mpv


def environment_report():
    versions = {}
    for name in ('PySide6', 'mpv', 'mutagen', 'yt-dlp'):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = 'metadata unavailable'
    native = probe_mpv()
    return {'auralume': __version__, 'python': platform.python_version(),
            'system': platform.system(), 'architecture': platform.machine(),
            'glibc': platform.libc_ver(), 'frozen': bool(getattr(sys, 'frozen', False)),
            'libmpv': native['path'], 'native_mpv': native, 'packages': versions}
