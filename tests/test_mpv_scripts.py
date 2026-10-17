"""Exercise Windows embedding options with the real native engine on both hosts."""
from pathlib import Path
import os
import subprocess
import sys
import textwrap

import pytest

from auralume import native, player


@pytest.mark.integration
@pytest.mark.parametrize('consumer', ['player', 'diagnostics'])
def test_windows_engine_never_starts_lua_scripts(tmp_path, monkeypatch, consumer):
    binding = native.load_mpv()
    real_constructor = binding.MPV
    log = tmp_path / 'mpv-initialization.log'
    options = {}

    def construct(**kwargs):
        options.update(kwargs)
        return real_constructor(**kwargs, log_file=str(log))

    # Simulate only platform/discovery; construction and teardown use real libmpv.
    monkeypatch.setattr(native, '_is_windows', lambda: True)
    monkeypatch.setattr(native, 'windows_library_path', lambda: Path(binding.backend._name))
    monkeypatch.setattr(native, 'loaded_windows_module', lambda name: None)
    monkeypatch.setattr(native, 'load_mpv', lambda: binding)
    monkeypatch.setattr(player, 'load_mpv', lambda: binding)
    monkeypatch.setattr(binding, 'MPV', construct)
    if consumer == 'player':
        engine = player.MpvPlayer(audio_output='null')
        try:
            assert engine.available, engine.initialization_error
        finally:
            engine.close()
    else:
        report = native.probe_mpv()
        assert report['engine_created'], report['error']

    output = log.read_text(encoding='utf-8')
    assert 'Loading lua script' not in output, output
    for option in native._LUA_SCRIPTS:
        assert options.get(option) is False, option


@pytest.mark.integration
def test_full_script_disable_is_complete_and_minimal_is_insufficient(tmp_path):
    """The pinned Windows build loads builtin scripts unless every switch is off."""
    binding = native.load_mpv()

    def loaded_lua_scripts(options):
        log = tmp_path / 'initialization.log'
        engine = binding.MPV(ao='null', video=False, audio_display='no', config=False,
                             terminal=False, input_default_bindings=False,
                             input_vo_keyboard=False, log_file=str(log), **options)
        engine.terminate()
        text = log.read_text(encoding='utf-8', errors='replace')
        return [line for line in text.splitlines() if 'Loading lua script' in line]

    complete = {option: False for option in native._LUA_SCRIPTS}
    assert not loaded_lua_scripts(complete)
    if sys.platform != 'win32':
        # Starting builtin scripts is the exact crash this fix prevents, so the
        # negative case only runs where LuaJIT SEH cannot escape into Python.
        assert loaded_lua_scripts(dict(osc=False, ytdl=False, load_scripts=False))


@pytest.mark.integration
def test_repeated_real_player_lifecycle_in_subprocess(tmp_path):
    """Keep SEH reporting enabled and make native aborts/timeouts fail pytest."""
    program = textwrap.dedent('''\
        from pathlib import Path
        import sys
        import time
        import wave
        from PySide6.QtWidgets import QApplication
        from auralume.player import MpvPlayer

        app = QApplication([])
        root = Path(sys.argv[1])
        paths = [root / f'música de teste {index}.wav' for index in (1, 2)]
        for path in paths:
            with wave.open(str(path), 'wb') as audio:
                audio.setnchannels(1)
                audio.setsampwidth(2)
                audio.setframerate(8000)
                audio.writeframes(b'\\x00\\x00' * 800)
        for cycle in range(12):
            player = MpvPlayer(audio_output='null')
            loaded, ended, errors = [], [], []
            player.loaded.connect(loaded.append)
            player.ended.connect(ended.append)
            player.error.connect(errors.append)
            try:
                assert player.available, player.initialization_error
                thread = player._engine._event_thread
                for index, path in enumerate(paths, start=1):
                    player.load(str(path))
                    deadline = time.monotonic() + 5
                    while len(ended) < index and time.monotonic() < deadline:
                        app.processEvents()
                        time.sleep(.005)
                    assert len(ended) == index, (cycle, ended, errors)
                assert loaded == ended == list(map(str, paths)), (loaded, ended)
                assert not errors, errors
            finally:
                player.close()
                player.close()
            assert not thread.is_alive(), cycle
            app.processEvents()
            print(f'cycle {cycle + 1}: loaded=2 eof=2 thread=closed', flush=True)
    ''')
    result = subprocess.run(
        [sys.executable, '-X', 'faulthandler', '-c', program, str(tmp_path)],
        env={**os.environ, 'QT_QPA_PLATFORM': 'offscreen', 'PYTHONUTF8': '1'},
        capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60,
    )
    evidence = result.stdout + '\n' + result.stderr
    assert result.returncode == 0, evidence
    assert 'cycle 12: loaded=2 eof=2 thread=closed' in result.stdout, evidence
    assert '0xe24c4a02' not in result.stderr.lower(), evidence
    assert 'access violation' not in result.stderr.lower(), evidence
