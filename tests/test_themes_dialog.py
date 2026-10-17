from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox, QInputDialog, QPushButton

from auralume.themes import PRESETS, ThemeDefinition, ThemeManager
from auralume.ui.theme_dialog import ThemeEditorDialog, ThemeGalleryDialog


def test_gallery_shows_all_presets_marks_active_and_applies_selected_theme(qt_application):
    manager = ThemeManager()
    dialog = ThemeGalleryDialog(manager)
    dialog.show()
    qt_application.processEvents()

    assert dialog.theme_list.count() == 5
    assert "Ativo" in dialog.theme_list.item(0).text()
    dialog.theme_list.setCurrentRow(1)
    dialog.apply_button.click()

    assert manager.active_theme == PRESETS[1]
    assert dialog.result() == dialog.DialogCode.Accepted


def test_editor_preview_is_local_and_reset_restores_seed_colors(qt_application):
    manager = ThemeManager()
    seed = PRESETS[0]
    dialog = ThemeEditorDialog(seed)
    original_preview = dialog.preview_widget.styleSheet()
    accent_edit = dialog.findChild(type(dialog.name_edit), "colorEdit_accent")
    accent_edit.setText("#010203")
    qt_application.processEvents()

    assert dialog.preview_widget.styleSheet() != original_preview
    assert manager.active_theme == seed
    assert dialog.contrast_warning.text()

    dialog.findChild(QPushButton, "resetThemeButton").click()

    assert accent_edit.text() == seed.colors["accent"]


def test_editor_cancel_does_not_change_manager(qt_application):
    manager = ThemeManager()
    dialog = ThemeEditorDialog(manager.active_theme)
    dialog.name_edit.setText("Unsaved theme")
    dialog.reject()

    assert manager.active_theme == PRESETS[0]
    assert manager.themes() == list(PRESETS)


def test_gallery_does_not_apply_selection_until_apply_button(qt_application):
    manager = ThemeManager()
    dialog = ThemeGalleryDialog(manager)
    dialog.theme_list.setCurrentRow(2)

    assert manager.active_theme == PRESETS[0]
    assert dialog.preview_theme.id == PRESETS[2].id


def test_gallery_create_and_apply_action_persists_only_after_editor_confirmation(qt_application):
    manager = ThemeManager()
    dialog = ThemeGalleryDialog(manager)
    dialog.show()

    def fill_editor():
        editor = QApplication.activeModalWidget()
        assert isinstance(editor, ThemeEditorDialog)
        editor.name_edit.setText("Tema da galeria")
        editor.apply_button.click()

    QTimer.singleShot(0, fill_editor)
    dialog.create_button.click()

    assert manager.active_theme.name == "Tema da galeria"
    assert any(theme.name == "Tema da galeria" for theme in manager.themes())


def test_editor_save_keeps_active_theme_while_cancel_discards_draft(qt_application):
    manager = ThemeManager()
    dialog = ThemeGalleryDialog(manager)

    def save_draft():
        editor = QApplication.activeModalWidget()
        assert isinstance(editor, ThemeEditorDialog)
        editor.name_edit.setText("Tema salvo")
        editor.save_button.click()

    QTimer.singleShot(0, save_draft)
    dialog.create_button.click()
    assert manager.active_theme == PRESETS[0]
    assert any(theme.name == "Tema salvo" for theme in manager.themes())

    def cancel_draft():
        editor = QApplication.activeModalWidget()
        assert isinstance(editor, ThemeEditorDialog)
        editor.name_edit.setText("Rascunho descartado")
        editor.reject()

    QTimer.singleShot(0, cancel_draft)
    dialog.create_button.click()
    assert all(theme.name != "Rascunho descartado" for theme in manager.themes())


def test_gallery_renames_user_theme_and_requires_delete_confirmation(qt_application, monkeypatch):
    manager = ThemeManager()
    user_theme = manager.duplicate(PRESETS[0].id, "Tema removível")
    dialog = ThemeGalleryDialog(manager)
    dialog._select_id(user_theme.id)
    monkeypatch.setattr(QInputDialog, "getText", lambda *args, **kwargs: ("Tema renomeado", True))
    dialog.rename_button.click()
    assert any(theme.name == "Tema renomeado" for theme in manager.themes())

    renamed = next(theme for theme in manager.themes() if theme.name == "Tema renomeado")
    dialog._select_id(renamed.id)
    manager.set_active(renamed.id)
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.No)
    dialog.delete_button.click()
    assert any(theme.id == renamed.id for theme in manager.themes())

    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    dialog.delete_button.click()
    assert all(theme.id != renamed.id for theme in manager.themes())
    assert manager.active_theme == PRESETS[0]


def test_gallery_import_export_uses_json_files_and_copies_collisions(
    tmp_path, qt_application, monkeypatch
):
    manager = ThemeManager()
    source_theme = ThemeDefinition("shared-theme", "Tema compartilhado", PRESETS[1].colors)
    source_path = tmp_path / "tema.json"
    source_path.write_text(source_theme.to_json(), encoding="utf-8")
    export_path = tmp_path / "exportado.json"
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *args: (str(source_path), "JSON (*.json)"))
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args: (str(export_path), "JSON (*.json)"))
    dialog = ThemeGalleryDialog(manager)

    dialog.import_button.click()
    assert any(theme.id == source_theme.id for theme in manager.themes())
    dialog._select_id(source_theme.id)
    dialog.export_button.click()
    assert ThemeDefinition.from_json(export_path.read_bytes()) == source_theme

    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    dialog.import_button.click()
    copies = [theme for theme in manager.themes() if theme.name.startswith("Tema compartilhado")]
    assert len(copies) == 2
    assert copies[0].id != copies[1].id
