import json
import os
from pathlib import Path
import subprocess
import sys


def test_diagnostics_does_not_require_display_or_create_user_data(tmp_path):
    result = subprocess.run([sys.executable, '-m', 'auralume', '--diagnostics'],
                            capture_output=True, text=True, timeout=15,
                            env={**os.environ, 'XDG_DATA_HOME': str(tmp_path)})
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report['auralume'] == '0.1.0'
    assert report['libmpv']
    assert not list(tmp_path.iterdir())


def test_offscreen_startup_smoke(tmp_path):
    screenshot = tmp_path / 'startup.png'
    result = subprocess.run([sys.executable, '-m', 'auralume', '--smoke-test',
                             '--data-dir', str(tmp_path / 'data'), '--screenshot', str(screenshot)],
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report['ok'] is True
    assert screenshot.read_bytes().startswith(b'\x89PNG')


def test_invalid_authorized_source_is_a_reported_failure(tmp_path):
    result = subprocess.run([sys.executable, '-m', 'auralume', '--smoke-test',
                             '--data-dir', str(tmp_path / 'data'), '--authorized-source', 'file:///etc/passwd'],
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report['ok'] is False
    assert report['tracks'] == 0
    assert report['history'] == 0
