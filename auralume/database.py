"""Thread-safe local SQLite repository; no external account or backend."""
from contextlib import contextmanager
from dataclasses import asdict
import json
from pathlib import Path
import sqlite3
from threading import RLock
from uuid import uuid4

from .models import Playlist, Track, normalized


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._db = sqlite3.connect(str(self.path), timeout=10, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.create_function('normalize', 1, normalized, deterministic=True)
        self._db.execute('PRAGMA foreign_keys=ON')
        self._db.execute('PRAGMA journal_mode=WAL')
        self._db.executescript('''
            CREATE TABLE IF NOT EXISTS tracks (
                id TEXT PRIMARY KEY, source TEXT NOT NULL UNIQUE, title TEXT NOT NULL,
                artist TEXT NOT NULL, album TEXT NOT NULL DEFAULT '',
                duration REAL NOT NULL DEFAULT 0, genre TEXT NOT NULL DEFAULT '',
                artwork TEXT NOT NULL DEFAULT '', is_remote INTEGER NOT NULL DEFAULT 0,
                favorite INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS playlists (id TEXT PRIMARY KEY, name TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS playlist_tracks (
                playlist_id TEXT NOT NULL REFERENCES playlists(id) ON DELETE CASCADE,
                track_id TEXT NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
                position INTEGER NOT NULL,
                PRIMARY KEY (playlist_id, track_id)
            );
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                track_id TEXT NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
                played_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
            );
            CREATE INDEX IF NOT EXISTS history_track ON history(track_id);
            CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT, term TEXT NOT NULL
            );
            PRAGMA user_version=1;
        ''')
        self._db.commit()

    @contextmanager
    def _transaction(self):
        with self._lock, self._db:
            yield self._db

    @staticmethod
    def _track(row) -> Track:
        data = dict(row)
        data['favorite'] = bool(data['favorite'])
        data['is_remote'] = bool(data['is_remote'])
        return Track(**data)

    def upsert_track(self, track: Track) -> None:
        self.upsert_tracks([track])

    def upsert_tracks(self, tracks: list[Track]) -> None:
        with self._transaction() as db:
            db.executemany('''
                INSERT INTO tracks VALUES (:id,:source,:title,:artist,:album,:duration,
                    :genre,:artwork,:is_remote,:favorite)
                ON CONFLICT(id) DO UPDATE SET source=excluded.source,title=excluded.title,
                    artist=excluded.artist,album=excluded.album,duration=excluded.duration,
                    genre=excluded.genre,artwork=excluded.artwork,is_remote=excluded.is_remote
            ''', [asdict(track) for track in tracks])

    def get_track(self, track_id: str) -> Track | None:
        with self._lock:
            row = self._db.execute('SELECT * FROM tracks WHERE id=?', (track_id,)).fetchone()
            return self._track(row) if row else None

    def list_tracks(self, query: str = '', favorites: bool = False) -> list[Track]:
        term = normalized(query.strip())
        with self._lock:
            rows = self._db.execute('''
                SELECT * FROM tracks WHERE (?=0 OR favorite=1)
                AND instr(normalize(title || ' ' || artist || ' ' || album || ' ' || genre), ?) > 0
                ORDER BY normalize(artist), normalize(title), id
            ''', (int(favorites), term)).fetchall()
            return [self._track(row) for row in rows]

    def toggle_favorite(self, track_id: str) -> bool:
        with self._transaction() as db:
            row = db.execute('SELECT favorite FROM tracks WHERE id=?', (track_id,)).fetchone()
            if row is None:
                raise KeyError(track_id)
            favorite = not row['favorite']
            db.execute('UPDATE tracks SET favorite=? WHERE id=?', (favorite, track_id))
            return favorite

    def create_playlist(self, name: str) -> Playlist:
        name = name.strip()
        if not name:
            raise ValueError('Dê um nome à playlist.')
        playlist = Playlist(uuid4().hex, name[:150])
        with self._transaction() as db:
            db.execute('INSERT INTO playlists VALUES (?,?)', (playlist.id, playlist.name))
        return playlist

    def list_playlists(self) -> list[Playlist]:
        with self._lock:
            rows = self._db.execute('''SELECT p.id,p.name,count(pt.track_id) AS track_count
                FROM playlists p LEFT JOIN playlist_tracks pt ON pt.playlist_id=p.id
                GROUP BY p.id ORDER BY normalize(p.name)''').fetchall()
            return [Playlist(**dict(row)) for row in rows]

    def add_to_playlist(self, playlist_id: str, track_id: str) -> None:
        with self._transaction() as db:
            db.execute('''INSERT OR IGNORE INTO playlist_tracks
                SELECT ?,?,COALESCE(MAX(position),-1)+1 FROM playlist_tracks WHERE playlist_id=?
            ''', (playlist_id, track_id, playlist_id))

    def playlist_tracks(self, playlist_id: str) -> list[Track]:
        with self._lock:
            rows = self._db.execute('''SELECT t.* FROM tracks t JOIN playlist_tracks pt
                ON pt.track_id=t.id WHERE pt.playlist_id=? ORDER BY pt.position
            ''', (playlist_id,)).fetchall()
            return [self._track(row) for row in rows]

    def remove_from_playlist(self, playlist_id: str, track_id: str) -> None:
        with self._transaction() as db:
            db.execute('DELETE FROM playlist_tracks WHERE playlist_id=? AND track_id=?',
                       (playlist_id, track_id))

    def delete_playlist(self, playlist_id: str) -> None:
        with self._transaction() as db:
            db.execute('DELETE FROM playlists WHERE id=?', (playlist_id,))

    def record_play(self, track_id: str) -> None:
        with self._transaction() as db:
            db.execute('INSERT INTO history(track_id) VALUES (?)', (track_id,))

    def history(self, limit: int = 100) -> list[Track]:
        with self._lock:
            rows = self._db.execute('''SELECT t.* FROM tracks t JOIN
                (SELECT track_id,MAX(id) AS last_id FROM history GROUP BY track_id) h
                ON h.track_id=t.id ORDER BY h.last_id DESC LIMIT ?''', (max(0, limit),)).fetchall()
            return [self._track(row) for row in rows]

    def play_counts(self) -> dict[str, int]:
        with self._lock:
            return dict(self._db.execute('SELECT track_id,COUNT(*) FROM history GROUP BY track_id'))

    def set_setting(self, key: str, value) -> None:
        with self._transaction() as db:
            db.execute('INSERT INTO settings VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',
                       (key, json.dumps(value, ensure_ascii=False)))

    def get_setting(self, key: str, default=None):
        with self._lock:
            row = self._db.execute('SELECT value FROM settings WHERE key=?', (key,)).fetchone()
            return json.loads(row[0]) if row else default

    def record_search(self, term: str) -> None:
        if term.strip():
            with self._transaction() as db:
                db.execute('INSERT INTO searches(term) VALUES (?)', (term.strip()[:200],))
                db.execute('DELETE FROM searches WHERE id NOT IN (SELECT id FROM searches ORDER BY id DESC LIMIT 100)')

    def recent_searches(self) -> list[str]:
        with self._lock:
            return [row[0] for row in self._db.execute('SELECT term FROM searches ORDER BY id DESC LIMIT 10')]

    def close(self) -> None:
        with self._lock:
            self._db.close()
