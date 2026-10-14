"""Value objects shared by services and UI."""
from dataclasses import dataclass
import hashlib
import unicodedata


def normalized(text: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD', text.casefold())
                   if not unicodedata.combining(c))


def source_id(source: str) -> str:
    return hashlib.sha256(source.encode('utf-8')).hexdigest()[:24]


@dataclass(frozen=True)
class Track:
    id: str
    source: str
    title: str
    artist: str = 'Artista desconhecido'
    album: str = ''
    duration: float = 0.0
    genre: str = ''
    artwork: str = ''
    is_remote: bool = False
    favorite: bool = False


@dataclass(frozen=True)
class Playlist:
    id: str
    name: str
    track_count: int = 0
