"""Unit checks for Windows loader boundaries; real engine tests remain separate."""
import os
from pathlib import Path
import struct
from types import SimpleNamespace

import pytest


def pe_stub(path, machine=0x8664):
    header = bytearray(128)
    header[:2] = b'MZ'
    struct.pack_into('<I', header, 60, 64)
    header[64:68] = b'PE\x00\x00'
    struct.pack_into('<H', header, 68, machine)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(header)
    return path


def test_windows_loader_uses_absolute_directory_before_import_and_restores_path(tmp_path, monkeypatch):
    from auralume import native
    directory = tmp_path / 'DLL música com espaços'
    dll = pe_stub(directory / 'mpv-2.dll')
    monkeypatch.setattr(native, '_is_windows', lambda: True)
    monkeypatch.setenv('AURALUME_MPV_DIR', str(directory))
    monkeypatch.setenv('PATH', 'unchanged-path')
    handle = object()
    opened = []
    monkeypatch.setattr(os, 'add_dll_directory', lambda p: opened.append(p) or handle, raising=False)
    monkeypatch.setattr(native, '_dll_directories', {})

    def import_binding(name):
        assert name == 'mpv'
        assert opened == [str(directory)]
        assert os.environ['PATH'] == str(directory)
        return SimpleNamespace(backend=SimpleNamespace(_name=str(dll)))

    monkeypatch.setattr(native.importlib, 'import_module', import_binding)
    assert native.load_mpv().backend._name == str(dll)
    assert os.environ['PATH'] == 'unchanged-path'
    assert native._dll_directories[str(directory)] is handle


def test_windows_load_failure_restores_environment_and_reports_native_error(tmp_path, monkeypatch):
    from auralume import native
    pe_stub(tmp_path / 'mpv-2.dll')
    monkeypatch.setattr(native, '_is_windows', lambda: True)
    monkeypatch.setenv('AURALUME_MPV_DIR', str(tmp_path))
    monkeypatch.delenv('PATH', raising=False)
    monkeypatch.setattr(os, 'add_dll_directory', lambda p: object(), raising=False)
    monkeypatch.setattr(native, '_dll_directories', {})

    def fail(name):
        raise OSError('transitive dependency missing')

    monkeypatch.setattr(native.importlib, 'import_module', fail)
    with pytest.raises(OSError, match='transitive dependency missing'):
        native.load_mpv()
    assert 'PATH' not in os.environ


def test_frozen_ignores_external_override_and_current_directory(tmp_path, monkeypatch):
    from auralume import native
    bundle = tmp_path / 'Aplicativo extraído' / '_internal'
    bundled = pe_stub(bundle / 'native' / 'mpv-2.dll')
    outside = tmp_path / 'other'
    pe_stub(outside / 'mpv-2.dll')
    monkeypatch.setattr(native.sys, 'frozen', True, raising=False)
    monkeypatch.setattr(native.sys, '_MEIPASS', str(bundle), raising=False)
    monkeypatch.setenv('AURALUME_MPV_DIR', str(outside))
    monkeypatch.chdir(outside)
    assert native.windows_library_path() == bundled


@pytest.mark.parametrize('machine', [0x014c, 0xaa64])
def test_non_x64_dll_rejected_before_import(tmp_path, machine):
    from auralume import native
    with pytest.raises(OSError, match='x64'):
        native.validate_windows_dll(pe_stub(tmp_path / 'bad.dll', machine))


def test_relative_override_and_missing_dll_are_explicit_failures(tmp_path, monkeypatch):
    from auralume import native
    monkeypatch.setenv('AURALUME_MPV_DIR', 'relative')
    with pytest.raises(OSError, match='absoluto'):
        native.windows_library_path()
    monkeypatch.setenv('AURALUME_MPV_DIR', str(tmp_path))
    with pytest.raises(OSError, match='mpv-2.dll'):
        native.windows_library_path()


def test_linux_does_not_change_dll_environment(monkeypatch):
    from auralume import native
    monkeypatch.setattr(native, '_is_windows', lambda: False)
    monkeypatch.setenv('PATH', 'original')
    binding = object()
    monkeypatch.setattr(native.importlib, 'import_module', lambda name: binding)
    assert native.load_mpv() is binding
    assert os.environ['PATH'] == 'original'


def test_diagnostics_distinguishes_load_failure_from_engine_creation(monkeypatch):
    from auralume import native

    def fail():
        raise OSError('broken DLL')

    monkeypatch.setattr(native, 'load_mpv', fail)
    report = native.probe_mpv()
    assert not report['loaded'] and not report['engine_created']
    assert 'broken DLL' in report['error']


def test_data_paths_preserve_linux_and_use_windows_local_appdata(tmp_path):
    from auralume.paths import default_data_dir
    assert default_data_dir('linux', {'XDG_DATA_HOME':str(tmp_path)}, tmp_path) == tmp_path / 'Auralume'
    assert default_data_dir('linux', {}, tmp_path) == tmp_path / '.local/share/Auralume'
    assert default_data_dir('win32', {'LOCALAPPDATA':str(tmp_path / 'AppData/Local')}, tmp_path) == tmp_path / 'AppData/Local/Auralume'
    assert default_data_dir('win32', {}, tmp_path) == tmp_path / 'AppData/Local/Auralume'
    assert not (tmp_path / 'AppData').exists()


def test_windows_preserves_existing_legacy_library_without_moving_data(tmp_path):
    from auralume.paths import default_data_dir
    legacy = tmp_path / '.local/share/Auralume'
    legacy.mkdir(parents=True)
    database = legacy / 'library.sqlite3'
    database.write_bytes(b'existing database')
    assert default_data_dir('win32', {}, tmp_path) == legacy
    assert database.read_bytes() == b'existing database'
    modern = tmp_path / 'AppData/Local/Auralume'
    modern.mkdir(parents=True)
    (modern / 'library.sqlite3').write_bytes(b'newer database')
    assert default_data_dir('win32', {}, tmp_path) == modern


def test_windows_disables_every_builtin_lua_entry_point(monkeypatch):
    """The pinned libmpv-2.dll ships LuaJIT plus nine builtin Lua scripts."""
    from auralume import native
    monkeypatch.setattr(native, '_is_windows', lambda: True)
    options = native.mpv_script_options()
    assert set(options) == set(native._LUA_SCRIPTS)
    assert {'osc', 'ytdl', 'load_scripts', 'load_stats_overlay', 'load_console',
            'load_auto_profiles', 'load_select', 'load_positioning',
            'load_commands', 'load_context_menu'} == set(options)
    assert all(value is False for value in options.values())


def test_linux_keeps_existing_player_options(monkeypatch):
    from auralume import native
    monkeypatch.setattr(native, '_is_windows', lambda: False)
    assert native.mpv_script_options() == {}
