"""Theme changes exercise the real Qt tree, SQLite and libmpv engine."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import wave
import pytest

from PySide6.QtCore import QTimer
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication, QDialog, QMenu

from auralume.controller import Controller
from auralume.database import Database
from auralume.models import Track
from auralume.player import MpvPlayer
from auralume.ui.main_window import MainWindow
from auralume.ui.widgets import CoverArt


def wait_for(app, predicate):
    deadline = time.monotonic() + 6
    while not predicate() and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(.01)
    assert predicate()


def test_theme_switch_repaints_existing_and_new_pages_without_show_override(qt_application):
    window = MainWindow()
    try:
        window.show()
        qt_application.processEvents()
        assert hasattr(window, 'theme_manager'), 'The window needs a live theme manager'
        before = window.now_art.grab().toImage().pixelColor(5, 5)
        window.theme_manager.set_active('soft-daylight')
        colors = window.theme_manager.active_theme.colors
        window.hide()
        window.show()
        for page in ('home', 'library', 'recommendations', 'favorites', 'history', 'settings'):
            window.display_page(page)
            qt_application.processEvents()
            assert window.page_title.palette().color(QPalette.ColorRole.WindowText).name().upper() == colors['text_primary']
            assert window.search_input.palette().color(QPalette.ColorRole.Text).name().upper() == colors['text_primary']
            assert window.sidebar.grab().toImage().pixelColor(1, 1).name().upper() == colors['sidebar']
        assert window.now_art.grab().toImage().pixelColor(5, 5) != before
        window.display_page('recommendations')
        window.show_tracks('Temas', [Track('theme-track', '/missing.wav', 'Música de teste')])
        qt_application.processEvents()
        cover = window.page_widgets['recommendations'].findChild(CoverArt)
        assert cover is not None
        assert cover.grab().toImage().pixelColor(5, 5) != before
        menu = QMenu(window)
        menu.addAction('Ação')
        menu.ensurePolished()
        assert menu.palette().color(QPalette.ColorRole.WindowText).name().upper() == colors['text_primary']
    finally:
        window.close()


def test_theme_gallery_button_opens_accessible_dialog(qt_application):
    window = MainWindow()
    errors = []
    try:
        window.show()
        assert hasattr(window, 'themes_button'), 'Themes entry point is missing'
        assert window.themes_button.accessibleName() == 'Temas'

        def inspect_dialog():
            dialog = QApplication.activeModalWidget()
            if not isinstance(dialog, QDialog) or 'Tema' not in dialog.windowTitle():
                errors.append('Galeria não abriu')
            if dialog:
                dialog.reject()

        QTimer.singleShot(0, inspect_dialog)
        window.themes_button.click()
        assert not errors
    finally:
        window.close()


def test_live_mpv_state_and_import_survive_theme_changes(tmp_path, qt_application):
    window = MainWindow()
    db = Database(tmp_path / 'biblioteca música.sqlite3')
    player = MpvPlayer(audio_output='null')
    controller = Controller(window, db, player)
    path = tmp_path / 'Canção de teste.wav'
    with wave.open(str(path), 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(8000)
        wav.writeframes(b'\x00\x00' * 8000 * 20)
    try:
        assert hasattr(window, 'theme_manager'), 'Theme integration is missing'
        engine = player._engine
        controller.import_paths([path], autoplay=True)
        window.theme_manager.set_active('midnight-blue')
        wait_for(qt_application, lambda: bool(db.history()) and controller._loaded)
        controller.set_volume(37)
        controller.set_shuffle(True)
        controller.set_repeat('all')
        player.seek(3)
        wait_for(qt_application, lambda: player.position >= 2.5)
        controller.toggle_pause()
        position = player.position
        queue = controller.queue
        items = list(queue.items)
        current = controller.current_track.id
        for theme in ('rose-velvet', 'forest', 'soft-daylight', 'auralume-original'):
            window.theme_manager.set_active(theme)
            qt_application.processEvents()
        assert player._engine is engine
        assert controller.db is db
        assert controller.queue is queue and queue.items == items
        assert controller.current_track.id == current
        assert abs(player.position - position) < .25
        assert player.paused and player.volume == 37
        assert queue.shuffle and queue.repeat == 'all'
        assert len(db.history()) == 1 and len(db.list_tracks()) == 1
    finally:
        controller.close()
        window.close()
        db.close()


def test_startup_uses_persisted_theme_under_data_dir_without_losing_legacy_data(tmp_path):
    data = tmp_path / 'Dados música com espaço'
    data.mkdir()
    with_db = Database(data / 'library.sqlite3')
    with_db.set_setting('volume', 37)
    with_db.upsert_track(Track('kept', '/not-played.wav', 'Preservada', favorite=True))
    with_db.set_setting('themes_v1', {'schema_version': 1, 'active_id': 'soft-daylight', 'custom': []})
    with_db.close()
    screenshot = tmp_path / 'light.png'
    result = subprocess.run([sys.executable, '-m', 'auralume', '--smoke-test', '--data-dir', str(data),
                             '--screenshot', str(screenshot)], capture_output=True, text=True, timeout=20,
                            env={**os.environ, 'QT_QPA_PLATFORM': 'offscreen'})
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['ok']
    from PySide6.QtGui import QImage
    # Light sidebar, away from text, borders and rounded controls.
    color = QImage(str(screenshot)).pixelColor(2, 300)
    assert color.lightness() > 180, 'Startup ignored the persisted light theme'
    db = Database(data / 'library.sqlite3')
    try:
        assert db.get_setting('volume') == 37
        assert db.get_track('kept').favorite
    finally:
        db.close()


def test_custom_theme_roundtrip_in_real_sqlite_and_legacy_settings(tmp_path):
    from auralume.themes import ThemeDefinition, ThemeManager
    path = tmp_path / 'dados.sqlite3'
    db = Database(path)
    try:
        db.set_setting('preferences', ['jazz', 'música brasileira'])
        manager = ThemeManager(db)
        assert manager.active_theme.id == 'auralume-original'
        assert db.get_setting('themes_v1') is None
        custom = manager.import_json(Path('docs/contracts/theme-example.json').read_bytes())
        manager.set_active(custom.id)
        exported = manager.export_json(custom.id)
    finally:
        db.close()
    db = Database(path)
    try:
        reopened = ThemeManager(db)
        assert reopened.active_theme.id == 'meu-auralume'
        assert reopened.active_theme.name == 'Meu Auralume'
        assert reopened.active_theme.colors['background'] == '#14131A'
        assert ThemeDefinition.from_json(exported) == reopened.active_theme
        assert db.get_setting('preferences') == ['jazz', 'música brasileira']
        reopened.delete('meu-auralume')
        assert reopened.active_theme.id == 'auralume-original'
        assert db.get_setting('themes_v1')['active_id'] == 'auralume-original'
    finally:
        db.close()


@pytest.mark.parametrize('fixture', sorted(Path('docs/contracts/invalid').glob('*.json')), ids=lambda p: p.stem)
def test_shared_invalid_theme_fixtures_are_rejected(fixture):
    from auralume.themes import ThemeDefinition, ThemeValidationError
    with pytest.raises(ThemeValidationError):
        ThemeDefinition.from_json(fixture.read_bytes())
