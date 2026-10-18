"""Stability-focused real-engine tests for the native mpv integration.

These complement test_player.py (basic lifecycle) and test_mpv_scripts.py (the
Lua-isolation guarantee) by exercising the port under conditions that stress
the engine's event thread, error recovery, and resource teardown.
"""
from pathlib import Path
import time
import wave

import pytest
from PySide6.QtWidgets import QApplication

from auralume.player import MpvPlayer, PlaybackError


def wait_until(app, predicate, timeout=5):
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(.01)
    assert predicate(), 'Audio event did not arrive'


def make_wav(path: Path, seconds: float = 3.0, rate: int = 8000) -> None:
    with wave.open(str(path), 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(b'\x00\x00' * int(rate * seconds))


@pytest.fixture
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def tone(tmp_path):
    path = tmp_path / 'tone.wav'
    make_wav(path, seconds=3.0)
    return path


@pytest.fixture
def player(app):
    instance = MpvPlayer(audio_output='null')
    assert instance.available, instance.initialization_error
    yield instance
    instance.close()


@pytest.mark.integration
def test_two_engines_can_live_simultaneously(app, tmp_path):
    first_path = tmp_path / 'first.wav'
    second_path = tmp_path / 'second.wav'
    make_wav(first_path)
    make_wav(second_path)

    first = MpvPlayer(audio_output='null')
    second = MpvPlayer(audio_output='null')
    events = {'first': [], 'second': [], 'errors': []}
    first.loaded.connect(events['first'].append)
    second.loaded.connect(events['second'].append)
    first.error.connect(events['errors'].append)
    second.error.connect(events['errors'].append)
    try:
        first.load(str(first_path))
        second.load(str(second_path))
        wait_until(app, lambda: len(events['first']) == 1 and len(events['second']) == 1)
        assert events['first'] == [str(first_path)]
        assert events['second'] == [str(second_path)]
        assert not events['errors'], events['errors']
    finally:
        first.close()
        second.close()


@pytest.mark.integration
def test_load_error_does_not_break_the_engine(app, tone):
    loaded, errors = [], []
    player = MpvPlayer(audio_output='null')
    player.loaded.connect(loaded.append)
    player.error.connect(errors.append)
    try:
        with pytest.raises(PlaybackError):
            player.load(str(tone.parent / 'missing.wav'))
        player.load(str(tone))
        wait_until(app, lambda: bool(loaded))
        assert loaded == [str(tone)]
        assert not errors, errors
    finally:
        player.close()


@pytest.mark.integration
def test_non_audio_file_is_isolated_and_engine_survives(app, tmp_path, tone):
    junk = tmp_path / 'not-audio.txt'
    junk.write_text('this is not audio', encoding='utf-8')

    loaded, errors = [], []
    player = MpvPlayer(audio_output='null')
    player.loaded.connect(loaded.append)
    player.error.connect(errors.append)
    try:
        # A non-audio file is not rejected up front; mpv reports it as a playback
        # error and the engine must stay usable for the next load.
        player.load(str(junk))
        wait_until(app, lambda: bool(errors))
        assert loaded == []
        player.stop()
        player.load(str(tone))
        wait_until(app, lambda: bool(loaded))
        assert loaded == [str(tone)]
        assert len(errors) == 1, errors
    finally:
        player.close()


@pytest.mark.integration
def test_back_to_back_loads_without_waiting_for_eof(app, tmp_path):
    paths = []
    for index in range(3):
        path = tmp_path / f'track-{index}.wav'
        make_wav(path, seconds=1.0)
        paths.append(str(path))

    loaded, ended, errors = [], [], []
    player = MpvPlayer(audio_output='null')
    player.loaded.connect(loaded.append)
    player.ended.connect(ended.append)
    player.error.connect(errors.append)
    try:
        for path in paths:
            player.load(path)
            wait_until(app, lambda path=path: loaded.count(path) == 1)
        assert loaded == paths
        assert not errors, errors
        wait_until(app, lambda: len(ended) == 1)
        assert ended == [paths[-1]]
    finally:
        player.close()


@pytest.mark.integration
def test_repeated_in_process_lifecycle(app, tone):
    for cycle in range(5):
        player = MpvPlayer(audio_output='null')
        assert player.available, player.initialization_error
        thread = player._engine._event_thread
        loaded, errors = [], []
        player.loaded.connect(loaded.append)
        player.error.connect(errors.append)
        try:
            player.load(str(tone))
            wait_until(app, lambda: bool(loaded))
            assert loaded == [str(tone)]
            assert not errors, errors
        finally:
            player.close()
            player.close()
        assert not thread.is_alive(), f'event thread survived cycle {cycle + 1}'
        app.processEvents()


@pytest.mark.integration
def test_seek_and_pause_during_playback(app, tmp_path):
    long_tone = tmp_path / 'long-tone.wav'
    make_wav(long_tone, seconds=6.0)

    loaded, ended, errors = [], [], []
    player = MpvPlayer(audio_output='null')
    player.loaded.connect(loaded.append)
    player.ended.connect(ended.append)
    player.error.connect(errors.append)
    try:
        player.load(str(long_tone))
        wait_until(app, lambda: bool(loaded))
        player.seek(1.0)
        player.seek(4.5)
        player.toggle_pause()
        assert player.paused
        player.toggle_pause()
        wait_until(app, lambda: bool(ended))
        assert ended == [str(long_tone)]
        assert not errors, errors
    finally:
        player.close()


@pytest.mark.integration
def test_close_without_playing(app):
    player = MpvPlayer(audio_output='null')
    assert player.available, player.initialization_error
    player.close()
    player.close()
