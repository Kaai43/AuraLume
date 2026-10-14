from auralume.database import Database
from auralume.models import Track
from auralume.recommendations import recommend


def test_cold_start_uses_preferences_and_varies_artists(tmp_path):
    db = Database(tmp_path / 'data.sqlite3')
    for key, artist, genre in [('a', 'Piano', 'Jazz'), ('b', 'Piano', 'Jazz'), ('c', 'Trio', 'Jazz'), ('d', 'Rock', 'Rock')]:
        db.upsert_track(Track(key, '/' + key, key, artist=artist, genre=genre))
    db.set_setting('preferences', ['jazz'])
    result = recommend(db)
    assert result[0].genre == 'Jazz'
    assert result[0].artist != result[1].artist
    assert len({t.id for t in result}) == 4
    db.close()


def test_favorites_and_history_inform_recommendations(tmp_path):
    db = Database(tmp_path / 'data.sqlite3')
    for key, artist in [('a', 'Lume'), ('b', 'Lume'), ('c', 'Outro')]:
        db.upsert_track(Track(key, '/' + key, key, artist=artist))
    db.toggle_favorite('a')
    db.record_play('a')
    assert recommend(db, limit=1)[0].artist == 'Lume'
    assert recommend(db, limit=0) == []
    db.close()
