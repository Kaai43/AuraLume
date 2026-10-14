#!/usr/bin/env bash
set -euo pipefail
auralume_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$auralume_root"
export PYINSTALLER_CONFIG_DIR="$auralume_root/build/pyinstaller-cache"
"$auralume_root/.venv/bin/python" scripts/collect_licenses.py
"$auralume_root/.venv/bin/python" -m PyInstaller --noconfirm Auralume.spec
cp README.md LICENSE dist/Auralume/
cp packaging/Auralume.desktop packaging/auralume.svg dist/Auralume/
cp packaging/install-desktop.sh dist/Auralume/
cp -R docs dist/Auralume/
chmod +x dist/Auralume/install-desktop.sh
"$auralume_root/dist/Auralume/Auralume" --diagnostics
