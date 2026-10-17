"""Load the native mpv dependency before importing its ctypes binding.

Windows ships a private native/ directory. The binding's PATH-based discovery
needs a temporary, absolute search path in addition to AddDllDirectory. Handles
stay alive for delayed native loads; the user's PATH is always restored.
"""
import ctypes
import ctypes.util
import importlib
import os
from pathlib import Path
import struct
import sys
from threading import RLock

_lock = RLock()
_dll_directories = {}
DLL_NAMES = ('mpv-2.dll', 'libmpv-2.dll')


def _is_windows():
    return sys.platform == 'win32'


def windows_library_path() -> Path:
    if getattr(sys, 'frozen', False):
        root = Path(sys._MEIPASS) / 'native'
    elif os.environ.get('AURALUME_MPV_DIR'):
        root = Path(os.environ['AURALUME_MPV_DIR'])
        if not root.is_absolute():
            raise OSError('AURALUME_MPV_DIR deve ser um caminho absoluto.')
    else:
        root = Path(__file__).resolve().parents[1] / 'vendor' / 'mpv'
    for name in DLL_NAMES:
        candidate = root / name
        if candidate.is_file():
            return candidate.resolve()
    raise OSError(f'mpv-2.dll/libmpv-2.dll ausente em {root}. Extraia o pacote completo do Auralume.')


def validate_windows_dll(path: Path) -> None:
    """Reject a wrong architecture early; the Windows loader validates imports."""
    with path.open('rb') as stream:
        dos = stream.read(64)
        if len(dos) != 64 or dos[:2] != b'MZ':
            raise OSError('Biblioteca libmpv não é um arquivo PE Windows x64 válido.')
        offset = struct.unpack_from('<I', dos, 60)[0]
        if offset < 64 or offset > path.stat().st_size - 6:
            raise OSError('Cabeçalho PE inválido na biblioteca Windows x64.')
        stream.seek(offset)
        pe = stream.read(6)
    if pe[:4] != b'PE\0\0' or struct.unpack_from('<H', pe, 4)[0] != 0x8664:
        raise OSError('A biblioteca libmpv precisa ser Windows x64 (AMD64).')
    if ctypes.sizeof(ctypes.c_void_p) != 8:
        raise OSError('O Auralume Windows requer Python e libmpv x64.')


def load_mpv():
    with _lock:
        if not _is_windows():
            return importlib.import_module('mpv')
        path = windows_library_path()
        validate_windows_dll(path)
        directory = str(path.parent)
        if directory not in _dll_directories:
            _dll_directories[directory] = os.add_dll_directory(directory)
        old_path = os.environ.get('PATH')
        try:
            # ctypes.util.find_library on Windows iterates PATH. Do not allow an
            # unrelated earlier mpv DLL or an empty/relative PATH entry to win.
            os.environ['PATH'] = directory
            binding = importlib.import_module('mpv')
        finally:
            if old_path is None:
                os.environ.pop('PATH', None)
            else:
                os.environ['PATH'] = old_path
        loaded = Path(str(binding.backend._name)).resolve()
        if loaded != path:
            raise OSError('Uma libmpv externa já foi carregada neste processo; reinicie o Auralume.')
        return binding


def loaded_windows_module(name: str) -> str:
    """Ask the OS for a loaded module, not for a filesystem search candidate."""
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetModuleHandleW.argtypes = [ctypes.c_wchar_p]
    kernel.GetModuleHandleW.restype = ctypes.c_void_p
    kernel.GetModuleFileNameW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint32]
    kernel.GetModuleFileNameW.restype = ctypes.c_uint32
    handle = kernel.GetModuleHandleW(name)
    if not handle:
        raise OSError(f'Dependência não carregada: {name}')
    buffer = ctypes.create_unicode_buffer(32768)
    length = kernel.GetModuleFileNameW(handle, buffer, len(buffer))
    if not length or length >= len(buffer):
        raise OSError(f'Não foi possível obter o caminho da dependência: {name}')
    return buffer.value


def probe_mpv() -> dict:
    """Create/destroy a real null-output engine without Qt, DB or user config."""
    report = {'detected': False, 'path': None, 'loaded': False,
              'engine_created': False, 'version': None, 'error': None, 'loaded_dependencies': {}}
    engine = None
    try:
        candidate = str(windows_library_path()) if _is_windows() else ctypes.util.find_library('mpv')
        report.update(detected=bool(candidate), path=candidate)
        binding = load_mpv()
        report.update(loaded=True, path=str(binding.backend._name))
        if _is_windows():
            report['loaded_dependencies']['vulkan-1.dll'] = loaded_windows_module('vulkan-1.dll')
        engine = binding.MPV(ao='null', video=False, audio_display='no', config=False,
                             ytdl=False, terminal=False, input_default_bindings=False,
                             input_vo_keyboard=False, osc=False)
        report.update(engine_created=True, version=engine.mpv_version)
    except Exception as error:
        report['error'] = f'{type(error).__name__}: {error}'
    finally:
        if engine is not None:
            engine.terminate()
    return report
