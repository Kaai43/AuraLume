"""Platform data/resource locations, independent of the working directory."""
import os
from pathlib import Path
import sys


def default_data_dir(platform_name=None, environment=None, home=None) -> Path:
    platform_name = sys.platform if platform_name is None else platform_name
    environment = os.environ if environment is None else environment
    home = Path.home() if home is None else Path(home)
    if platform_name == 'win32':
        modern = Path(environment.get('LOCALAPPDATA') or home / 'AppData' / 'Local') / 'Auralume'
        legacy = Path(environment.get('XDG_DATA_HOME') or home / '.local/share') / 'Auralume'
        if not (modern / 'library.sqlite3').exists() and (legacy / 'library.sqlite3').is_file():
            return legacy  # Preserve pre-port data in place; --data-dir always overrides.
        return modern
    return Path(environment.get('XDG_DATA_HOME') or home / '.local/share') / 'Auralume'


def resource_path(name: str) -> Path:
    root = Path(sys._MEIPASS) if getattr(sys, 'frozen', False) else Path(__file__).resolve().parents[1]
    return root / 'packaging' / name
