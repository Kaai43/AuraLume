#!/usr/bin/env bash
# Run explicitly to register this extracted directory in the user's app menu.
set -euo pipefail
auralume_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
auralume_apps="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
mkdir -p "$auralume_apps"
auralume_escaped="${auralume_dir//\\/\\\\}"
auralume_escaped="${auralume_escaped//\"/\\\"}"
auralume_escaped="${auralume_escaped//\$/\\\$}"
auralume_escaped="${auralume_escaped//\`/\\\`}"
auralume_escaped="${auralume_escaped//%/%%}"
cat > "$auralume_apps/Auralume.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Auralume
Comment=Your Music, Your Way
Exec="$auralume_escaped/Auralume"
Icon=$auralume_dir/auralume.svg
Terminal=false
Categories=AudioVideo;Audio;Player;
StartupNotify=true
DESKTOP
chmod +x "$auralume_apps/Auralume.desktop"
printf 'Atalho criado em %s\n' "$auralume_apps/Auralume.desktop"
