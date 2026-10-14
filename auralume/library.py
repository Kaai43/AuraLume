"""Local discovery and metadata extraction, executed away from the UI thread."""
from dataclasses import dataclass, field
from pathlib import Path
import math

import mutagen

from .models import Track, source_id

EXTENSIONS = {'.mp3', '.flac', '.ogg', '.opus', '.wav', '.m4a', '.aac', '.wma', '.aiff', '.aif', '.ape'}


@dataclass
class ImportResult:
    tracks: list[Track] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def read_track(path: Path) -> Track:
    path = path.expanduser().resolve()
    if not path.is_file():
        raise ValueError('Arquivo não encontrado')
    audio = mutagen.File(path, easy=True)
    if audio is None or not getattr(audio, 'info', None):
        raise ValueError('Formato de áudio inválido ou não reconhecido')

    def tag(name: str, default: str = '') -> str:
        values = audio.get(name, [])
        return str(values[0]) if values else default

    artist, title = ('Artista desconhecido', path.stem)
    if ' - ' in path.stem:
        artist, title = path.stem.split(' - ', 1)
    duration = float(getattr(audio.info, 'length', 0) or 0)
    if not math.isfinite(duration):
        duration = 0
    artwork = next((str(path.parent / name) for name in ('cover.jpg', 'cover.png', 'folder.jpg', 'folder.png')
                    if (path.parent / name).is_file()), '')
    return Track(source_id(str(path)), str(path), tag('title', title),
                 tag('artist', artist), tag('album'), max(0, duration), tag('genre'), artwork)


def scan_paths(paths) -> ImportResult:
    result = ImportResult()
    seen: set[Path] = set()
    for supplied in paths:
        root = Path(supplied).expanduser()
        if not root.exists():
            result.errors.append(f'{root.name}: arquivo não encontrado')
            continue
        try:
            candidates = sorted(root.rglob('*'), key=lambda p: str(p).casefold()) if root.is_dir() else [root]
            for candidate in candidates:
                if candidate.suffix.lower() not in EXTENSIONS or not candidate.is_file():
                    continue
                path = candidate.resolve()
                if path in seen:
                    continue
                seen.add(path)
                try:
                    result.tracks.append(read_track(path))
                except (OSError, ValueError, mutagen.MutagenError) as error:
                    result.errors.append(f'{candidate.name}: {error}')
        except OSError as error:
            result.errors.append(f'{root.name}: {error}')
    return result
