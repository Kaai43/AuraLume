"""Authorized, transient streaming through the documented yt-dlp Python API."""
from dataclasses import dataclass
import math
from urllib.parse import urlsplit

from .models import Track, source_id


class SourceError(ValueError):
    pass


@dataclass(frozen=True)
class ResolvedSource:
    track: Track
    url: str
    headers: dict[str, str]


def validate_url(url: str) -> str:
    url = url.strip()
    try:
        parts = urlsplit(url)
        if parts.scheme not in ('http', 'https') or not parts.hostname or parts.username or parts.password:
            raise ValueError
        if any(ord(c) < 32 for c in url):
            raise ValueError
        _ = parts.port
    except (ValueError, AttributeError):
        raise SourceError('Informe uma URL HTTP/HTTPS válida, sem credenciais.') from None
    return url


def parse_info(info: dict, origin: str) -> ResolvedSource:
    if not isinstance(info, dict) or info.get('_type') in ('playlist', 'multi_video'):
        raise SourceError('Escolha uma faixa individual na origem.')
    if info.get('has_drm') or info.get('availability') in ('private', 'premium_only', 'subscriber_only', 'needs_auth'):
        raise SourceError('Conteúdo protegido ou restrito. Abra o conteúdo na origem.')
    stream = info.get('url')
    title = info.get('title')
    if not isinstance(stream, str) or not isinstance(title, str) or not title.strip():
        raise SourceError('A origem não forneceu áudio ou metadados utilizáveis.')
    stream = validate_url(stream)
    origin = validate_url(origin)
    try:
        duration = float(info.get('duration') or 0)
        if not math.isfinite(duration):
            duration = 0
    except (TypeError, ValueError):
        duration = 0
    headers = {str(key): str(value) for key, value in (info.get('http_headers') or {}).items()
               if key.lower() in ('user-agent', 'referer', 'origin')
               and '\r' not in str(value) and '\n' not in str(value)}
    track = Track(source_id(origin), origin, title.strip(),
                  str(info.get('artist') or info.get('uploader') or info.get('channel') or 'Artista desconhecido'),
                  str(info.get('album') or ''), max(0, duration), str(info.get('genre') or ''),
                  str(info.get('thumbnail') or ''), is_remote=True)
    return ResolvedSource(track, stream, headers)


class _QuietLogger:
    # The UI presents a bounded error. Extractor messages may contain temporary URLs.
    def debug(self, message):
        pass

    def warning(self, message):
        pass

    def error(self, message):
        pass


class SourceService:
    def __init__(self, ydl_factory=None):
        self._factory = ydl_factory

    def resolve(self, url: str, authorized: bool = False) -> ResolvedSource:
        if not authorized:
            raise SourceError('Confirme que tem autorização para reproduzir este conteúdo.')
        url = validate_url(url)
        if self._factory is None:
            from yt_dlp import YoutubeDL
            factory = YoutubeDL
        else:
            factory = self._factory
        options = {
            'format': 'bestaudio/best', 'noplaylist': True, 'skip_download': True,
            'quiet': True, 'no_warnings': True, 'logger': _QuietLogger(),
            'socket_timeout': 12, 'retries': 1, 'extractor_retries': 1,
            'cachedir': False, 'allow_unplayable_formats': False,
            'usenetrc': False, 'cookiefile': None, 'cookiesfrombrowser': None,
        }
        try:
            with factory(options) as ydl:
                info = ydl.extract_info(url, download=False)
            return parse_info(info, url)
        except SourceError:
            raise
        except Exception as error:
            # Network/extractor failures are recoverable, and never saved as library tracks.
            raise SourceError('Não foi possível obter áudio. Verifique a rede ou abra o conteúdo na origem.') from error
