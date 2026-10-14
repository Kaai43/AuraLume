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


@pytest.mark.integration
def test_real_mpv_load_pause_seek_and_eof(tmp_path):
    app = QApplication.instance() or QApplication([])
    path = tmp_path / 'tone.wav'
    with wave.open(str(path), 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(8000)
        wav.writeframes(b'\x00\x00' * 24000)
    player = MpvPlayer(audio_output='null')
    loaded, ended, errors = [], [], []
    player.loaded.connect(loaded.append)
    player.ended.connect(ended.append)
    player.error.connect(errors.append)
    try:
        player.load(str(path))
        wait_until(app, lambda: bool(loaded))
        assert loaded == [str(path)]
        player.toggle_pause()
        assert player.paused
        player.seek(2.7)
        player.set_volume(30)
        assert player.volume == 30
        player.toggle_pause()
        wait_until(app, lambda: bool(ended))
        assert not errors
        assert ended == [str(path)]
    finally:
        player.close()


def test_missing_file_fails_without_loaded_event(tmp_path):
    app = QApplication.instance() or QApplication([])
    player = MpvPlayer(audio_output='null')
    loaded = []
    player.loaded.connect(loaded.append)
    try:
        with pytest.raises(PlaybackError):
            player.load(str(tmp_path / 'missing.wav'))
        app.processEvents()
        assert loaded == []
    finally:
        player.close()
