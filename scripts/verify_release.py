#!/usr/bin/env python3
"""Exercise the actual ELF in a relocated directory with original test audio.

Needs FFmpeg on the test host and permission for a loopback HTTP server.
Does not access the internet or modify the installed user's library.
"""
import argparse
from contextlib import closing
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import math
import os
from pathlib import Path
import shutil
import sqlite3
import struct
import subprocess
import tempfile
from threading import Thread
import wave


def invoke(binary, *arguments):
    result = subprocess.run([str(binary), *map(str, arguments)], text=True, capture_output=True,
                            timeout=25, env={**os.environ, 'QT_QPA_PLATFORM': 'offscreen', 'PYTHONPATH': ''},
                            cwd=binary.parent)
    if result.returncode:
        raise RuntimeError(f'Exit {result.returncode}: {result.stdout}\n{result.stderr}')
    return json.loads(result.stdout)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('binary', nargs='?', type=Path, default=Path('dist/Auralume/Auralume'))
    parser.add_argument('--screenshot', type=Path, default=Path('docs/evidence/player.png'))
    args = parser.parse_args()
    binary = args.binary.resolve()
    screenshot = args.screenshot.resolve()
    with tempfile.TemporaryDirectory(prefix='auralume-release-') as directory:
        root = Path(directory)
        # A different directory (including spaces) catches absolute build paths.
        relocated = root / 'Portable Player'
        shutil.copytree(binary.parent, relocated)
        binary = relocated / 'Auralume'
        assert not (relocated / '_internal/libmpv.so.2').exists()
        report = {'environment': invoke(binary, '--diagnostics'), 'checks': {}}
        assert report['environment']['frozen'] is True
        wav_path = root / 'Lume - Aurora.wav'
        with wave.open(str(wav_path), 'wb') as audio:
            audio.setparams((1, 2, 22050, 0, 'NONE', 'not compressed'))
            audio.writeframes(b''.join(struct.pack('<h', int(1000 * math.sin(2 * math.pi * 220 * i / 22050)))
                                      for i in range(22050 * 3)))
        paths = [wav_path]
        for extension in ('mp3', 'flac'):
            path = root / f'Aurora.{extension}'
            subprocess.run(['ffmpeg', '-v', 'error', '-i', str(wav_path), '-metadata', 'title=Aurora',
                            '-metadata', 'artist=Lume', '-metadata', 'album=Primeira luz',
                            '-metadata', 'genre=Ambient', str(path)], check=True, timeout=15)
            paths.append(path)
        for path in paths:
            data_dir = root / f'data-{path.suffix[1:]}'
            arguments = ['--smoke-test', '--play', '--data-dir', data_dir, path]
            if path.suffix == '.mp3':
                arguments += ['--screenshot', screenshot]
            state = invoke(binary, *arguments)
            assert state['ok'] and state['tracks'] == 1 and state['history'] == 1 and state['playback_started']
            report['checks'][path.suffix[1:]] = state
            with closing(sqlite3.connect(data_dir / 'library.sqlite3')) as db:
                assert db.execute('SELECT title FROM tracks').fetchone()[0] == 'Aurora'
        class Handler(SimpleHTTPRequestHandler):
            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Handler, directory=str(root)))
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f'http://127.0.0.1:{server.server_port}/Aurora.mp3'
            data_dir = root / 'data-http'
            state = invoke(binary, '--smoke-test', '--data-dir', data_dir, '--authorized-source', url)
            assert state['ok'] and state['history'] == 1 and state['playback_started']
            with closing(sqlite3.connect(data_dir / 'library.sqlite3')) as db:
                assert db.execute('SELECT source,is_remote FROM tracks').fetchone() == (url, 1)
            assert {p.name for p in data_dir.iterdir()} <= {
                'library.sqlite3', 'library.sqlite3-wal', 'library.sqlite3-shm', 'auralume.log'}
            report['checks']['yt_dlp_http_playback'] = state
        finally:
            server.shutdown()
            thread.join(timeout=2)
            server.server_close()
        report['relocation'] = 'passed'
        report['physical_audio'] = 'not checked; ao=null'
        print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
