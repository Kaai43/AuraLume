"""Original, deterministic recommendation ranking using only local metadata."""
from collections import Counter
import math

from .models import normalized


def recommend(db, limit: int = 30):
    tracks = db.list_tracks()
    counts = db.play_counts()
    preferences = [normalized(str(p)) for p in db.get_setting('preferences', []) if str(p).strip()]
    searches = [normalized(s) for s in db.recent_searches()]
    recent = {track.id for track in db.history(5)}
    playlist_ids = {t.id for p in db.list_playlists() for t in db.playlist_tracks(p.id)}
    artists: Counter = Counter()
    genres: Counter = Counter()
    for track in tracks:
        signal = (3 if track.favorite else 0) + math.log1p(counts.get(track.id, 0))
        if track.id in playlist_ids:
            signal += 1
        artists[normalized(track.artist)] += signal
        if track.genre:
            genres[normalized(track.genre)] += signal
    scores = {}
    for track in tracks:
        metadata = normalized(f'{track.artist} {track.title} {track.album} {track.genre}')
        score = sum(6 for pref in preferences if pref in metadata)
        score += sum(1 for term in searches if term in metadata)
        score += min(artists[normalized(track.artist)], 8) + min(genres[normalized(track.genre)], 4)
        score += 2 if track.favorite else 0
        score += 1 if track.id in playlist_ids else 0
        score -= 2 if track.id in recent else 0
        score -= min(math.log1p(counts.get(track.id, 0)), 3)
        scores[track.id] = score
    # Greedy diversity reduces adjacent artist repetition without hiding any track.
    selected = []
    used_artists: Counter = Counter()
    remaining = list(tracks)
    while remaining and len(selected) < max(0, limit):
        best = max(remaining, key=lambda t: (scores[t.id] - 5 * used_artists[normalized(t.artist)], t.id))
        selected.append(best)
        used_artists[normalized(best.artist)] += 1
        remaining.remove(best)
    return selected
