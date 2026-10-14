import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QLineEdit, QCheckBox, QMenu

from auralume.ui.main_window import MainWindow
from auralume.models import Playlist, Track


@pytest.fixture(scope="session")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(app):
    instance = MainWindow()
    instance.show()
    yield instance
    instance.close()


def test_sidebar_navigation_emits_stable_page_id(window):
    navigated = []
    window.navigate.connect(navigated.append)

    window.nav_buttons["favorites"].click()

    assert navigated == ["favorites"]
    assert window.current_page == "favorites"


def test_search_submits_trimmed_query_and_opens_search_page(window):
    searches = []
    navigated = []
    window.search_requested.connect(searches.append)
    window.navigate.connect(navigated.append)
    window.search_input.setText("  ambient focus  ")
    QTest.keyClick(window.search_input, Qt.Key_Return)

    assert searches == ["ambient focus"]
    assert navigated == ["search"]


def test_progress_slider_emits_seconds_based_on_current_duration(window):
    positions = []
    window.seek_requested.connect(positions.append)
    window.set_progress(45, 180)

    window.progress_slider.setValue(500)
    window.progress_slider.sliderReleased.emit()

    assert positions == [90.0]


def test_source_request_is_not_emitted_when_authorization_is_not_checked(window):
    def cancel_dialog():
        dialog = QApplication.activeModalWidget()
        assert dialog is not None
        dialog.findChild(QLineEdit).setText("https://example.org/audio")
        dialog.findChild(QDialogButtonBox).button(QDialogButtonBox.StandardButton.Cancel).click()

    QTimer.singleShot(0, cancel_dialog)
    requested = []
    window.source_requested.connect(requested.append)

    window.open_source_button.click()

    assert requested == []


def test_source_request_emits_url_only_after_authorized_confirmation(window):
    def authorize_and_open():
        dialog = QApplication.activeModalWidget()
        assert dialog is not None
        dialog.findChild(QLineEdit).setText("https://example.org/audio")
        dialog.findChild(QCheckBox).setChecked(True)
        dialog.findChild(QDialogButtonBox).button(QDialogButtonBox.StandardButton.Open).click()

    QTimer.singleShot(0, authorize_and_open)
    requested = []
    window.source_requested.connect(requested.append)

    window.open_source_button.click()

    assert requested == ["https://example.org/audio"]


def test_source_dialog_opens_valid_http_source_in_browser_only_after_click(window, monkeypatch):
    from PySide6.QtGui import QDesktopServices
    from PySide6.QtWidgets import QPushButton

    opened = []
    requested = []
    monkeypatch.setattr(QDesktopServices, "openUrl", lambda url: opened.append(url.toString()) or True)
    window.source_requested.connect(requested.append)

    missing_button = []

    def click_browser_action():
        dialog = QApplication.activeModalWidget()
        assert dialog is not None
        dialog.findChild(QLineEdit).setText("https://music.example.org/song")
        dialog.findChild(QCheckBox).setChecked(True)
        browser_button = dialog.findChild(QPushButton, "openSourceBrowserButton")
        try:
            if browser_button is None:
                missing_button.append(True)
            else:
                assert browser_button.isEnabled()
                browser_button.click()
        finally:
            dialog.reject()

    QTimer.singleShot(0, click_browser_action)
    window.open_source_button.click()

    assert missing_button == []
    assert opened == ["https://music.example.org/song"]
    assert requested == []


def test_source_dialog_does_not_offer_browser_for_non_http_urls(window):
    from PySide6.QtWidgets import QPushButton

    available = []

    def inspect_unsupported_url():
        dialog = QApplication.activeModalWidget()
        assert dialog is not None
        dialog.findChild(QLineEdit).setText("file:///tmp/song.ogg")
        dialog.findChild(QCheckBox).setChecked(True)
        browser_button = dialog.findChild(QPushButton, "openSourceBrowserButton")
        available.append(browser_button.isEnabled())
        dialog.reject()

    QTimer.singleShot(0, inspect_unsupported_url)
    window.open_source_button.click()

    assert available == [False]


def test_setting_controls_can_be_updated_without_emitting_user_changes(window):
    volume_changes = []
    shuffle_changes = []
    window.volume_requested.connect(volume_changes.append)
    window.shuffle_requested.connect(shuffle_changes.append)

    window.set_settings(33, True, "one", "jazz, ambient")
    window.display_page("settings")

    assert window.volume_slider.value() == 33
    assert window.shuffle_button.isChecked()
    assert window.settings_volume.value() == 33
    assert window.settings_shuffle.isChecked()
    assert window.settings_repeat.currentData() == "one"
    assert window.settings_preferences.text() == "jazz, ambient"
    assert volume_changes == []
    assert shuffle_changes == []


def test_import_controls_emit_requests(window):
    file_imports = []
    folder_imports = []
    window.import_files_requested.connect(lambda: file_imports.append(True))
    window.import_folder_requested.connect(lambda: folder_imports.append(True))

    window.import_file_button.click()
    window.import_folder_button.click()

    assert file_imports == [True]
    assert folder_imports == [True]


def test_global_space_shortcut_does_not_steal_text_from_search(window):
    playback = []
    window.play_pause_requested.connect(lambda: playback.append(True))
    window.search_input.setFocus()
    QTest.keyClick(window.search_input, Qt.Key_Space)

    assert window.search_input.text() == " "
    assert playback == []


