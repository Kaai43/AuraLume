from dataclasses import replace

import pytest

from auralume.database import Database
from auralume.models import Track


@pytest.fixture
def db(tmp_path):
    database = Database(tmp_path / 'library.sqlite3')
    yield database
    database.close()


def test_reimport_preserves_favorite_and_survives_restart(tmp_path):
    path = tmp_path / 'library.sqlite3'
    db = Database(path)
    track = Track('a', '/a.wav', 'Canção', artist='João')
    db.upsert_track(track)
    assert db.toggle_favorite('a') is True
    db.upsert_track(replace(track, title='Canção remasterizada'))
    db.close()
    db = Database(path)
    assert len(db.list_tracks()) == 1
    assert db.list_tracks(favorites=True)[0].title == 'Canção remasterizada'
    assert db.list_tracks(query='joao')[0].id == 'a'
    assert db.list_tracks(query="' OR 1=1 --") == []
    db.close()


def test_playlist_order_duplicates_removal_and_cascade(db):
    for key in ('a', 'b'):
        db.upsert_track(Track(key, f'/{key}.wav', key))
    playlist = db.create_playlist('Viagem')
    db.add_to_playlist(playlist.id, 'b')
    db.add_to_playlist(playlist.id, 'a')
    db.add_to_playlist(playlist.id, 'b')
    assert [t.id for t in db.playlist_tracks(playlist.id)] == ['b', 'a']
    assert db.list_playlists()[0].track_count == 2
    db.remove_from_playlist(playlist.id, 'b')
    assert [t.id for t in db.playlist_tracks(playlist.id)] == ['a']
    db.delete_playlist(playlist.id)
    assert db.list_playlists() == []
    assert len(db.list_tracks()) == 2


def test_history_and_settings_are_local_and_persistent(db):
    db.upsert_track(Track('a', '/a.wav', 'A'))
    db.upsert_track(Track('b', '/b.wav', 'B'))
    db.record_play('a')
    db.record_play('b')
    db.record_play('a')
    assert [t.id for t in db.history()] == ['a', 'b']
    assert db.play_counts() == {'a': 2, 'b': 1}
    db.set_setting('preferences', ['jazz', 'piano'])
    assert db.get_setting('preferences', []) == ['jazz', 'piano']
    assert db.get_setting('volume', 70) == 70
    db.record_search('piano')
    assert db.recent_searches() == ['piano']


def test_empty_playlist_name_and_unknown_favorite_rejected(db):
    with pytest.raises(ValueError):
        db.create_playlist('   ')
    with pytest.raises(KeyError):
        db.toggle_favorite('missing')
