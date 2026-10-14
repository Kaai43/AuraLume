"""Real yt-dlp integration against an ephemeral, authorized loopback source."""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
import threading
import wave

import pytest

from auralume.sources import SourceService


def make_wav() -> bytes:
    buffer = BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(8_000)
        wav.writeframes(b"\x00\x00" * 800)
    return buffer.getvalue()


@pytest.fixture
def wav_server():
    payload = make_wav()
    requests: list[str] = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            pass

        def do_HEAD(self):
            self._serve(send_body=False)

        def do_GET(self):
            self._serve(send_body=True)

        def _serve(self, send_body: bool):
            requests.append(self.path)
            if self.path == "/origin":
                self.send_response(302)
                self.send_header("Location", "/media/sample.wav")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            if self.path != "/media/sample.wav":
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", "audio/wav")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            if send_body:
                self.wfile.write(payload)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = f"http://127.0.0.1:{server.server_port}/origin"
    try:
        yield origin, requests
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()


@pytest.mark.integration
def test_yt_dlp_resolves_loopback_audio_without_downloading_and_keeps_origin(
    wav_server, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    from urllib.request import urlopen

    origin, requests = wav_server
    monkeypatch.chdir(tmp_path)

    resolved = SourceService().resolve(origin, authorized=True)

    assert resolved.track.source == origin
    assert resolved.track.is_remote is True
    assert resolved.url == f"http://127.0.0.1:{url_port(origin)}/media/sample.wav"
    assert list(tmp_path.iterdir()) == []

    with urlopen(resolved.url, timeout=3) as stream:
        assert stream.headers.get_content_type() == "audio/wav"
        header = stream.read(12)
    assert header[:4] == b"RIFF"
    assert header[8:12] == b"WAVE"
    assert list(tmp_path.iterdir()) == []
    assert "/origin" in requests
    assert "/media/sample.wav" in requests


def url_port(url: str) -> int:
    from urllib.parse import urlsplit

    return urlsplit(url).port
