#!/usr/bin/env python3
"""Copy installed distribution notices byte-for-byte for local packaging."""
import hashlib
from importlib.metadata import distribution, PackageNotFoundError
import json
from pathlib import Path
import shutil


root = Path(__file__).resolve().parent.parent
destination = root / 'packaging/licenses/python-dependencies'
destination.mkdir(parents=True, exist_ok=True)
manifest = []
for name in ('requests', 'urllib3', 'certifi', 'idna', 'charset-normalizer', 'websockets',
             'brotli', 'pycryptodomex', 'yt-dlp-ejs', 'setuptools', 'packaging'):
    try:
        package = distribution(name)
    except PackageNotFoundError:
        continue  # Optional yt-dlp backends may be absent in a fresh environment.
    for entry in package.files or []:
        relative = str(entry)
        if '.dist-info/' not in relative or not any(word in relative.casefold() for word in ('license', 'copying', 'notice')):
            continue
        source = Path(package.locate_file(entry))
        if not source.is_file():
            continue
        target = destination / (relative.replace('/', '__') + '.txt')
        shutil.copyfile(source, target)
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        assert hashlib.sha256(target.read_bytes()).hexdigest() == digest
        manifest.append({'package': name, 'version': package.version, 'file': target.name, 'sha256': digest})
(destination / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(f'{len(manifest)} avisos de dependências copiados e verificados.')
