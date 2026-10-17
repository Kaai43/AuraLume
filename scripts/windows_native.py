#!/usr/bin/env python3
"""Fetch pinned inputs and stage Windows DLLs; never install them globally."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / 'packaging/windows/native-lock.json'


def verify_digest(path, expected):
    with Path(path).open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    if actual != expected:
        raise ValueError(f'SHA-256 mismatch: {path.name}: {actual} != {expected}')


def fetch(item, cache):
    target = cache / item['filename']
    if not target.exists():
        with urllib.request.urlopen(item['url'], timeout=120) as response, target.open('wb') as output:
            shutil.copyfileobj(response, output)
    verify_digest(target, item['sha256'])
    return target


def validate_imports(imports, allowed):
    allowed = {name.lower() for name in allowed}
    missing = [name for name in imports if name.lower() not in allowed
               and not name.lower().startswith(('api-ms-win-', 'ext-ms-win-'))]
    if missing:
        raise ValueError(f'Unresolved native dependencies: {", ".join(missing)}')


def audit_pe(path, allowed):
    import pefile
    with pefile.PE(str(path), fast_load=True) as pe:
        if pe.FILE_HEADER.Machine != 0x8664:
            raise ValueError(f'Not AMD64: {path}')
        pe.parse_data_directories(directories=[1, 13])
        imports = sorted({entry.dll.decode().lower()
                          for key in ('DIRECTORY_ENTRY_IMPORT', 'DIRECTORY_ENTRY_DELAY_IMPORT')
                          for entry in getattr(pe, key, [])})
        validate_imports(imports, allowed)
    return {'file': path.name, 'size': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'machine': 'AMD64', 'imports': imports}


def unpack_source(archive, destination):
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive) as source:
        source.extractall(destination, filter='data')
    roots = [path for path in destination.iterdir() if path.is_dir()]
    if len(roots) != 1:
        raise ValueError(f'Unexpected source archive layout: {archive}')
    return roots[0]


def run(*arguments):
    subprocess.run([str(arg) for arg in arguments], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=ROOT / '.tools/windows-native')
    parser.add_argument('--output', type=Path, default=ROOT / 'vendor/mpv')
    parser.add_argument('--seven-zip', default=shutil.which('7z'))
    parser.add_argument('--audit-only', action='store_true', help='Inspect pinned libmpv without building Windows Vulkan')
    args = parser.parse_args()
    lock = json.loads(LOCK.read_text(encoding='utf-8'))
    cache, output = args.cache.resolve(), args.output.resolve()
    cache.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)
    if not args.seven_zip:
        parser.error('7-Zip is required (7z on PATH or --seven-zip).')
    archive = fetch(lock['mpv'], cache)
    # Extract exactly one hashed file to stdout, never trust archive paths.
    dll = output / 'libmpv-2.dll'
    with dll.open('wb') as stream:
        subprocess.run([args.seven_zip, 'e', '-so', str(archive), 'libmpv-2.dll'],
                       stdout=stream, check=True)
    verify_digest(dll, lock['mpv']['dll_sha256'])
    report = {'inputs': lock, 'public_distribution': 'BLOCKED: corresponding-source/license audit pending',
              'binaries': [audit_pe(dll, lock['system_dlls'] + ['vulkan-1.dll'])]}
    if args.audit_only:
        report['runtime_validation'] = 'NOT EXECUTED; Vulkan DLL still required'
    else:
        if sys.platform != 'win32':
            parser.error('A native Windows host is required to build Vulkan. Use --audit-only on Linux.')
        headers = unpack_source(fetch(lock['vulkan_headers'], cache), cache / 'headers-source')
        loader = unpack_source(fetch(lock['vulkan_loader'], cache), cache / 'loader-source')
        install = cache / 'vulkan-install'
        run('cmake', '-S', headers, '-B', cache / 'headers-build', '-A', 'x64',
            f'-DCMAKE_INSTALL_PREFIX={install}', '-DVULKAN_HEADERS_ENABLE_TESTS=OFF')
        run('cmake', '--install', cache / 'headers-build', '--config', 'Release')
        run('cmake', '-S', loader, '-B', cache / 'loader-build', '-A', 'x64',
            f'-DCMAKE_PREFIX_PATH={install}', '-DBUILD_TESTS=OFF', '-DUPDATE_DEPS=OFF',
            f'-DCMAKE_INSTALL_PREFIX={install}')
        run('cmake', '--build', cache / 'loader-build', '--config', 'Release', '--parallel', '2')
        run('cmake', '--install', cache / 'loader-build', '--config', 'Release')
        vulkan = output / 'vulkan-1.dll'
        shutil.copy2(install / 'bin/vulkan-1.dll', vulkan)
        report['binaries'].append(audit_pe(vulkan, lock['system_dlls']))
        notices = output / 'licenses'
        notices.mkdir(exist_ok=True)
        for name, source in [('Vulkan-Loader', loader), ('Vulkan-Headers', headers)]:
            for path in source.iterdir():
                if path.name.startswith(('LICENSE', 'NOTICE')):
                    if path.is_dir():
                        shutil.copytree(path, notices / f'{name}-{path.name}', dirs_exist_ok=True)
                    else:
                        shutil.copy2(path, notices / f'{name}-{path.name}')
        license_path = Path(sys.base_prefix) / 'LICENSE.txt'
        shutil.copy2(license_path, notices / 'Python-LICENSE.txt')
        python_inventory = []
        for name in ('PySide6', 'PySide6_Essentials', 'PySide6_Addons', 'shiboken6', 'mpv',
                     'mutagen', 'yt-dlp', 'PyInstaller', 'requests', 'urllib3', 'certifi',
                     'idna', 'charset-normalizer', 'websockets', 'brotli', 'pycryptodomex', 'yt-dlp-ejs'):
            package = importlib.metadata.distribution(name)
            copied = []
            for item in package.files or []:
                if '.dist-info/' in str(item) and any(word in str(item).lower() for word in ('license', 'copying', 'notice')):
                    path = Path(package.locate_file(item))
                    if path.is_file():
                        target = notices / (str(item).replace('/', '__').replace('\\', '__') + '.txt')
                        shutil.copy2(path, target)
                        copied.append(target.name)
            python_inventory.append({'package': name, 'version': package.version, 'copied_notices': copied})
        report['python_distributions'] = python_inventory
        ffmpeg_archive = fetch(lock['ffmpeg_test_only'], cache)
        with (cache / 'ffmpeg.exe').open('wb') as stream:
            subprocess.run([args.seven_zip, 'e', '-so', str(ffmpeg_archive), 'ffmpeg.exe'], stdout=stream, check=True)
        # The encoder has the same mandatory Vulkan import. Keep this test-only
        # runtime beside the encoder, outside the application's distribution.
        shutil.copy2(vulkan, cache / 'vulkan-1.dll')
        report['test_only_encoder'] = audit_pe(cache / 'ffmpeg.exe', lock['system_dlls'] + ['vulkan-1.dll'])
        report['runtime_validation'] = 'Requires python -m auralume --diagnostics and full test suite'
    (output / 'native-manifest.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
