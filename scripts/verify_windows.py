#!/usr/bin/env python3
"""Accept a real Windows onedir, ZIP/relocate it, and exercise the extracted EXE.

No application imports: subprocesses must use only their bundled interpreter.
This is automated ao=null validation, never evidence of audible playback.
"""
import argparse
from contextlib import closing, contextmanager
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import sqlite3
import struct
import subprocess
import sys
import tempfile
import wave
import zipfile


@contextmanager
def open_database(path):
    # Connection.__exit__ commits/rolls back but does not close Windows handles.
    with closing(sqlite3.connect(path)) as database, database:
        yield database


def inventory(directory):
    result = []
    for path in sorted(directory.rglob('*')):
        if not path.is_file():
            continue
        relative = path.relative_to(directory)
        forbidden = ('.git', '.venv', '.aws', '.codex', '.env', 'id_rsa', 'id_ed25519')
        public_ca = relative.as_posix() == '_internal/certifi/cacert.pem'
        if (path.is_symlink() or any(part in forbidden for part in relative.parts)
                or path.name.startswith('.env.')
                or (path.suffix.lower() == '.pem' and not public_ca)
                or path.suffix.lower() in {'.key', '.db', '.sqlite', '.sqlite3', '.wav', '.mp3', '.flac', '.log'}):
            raise ValueError(f'Private/development file in package: {relative}')
        with path.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        result.append({'path': relative.as_posix(), 'size': path.stat().st_size, 'sha256': digest})
    return result


def extract_package(archive, destination):
    with zipfile.ZipFile(archive) as source:
        for info in source.infolist():
            path = PurePosixPath(info.filename)
            if path.is_absolute() or '..' in path.parts or '\\' in info.filename or ':' in info.filename:
                raise ValueError(f'Unsafe ZIP member: {info.filename}')
        source.extractall(destination)


def invoke(binary, environment, cwd, *arguments, expected_code=0):
    process = subprocess.run([str(binary), *map(str, arguments)], cwd=cwd,
                             env=environment, capture_output=True, text=True,
                             encoding='utf-8', errors='replace', timeout=40)
    if process.returncode != expected_code:
        raise RuntimeError(f'{binary.name} exited {process.returncode}: {process.stdout}\n{process.stderr}')
    return json.loads(process.stdout)


