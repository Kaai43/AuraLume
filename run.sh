#!/usr/bin/env bash
set -euo pipefail
auralume_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ -x "$auralume_root/dist/Auralume/Auralume" ]]; then
    exec "$auralume_root/dist/Auralume/Auralume" "$@"
fi
cd "$auralume_root"
exec "$auralume_root/.venv/bin/python" -m auralume "$@"
