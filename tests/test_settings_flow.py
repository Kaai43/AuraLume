from PySide6.QtWidgets import QPushButton

from auralume.controller import Controller
from auralume.database import Database
from auralume.player import MpvPlayer
from auralume.ui.main_window import MainWindow


def test_saving_settings_persists_all_values_despite_synchronous_controller_updates(
    tmp_path, qt_application
):
    database = Database(tmp_path / "settings.sqlite3")
    window = MainWindow()
    controller = Controller(window, database, MpvPlayer(audio_output="null"))
    try:
        window.nav_buttons["settings"].click()
        window.settings_volume.setValue(34)
        window.settings_shuffle.setChecked(True)
        window.settings_repeat.setCurrentIndex(window.settings_repeat.findData("one"))
        window.settings_preferences.setText("ambient, piano")
        save = next(
            button
            for button in window.findChildren(QPushButton)
            if button.text() == "Salvar preferências"
        )

        save.click()

        assert database.get_setting("volume") == 34
        assert database.get_setting("shuffle") is True
        assert database.get_setting("repeat") == "one"
        assert database.get_setting("preferences") == ["ambient", "piano"]
    finally:
        controller.close()
        window.close()
        database.close()
