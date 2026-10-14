import time
import wave

from auralume.controller import Controller
from auralume.database import Database
from auralume.models import Track
from auralume.player import MpvPlayer
from auralume.ui.main_window import MainWindow


def wait_for(app, predicate):
    deadline = time.monotonic() + 6
    while not predicate() and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(.01)
    assert predicate()


def test_import_favorite_playlist_play_and_history_through_ui(tmp_path, qt_application):
    path = tmp_path / 'Lume - Dia.wav'
    with wave.open(str(path), 'wb') as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8000)
        audio.writeframes(b'\x00\x00' * 24000)
    db = Database(tmp_path / 'library.sqlite3')
    window = MainWindow()
    player = MpvPlayer(audio_output='null')
    controller = Controller(window, db, player)
    try:
        controller.import_paths([path])
        wait_for(qt_application, lambda: len(db.list_tracks()) == 1)
        track = db.list_tracks()[0]
        window.favorite_requested.emit(track.id)
        assert db.list_tracks(favorites=True)[0].id == track.id
        window.playlist_create_requested.emit('Minha lista')
        playlist = db.list_playlists()[0]
        window.playlist_add_requested.emit(playlist.id, track.id)
        assert db.playlist_tracks(playlist.id)[0].id == track.id
        window.navigate.emit('library')
        window.play_requested.emit(track.id)
        wait_for(qt_application, lambda: bool(db.history()))
        assert db.history()[0].id == track.id
        assert window.now_title.text() == 'Dia'
        window.play_pause_requested.emit()
        assert player.paused
        window.preferences_requested.emit('jazz, piano, jazz')
        assert db.get_setting('preferences') == ['jazz', 'piano']
        window.navigate.emit('favorites')
        assert window.current_page == 'favorites'
        assert window.track_table.rowCount() == 1
    finally:
        controller.close()
        window.close()
        db.close()


def test_failed_playback_does_not_record_history(tmp_path, qt_application):
    db = Database(tmp_path / 'library.sqlite3')
    db.upsert_track(Track('missing', str(tmp_path / 'gone.wav'), 'Ausente'))
    window = MainWindow()
    controller = Controller(window, db, MpvPlayer(audio_output='null'))
    try:
        controller.play('missing')
        qt_application.processEvents()
        assert db.history() == []
        assert window.status_label.property('error') is True
        assert not controller.playing
    finally:
        controller.close()
        window.close()
        db.close()


def test_queue_advances_after_real_eof_and_stops_at_end(tmp_path, qt_application):
    for number in (1, 2):
        with wave.open(str(tmp_path / f'{number}.wav'), 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(8000)
            wav.writeframes(b'\x00\x00' * 1600)
    db = Database(tmp_path / 'data.sqlite3')
    window = MainWindow()
    controller = Controller(window, db, MpvPlayer(audio_output='null'))
    try:
        controller.import_paths([tmp_path], autoplay=True)
        wait_for(qt_application, lambda: len(db.history()) == 2 and not controller.playing)
        assert [t.title for t in db.history()] == ['2', '1']
        assert window.play_button.text() == '▶'
    finally:
        controller.close()
        window.close()
        db.close()


def test_stale_network_result_cannot_replace_new_local_playback(tmp_path, qt_application):
    from threading import Event
    from auralume.sources import ResolvedSource
    entered, release = Event(), Event()
    remote = Track('remote', 'https://example.com/music', 'Remote', is_remote=True)

    class SlowSource:
        def resolve(self, url, authorized):
            entered.set()
            release.wait(5)
            return ResolvedSource(remote, 'https://example.com/audio.wav', {})

    path = tmp_path / 'local.wav'
    with wave.open(str(path), 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(8000)
        wav.writeframes(b'\x00\x00' * 24000)
    db = Database(tmp_path / 'data.sqlite3')
    db.upsert_track(Track('local', str(path), 'Local'))
    window = MainWindow()
    controller = Controller(window, db, MpvPlayer(audio_output='null'), SlowSource())
    try:
        controller.open_source(remote.source)
        wait_for(qt_application, entered.is_set)
        controller.play('local')
        wait_for(qt_application, lambda: bool(db.history()))
        release.set()
        wait_for(qt_application, lambda: controller._busy == 0)
        assert controller.current_track.id == 'local'
        assert db.get_track('remote') is None
        assert [t.id for t in db.history()] == ['local']
    finally:
        release.set()
        controller.close()
        window.close()
        db.close()


def test_closing_during_network_work_drops_late_result(tmp_path, qt_application):
    from threading import Event
    from auralume.sources import ResolvedSource
    entered, release, finished = Event(), Event(), Event()

    class SlowSource:
        def resolve(self, url, authorized):
            entered.set()
            release.wait(5)
            finished.set()
            return ResolvedSource(Track('r', url, 'Remote', is_remote=True), url, {})

    db = Database(tmp_path / 'data.sqlite3')
    window = MainWindow()
    controller = Controller(window, db, MpvPlayer(audio_output='null'), SlowSource())
    try:
        controller.open_source('https://example.com/music')
        wait_for(qt_application, entered.is_set)
        controller.close()
        release.set()
        wait_for(qt_application, finished.is_set)
        qt_application.processEvents()
        assert db.list_tracks() == []
    finally:
        release.set()
        controller.close()
        window.close()
        db.close()