def test_show_tracks_keeps_current_navigation_context_and_playlist_page(window):
    selected = []
    window.playlist_selected.connect(selected.append)
    playlist = Playlist(id="mix-1", name="Tarde calma", track_count=1)
    track = Track(id="track-1", source="/music/track.ogg", title="Luz", artist="Lume")
    window.show_playlists([playlist])
    item = window.playlist_list.item(0)
    window.playlist_list.itemDoubleClicked.emit(item)

    window.show_tracks("Tarde calma", [track])

    assert selected == ["mix-1"]
    assert window.current_page == "playlists"
    assert window.page_title.text() == "Playlists"
    assert window.track_table.item(0, 0).text() == "Luz"


def test_remote_track_source_opens_in_system_browser_only_on_explicit_request(window, monkeypatch):
    from PySide6.QtGui import QDesktopServices

    opened = []
    monkeypatch.setattr(QDesktopServices, "openUrl", lambda url: opened.append(url.toString()))
    track = Track(
        id="remote-1",
        source="https://music.example.org/watch?id=1",
        title="Luz distante",
        is_remote=True,
    )
    window.display_page("library")
    window.show_tracks("Biblioteca", [track])
    assert opened == []

    window.open_track_source("remote-1")

    assert opened == ["https://music.example.org/watch?id=1"]


def test_set_queue_updates_player_indicator_without_opening_queue_dialog(window):
    track = Track(id="q1", source="/music/q1.ogg", title="Fila um")

    window.set_queue([track])

    assert window.current_page == "home"
    assert window.queue_button.text() == "Fila (1)"


def test_set_playlists_updates_cache_without_navigating(window):
    playlist = Playlist(id="mix-2", name="Noite", track_count=4)

    window.set_playlists([playlist])
    window.display_page("playlists")

    assert window.current_page == "playlists"
    assert window.playlist_list.count() == 1
    assert "Noite" in window.playlist_list.item(0).text()


def test_navigating_away_from_playlist_clears_its_track_action_context(window):
    playlist = Playlist(id="mix-3", name="Noite")
    window.show_playlists([playlist])
    window.playlist_list.itemDoubleClicked.emit(window.playlist_list.item(0))

    window.display_page("library")

    assert window._selected_playlist_id == ""


def test_busy_state_only_disables_import_actions(window):
    window.set_busy(True)

    assert window.import_file_button.isEnabled() is False
    assert window.import_folder_button.isEnabled() is False
    assert window.open_source_button.isEnabled() is False
    assert window.page_stack.isEnabled()
    assert window.play_button.isEnabled()
    assert window.nav_buttons["library"].isEnabled()


def test_player_progress_does_not_move_slider_while_user_is_dragging(window):
    window.set_progress(30, 120)
    window.progress_slider.setSliderDown(True)
    before = window.progress_slider.value()

    window.set_progress(75, 120)

    assert window.progress_slider.value() == before
    assert window.position_label.text() == "1:15"

    window.progress_slider.setSliderDown(False)


def test_set_active_playlist_selects_row_without_changing_page(window):
    window.show_playlists([Playlist(id="mix-4", name="Manhã")])

    window.set_active_playlist("mix-4")

    assert window.current_page == "playlists"
    assert window.playlist_list.currentItem().data(Qt.ItemDataRole.UserRole) == "mix-4"


def test_favorite_tracks_are_marked_in_the_library_table(window):
    favorite = Track(id="fav-1", source="/music/fav.ogg", title="Aurora", favorite=True)
    window.display_page("favorites")

    window.show_tracks("Favoritos", [favorite])

    assert window.track_table.item(0, 0).text() == "♥  Aurora"


def test_playlist_submenu_action_emits_the_selected_playlist_id(window):
    track = Track(id="track-menu", source="/music/song.ogg", title="Song")
    playlist = Playlist(id="playlist-menu", name="Mix")
    window.set_playlists([playlist])
    window.display_page("library")
    window.show_tracks("Biblioteca", [track])
    requests = []
    window.playlist_add_requested.connect(lambda playlist_id, track_id: requests.append((playlist_id, track_id)))

    def trigger_first_playlist_action():
        menu = QApplication.activePopupWidget()
        assert isinstance(menu, QMenu)
        submenu = next(action.menu() for action in menu.actions() if action.menu())
        submenu.actions()[0].trigger()
        menu.close()

    QTimer.singleShot(0, trigger_first_playlist_action)
    window._show_track_menu(QPoint(1, 1))

    assert requests == [("playlist-menu", "track-menu")]


def test_long_metadata_keeps_controls_visible_and_full_text_accessible(window, app):
    from auralume.ui.widgets import TrackCard
    from PySide6.QtWidgets import QLabel
    title = 'Uma canção de nome longo com todas as suas variações ' * 10
    artist = 'Artista convidado e orquestra ' * 10
    track = Track('long', '/long.wav', title, artist=artist, album='Álbum ' * 40)
    window.resize(980, 650)
    window.set_now_playing(track, True)
    window.display_page('recommendations')
    window.show_tracks('Para Você', [track])
    app.processEvents()

    assert window.now_title.toolTip() == title
    assert window.now_artist.toolTip() == artist
    assert window.now_title.mapTo(window, QPoint(window.now_title.width(), 0)).x() <= window.shuffle_button.mapTo(window, QPoint()).x()
    card = window.page_widgets['recommendations'].findChild(TrackCard)
    card_title = card.findChild(QLabel, 'cardTitle')
    assert card_title.toolTip() == title
    assert card_title.height() <= card_title.fontMetrics().height() * 2
    assert not window.track_table.horizontalScrollBar().isVisible()