def write_wav(path):
    with wave.open(str(path), 'wb') as stream:
        stream.setparams((1, 2, 22050, 0, 'NONE', 'not compressed'))
        stream.writeframes(b''.join(struct.pack('<h', int(1500 * math.sin(i * 2 * math.pi * 220 / 22050)))
                                   for i in range(22050 * 3)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, default=Path('dist/Auralume'))
    parser.add_argument('--output', type=Path, default=Path('dist/windows-candidate'))
    parser.add_argument('--revision', required=True)
    parser.add_argument('--ffmpeg', type=Path, help='Optional test-only encoder; never copied into ZIP')
    args = parser.parse_args()
    if sys.platform != 'win32':
        parser.error('Run this acceptance check on native Windows x64.')
    bundle, output = args.bundle.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if not (bundle / 'Auralume.exe').is_file():
        parser.error('Auralume.exe not found')
    entries = inventory(bundle)
    files = {item['path'] for item in entries}
    for required in ('_internal/native/libmpv-2.dll', '_internal/native/vulkan-1.dll',
                     '_internal/native/native-manifest.json', '_internal/packaging/auralume.svg',
                     '_internal/licenses/LICENSE', '_internal/PySide6/plugins/platforms/qwindows.dll',
                     '_internal/PySide6/plugins/platforms/qoffscreen.dll'):
        if required not in files:
            raise RuntimeError(f'Missing packaged resource: {required}')
    report = {'revision': args.revision, 'files': entries, 'checks': {},
              'physical_audio': 'NOT TESTED: ao=null', 'windows_10_11_manual': 'NOT TESTED',
              'clean_machine': 'NOT TESTED: runner has developer tools; child PATH is restricted',
              'public_distribution': 'BLOCKED: native corresponding-source/license review pending'}
    with tempfile.TemporaryDirectory(prefix='Auralume validação música ') as temporary:
        root = Path(temporary)
        cwd = root / 'diretório independente'
        cwd.mkdir()
        environment = dict(os.environ)
        for key in ('PYTHONPATH', 'PYTHONHOME', 'AURALUME_MPV_DIR', 'QT_PLUGIN_PATH', 'QT_QPA_PLATFORM_PLUGIN_PATH'):
            environment.pop(key, None)
        windows = Path(os.environ['SystemRoot'])
        environment.update(PATH=os.pathsep.join([str(windows / 'System32'), str(windows)]),
                           QT_QPA_PLATFORM='offscreen', PYTHONIOENCODING='utf-8',
                           LOCALAPPDATA=str(root / 'Dados pessoais'), XDG_DATA_HOME=str(root / 'XDG'))
        diagnostics = invoke(bundle / 'Auralume.exe', environment, cwd, '--diagnostics')
        if not diagnostics['frozen'] or not diagnostics['native_mpv']['engine_created']:
            raise RuntimeError(f'Frozen native engine unavailable: {diagnostics}')
        version = diagnostics['auralume']
        name = f'Auralume-{version}-candidate-{args.revision[:12]}-windows-x64.zip'
        archive = output / name
        with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zipped:
            for item in entries:
                zipped.write(bundle / item['path'], 'Auralume/' + item['path'])
        extracted = root / 'Pacote extraído ç'
        extract_package(archive, extracted)
        relocated = (extracted / 'Auralume').resolve()
        if inventory(relocated) != entries:
            raise RuntimeError('ZIP extraction changed package contents')
        binary = relocated / 'Auralume.exe'
        diagnostic = invoke(binary, environment, cwd, '--diagnostics')
        native = diagnostic['native_mpv']
        report['checks']['diagnostics'] = diagnostic
        if not diagnostic['frozen'] or not native['engine_created'] or native['error']:
            raise RuntimeError(f'Extracted engine unavailable: {diagnostic}')
        loaded_libmpv = Path(native['path']).resolve()
        if not loaded_libmpv.is_relative_to(relocated):
            raise RuntimeError(f'Loaded libmpv outside extracted package: {loaded_libmpv} not under {relocated}')
        loaded_vulkan = Path(native['loaded_dependencies']['vulkan-1.dll']).resolve()
        if not loaded_vulkan.is_relative_to(relocated):
            raise RuntimeError(f'Vulkan came from the host instead of the extracted package: '
                               f'{loaded_vulkan} not under {relocated}')
        if (root / 'Dados pessoais').exists() or (root / 'XDG').exists():
            raise RuntimeError('Diagnostics created personal data')
        wav_path = root / 'João - Canção própria.wav'
        write_wav(wav_path)
        paths = [wav_path]
        if args.ffmpeg:
            for extension in ('mp3', 'flac'):
                target = wav_path.with_suffix('.' + extension)
                subprocess.run([str(args.ffmpeg.resolve()), '-v', 'error', '-i', str(wav_path), str(target)],
                               check=True, timeout=30)
                paths.append(target)
        else:
            report['checks']['mp3_flac'] = 'NOT TESTED: supply --ffmpeg for generated encoded fixtures'
        data = root / 'Biblioteca persistente ç'
        for media in paths:
            state = invoke(binary, environment, cwd, '--smoke-test', '--audio-output', 'null', '--play',
                           '--data-dir', data, '--screenshot', output / f'smoke-{media.suffix[1:]}.png', media)
            if not all(state[key] for key in ('ok', 'player_available', 'playback_started', 'history')):
                raise RuntimeError(f'Playback failed: {state}')
            report['checks'][media.suffix[1:]] = state
        # Seed existing user records, then check the actual EXE preserves them
        # across restart. Creation via UI is covered by tests/test_controller.py.
        with open_database(data / 'library.sqlite3') as db:
            track = db.execute('SELECT id FROM tracks LIMIT 1').fetchone()[0]
            db.execute('UPDATE tracks SET favorite=1 WHERE id=?', (track,))
            db.execute('INSERT INTO playlists(id,name) VALUES (?,?)', ('acceptance', 'Viagem ç'))
            db.execute('INSERT INTO playlist_tracks(playlist_id,track_id,position) VALUES (?,?,?)', ('acceptance', track, 0))
            for key, value in [('volume', 43), ('shuffle', True), ('repeat', 'all'), ('preferences', ['jazz'])]:
                db.execute('INSERT OR REPLACE INTO settings(key,value) VALUES (?,?)', (key, json.dumps(value)))
        restart = invoke(binary, environment, cwd, '--smoke-test', '--data-dir', data)
        if not restart['ok'] or restart['tracks'] != len(paths) or restart['history'] != len(paths):
            raise RuntimeError(f'Restart failed: {restart}')
        with open_database(data / 'library.sqlite3') as db:
            if db.execute('SELECT favorite FROM tracks WHERE id=?', (track,)).fetchone() != (1,):
                raise RuntimeError('Favorite lost across restart')
            if db.execute('SELECT track_id FROM playlist_tracks WHERE playlist_id=?', ('acceptance',)).fetchone() != (track,):
                raise RuntimeError('Playlist lost across restart')
            for key, value in [('volume', 43), ('shuffle', True), ('repeat', 'all'), ('preferences', ['jazz'])]:
                if json.loads(db.execute('SELECT value FROM settings WHERE key=?', (key,)).fetchone()[0]) != value:
                    raise RuntimeError(f'Setting lost: {key}')
        report['checks']['restart_preserved_seeded_data'] = restart
        dll = relocated / '_internal/native/libmpv-2.dll'
        hidden = dll.with_suffix('.disabled')
        dll.rename(hidden)
        try:
            failure = invoke(binary, environment, cwd, '--diagnostics', expected_code=1)
            if failure['native_mpv']['loaded'] or failure['native_mpv']['engine_created']:
                raise RuntimeError('External libmpv hid a missing packaged dependency')
            report['checks']['missing_dll_rejected'] = failure
        finally:
            hidden.rename(dll)
        report.update(zip=name, zip_bytes=archive.stat().st_size,
                      sha256=hashlib.sha256(archive.read_bytes()).hexdigest(), relocated=True)
    (output / (name + '.sha256')).write_text(f'{report["sha256"]}  {name}\n', encoding='utf-8')
    (output / 'verification.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in report.items() if key != 'files'}, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
