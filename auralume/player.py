"""libmpv adapter. Its event thread only emits Qt signals; widgets stay on Qt."""
from pathlib import Path
from urllib.parse import urlsplit

from PySide6.QtCore import QObject, Signal


class PlaybackError(RuntimeError):
    pass


class MpvPlayer(QObject):
    loaded = Signal(str)
    ended = Signal(str)
    error = Signal(str)

    def __init__(self, audio_output: str | None = None, parent=None):
        super().__init__(parent)
        self._engine = None
        self._closed = False
        self._active_url = ''
        self.initialization_error = ''
        try:
            import mpv
            options = dict(video=False, audio_display='no', ytdl=False, input_default_bindings=False,
                           input_vo_keyboard=False, osc=False, config=False, terminal=False,
                           keep_open=False, idle=True, volume=70, network_timeout=15)
            if audio_output:
                options['ao'] = audio_output
            self._engine = mpv.MPV(**options)

            @self._engine.event_callback('file-loaded')
            def on_loaded(event):
                if not self._closed:
                    self._active_url = str(self._engine.path or '')
                    self.loaded.emit(self._active_url)

            @self._engine.event_callback('end-file')
            def on_ended(event):
                if self._closed:
                    return
                if event.data.reason == mpv.MpvEventEndFile.EOF:
                    self.ended.emit(self._active_url)
                elif event.data.reason == mpv.MpvEventEndFile.ERROR:
                    self.error.emit('Falha ao reproduzir áudio. Confira o arquivo ou abra a origem.')
        except (ImportError, OSError, RuntimeError, AttributeError) as error:
            self.initialization_error = f'Player indisponível: instale libmpv2. ({type(error).__name__})'

    @property
    def available(self) -> bool:
        return self._engine is not None and not self._closed

    def _property(self, name, default):
        if not self.available:
            return default
        try:
            value = getattr(self._engine, name)
            return default if value is None else value
        except (AttributeError, RuntimeError):
            return default

    @property
    def paused(self) -> bool:
        return bool(self._property('pause', False))

    @property
    def position(self) -> float:
        return float(self._property('time_pos', 0))

    @property
    def duration(self) -> float:
        return float(self._property('duration', 0))

    @property
    def volume(self) -> int:
        return round(self._property('volume', 70))

    def load(self, source: str, headers: dict[str, str] | None = None) -> None:
        if not self.available:
            raise PlaybackError(self.initialization_error or 'Player encerrado.')
        if urlsplit(source).scheme not in ('http', 'https') and not Path(source).is_file():
            raise PlaybackError('Arquivo não encontrado. Importe-o novamente da localização atual.')
        self._engine.http_header_fields = [f'{key}: {value}' for key, value in (headers or {}).items()]
        self._engine.pause = False
        self._engine.play(source)

    def toggle_pause(self) -> None:
        if self.available:
            self._engine.pause = not self._engine.pause

    def seek(self, seconds: float) -> None:
        if self.available and self.duration:
            self._engine.seek(max(0, min(seconds, self.duration)), 'absolute', 'exact')

    def set_volume(self, volume: int) -> None:
        if self.available:
            self._engine.volume = max(0, min(int(volume), 100))

    def stop(self) -> None:
        if self.available:
            self._engine.stop()

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            if self._engine:
                self._engine.terminate()
