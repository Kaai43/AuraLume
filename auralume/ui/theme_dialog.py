"""Accessible theme gallery and editor, isolated from the main application shell."""

from __future__ import annotations

import re
import secrets

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from auralume.themes import COLOR_TOKENS, MAX_JSON_BYTES, PRESETS, ThemeDefinition, ThemeValidationError
from auralume.themes.model import _HEX_RE
from auralume.themes.style import palette, stylesheet


_TOKEN_LABELS = {
    "background": "Fundo", "sidebar": "Barra lateral", "surface": "Superfície",
    "surface_alt": "Superfície alternativa", "player_background": "Fundo do player",
    "text_primary": "Texto principal", "text_secondary": "Texto secundário",
    "text_disabled": "Texto desativado", "accent": "Destaque",
    "accent_hover": "Destaque ao passar o mouse", "accent_foreground": "Texto sobre o destaque",
    "border": "Borda", "selection": "Seleção", "focus": "Foco", "success": "Sucesso",
    "warning": "Aviso", "error": "Erro", "slider_track": "Trilho do controle",
    "slider_fill": "Progresso do controle", "card_background": "Fundo do cartão",
    "card_hover": "Cartão ao passar o mouse", "menu_background": "Menu",
    "cover_start": "Capa — início", "cover_middle": "Capa — meio", "cover_end": "Capa — fim",
    "cover_foreground": "Símbolo da capa", "hero_start": "Painel inicial — início",
    "hero_middle": "Painel inicial — meio", "hero_end": "Painel inicial — fim",
}


def _luminance(hex_color: str) -> float:
    channels = [int(hex_color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(first: str, second: str) -> float:
    """Return the WCAG relative luminance contrast ratio for two #RRGGBB values."""
    if not _HEX_RE.fullmatch(first) or not _HEX_RE.fullmatch(second):
        raise ValueError("Cores de contraste devem usar o formato #RRGGBB.")
    high, low = sorted((_luminance(first), _luminance(second)), reverse=True)
    return (high + 0.05) / (low + 0.05)


class ThemeEditorDialog(QDialog):
    """Edits a detached draft; saving and applying remain separate actions."""

    def __init__(self, theme: ThemeDefinition, parent=None, *, is_new: bool = False):
        super().__init__(parent)
        self.setWindowTitle("Criar meu tema" if is_new else "Editar tema")
        self.setMinimumSize(700, 620)
        self._seed = theme
        self._result_theme: ThemeDefinition | None = None
        self.apply_after_save = False

        root = QVBoxLayout(self)
        details = QFormLayout()
        self.name_edit = QLineEdit(theme.name)
        self.name_edit.setObjectName("themeNameEdit")
        self.name_edit.setMaxLength(60)
        self.name_edit.setAccessibleName("Nome do tema")
        details.addRow("Nome", self.name_edit)
        root.addLayout(details)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        color_panel = QWidget()
        form = QFormLayout(color_panel)
        self.color_edits: dict[str, QLineEdit] = {}
        for token in COLOR_TOKENS:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            edit = QLineEdit(theme.colors[token])
            edit.setObjectName(f"colorEdit_{token}")
            edit.setMaxLength(7)
            edit.setAccessibleName(f"Cor {token.replace('_', ' ')} em hexadecimal")
            edit.textChanged.connect(self._update_preview)
            self.color_edits[token] = edit
            choose = QPushButton("Escolher…")
            choose.setAccessibleName(f"Escolher cor {token.replace('_', ' ')}")
            choose.clicked.connect(lambda checked=False, key=token: self._choose_color(key))
            row_layout.addWidget(edit, 1)
            row_layout.addWidget(choose)
            form.addRow(_TOKEN_LABELS[token], row)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(color_panel)
        splitter.addWidget(scroll)

        self.preview_widget = QWidget()
        self.preview_widget.setObjectName("themeEditorPreview")
        preview_layout = QVBoxLayout(self.preview_widget)
        preview_layout.setContentsMargins(15, 15, 15, 15)
        self.preview_sidebar = QLabel("AURALUME\nInício\nBiblioteca\nFavoritos")
        self.preview_sidebar.setObjectName("sidebar")
        self.preview_sidebar.setMinimumHeight(150)
        self.preview_sidebar.setAccessibleName("Prévia da barra lateral")
        preview_layout.addWidget(self.preview_sidebar)
        self.preview_card = QFrame()
        self.preview_card.setObjectName("trackCard")
        card_layout = QVBoxLayout(self.preview_card)
        self.preview_title = QLabel("Luz da manhã")
        self.preview_title.setObjectName("cardTitle")
        self.preview_detail = QLabel("Auralume · Prévia do tema")
        self.preview_detail.setObjectName("mutedText")
        card_layout.addWidget(self.preview_title)
        card_layout.addWidget(self.preview_detail)
        preview_layout.addWidget(self.preview_card)
        self.preview_action = QPushButton("Reproduzir")
        self.preview_action.setObjectName("primaryButton")
        preview_layout.addWidget(self.preview_action)
        self.contrast_warning = QLabel()
        self.contrast_warning.setObjectName("contrastWarning")
        self.contrast_warning.setWordWrap(True)
        self.contrast_warning.setAccessibleName("Aviso de contraste do tema")
        preview_layout.addWidget(self.contrast_warning)
        preview_layout.addStretch(1)
        splitter.addWidget(self.preview_widget)
        splitter.setSizes([430, 280])
        root.addWidget(splitter, 1)

        self.error_label = QLabel()
        self.error_label.setObjectName("themeEditorError")
        self.error_label.setWordWrap(True)
        root.addWidget(self.error_label)

        buttons = QHBoxLayout()
        self.reset_button = QPushButton("Redefinir")
        self.reset_button.setObjectName("resetThemeButton")
        self.reset_button.clicked.connect(self._reset)
        buttons.addWidget(self.reset_button)
        buttons.addStretch(1)
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)
        buttons.addWidget(self.cancel_button)
        self.save_button = QPushButton("Salvar")
        self.save_button.setObjectName("saveThemeButton")
        self.save_button.clicked.connect(self._save)
        buttons.addWidget(self.save_button)
        self.apply_button = QPushButton("Aplicar")
        self.apply_button.setObjectName("applyEditedThemeButton")
        self.apply_button.clicked.connect(self._apply)
        buttons.addWidget(self.apply_button)
        root.addLayout(buttons)
        self._update_preview()

    def result_theme(self) -> ThemeDefinition | None:
        return self._result_theme

    def _draft(self) -> ThemeDefinition:
        name = self.name_edit.text().strip()
        if not name:
            raise ThemeValidationError("Digite um nome para o tema.")
        colors = {token: edit.text().strip() for token, edit in self.color_edits.items()}
        for token, value in colors.items():
            if not _HEX_RE.fullmatch(value):
                raise ThemeValidationError(f"Confira a cor {token.replace('_', ' ')}. Use #RRGGBB.")
        return ThemeDefinition(self._seed.id, name, colors, self._seed.author)

    def _update_preview(self, *_args) -> None:
        try:
            draft = self._draft()
        except (ThemeValidationError, ValueError):
            self.contrast_warning.setText("Confira o nome e as cores para atualizar a prévia.")
            return
        self.preview_widget.setStyleSheet(stylesheet(draft))
        self.preview_widget.setPalette(palette(draft))
        self.preview_widget.setAutoFillBackground(True)
        pairs = {
            "texto principal/fundo": ("text_primary", "background"),
            "texto principal/superfície": ("text_primary", "surface"),
            "texto principal/cartão": ("text_primary", "card_background"),
            "texto principal/barra lateral": ("text_primary", "sidebar"),
            "texto principal/seleção": ("text_primary", "selection"),
            "texto principal/menu": ("text_primary", "menu_background"),
            "texto principal/painel inicial": ("text_primary", "hero_start"),
            "texto principal/painel inicial meio": ("text_primary", "hero_middle"),
            "texto principal/painel inicial fim": ("text_primary", "hero_end"),
            "texto secundário/fundo": ("text_secondary", "background"),
            "texto secundário/superfície": ("text_secondary", "surface"),
            "texto secundário/barra lateral": ("text_secondary", "sidebar"),
            "texto no destaque/destaque": ("accent_foreground", "accent"),
        }
        ratios = {
            label: contrast_ratio(draft.colors[foreground], draft.colors[background])
            for label, (foreground, background) in pairs.items()
        }
        low = [f"{label}: {ratio:.1f}:1" for label, ratio in ratios.items() if ratio < 4.5]
        if low:
            self.contrast_warning.setText("Nas combinações avaliadas, contraste abaixo de 4,5:1 — " + "; ".join(low))
        else:
            self.contrast_warning.setText("Nas combinações avaliadas, o contraste de texto atingiu pelo menos 4,5:1.")
        self.error_label.clear()

    def _choose_color(self, token: str) -> None:
        current = QColor(self.color_edits[token].text())
        color = QColorDialog.getColor(current if current.isValid() else QColor("#FFFFFF"), self,
                                      f"Escolher cor: {token.replace('_', ' ')}")
        if color.isValid():
            self.color_edits[token].setText(color.name().upper())

    def _reset(self) -> None:
        self.name_edit.setText(self._seed.name)
        for token, edit in self.color_edits.items():
            edit.setText(self._seed.colors[token])

    def _finish(self, apply: bool) -> None:
        try:
            self._result_theme = self._draft()
        except ThemeValidationError as exc:
            self.error_label.setText(str(exc))
            return
        self.apply_after_save = apply
        self.accept()

    def _save(self) -> None:
        self._finish(False)

    def _apply(self) -> None:
        self._finish(True)


class ThemeGalleryDialog(QDialog):
    """Shows native/user themes and opens detached editing and file actions."""

    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("Temas do Auralume")
        self.setMinimumSize(860, 590)
        self.resize(980, 680)
        self.preview_theme = manager.active_theme
        self._build()
        self.manager.theme_changed.connect(self._refresh)
        self._refresh()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        intro = QLabel("Escolha uma aparência ou crie um tema seu. A prévia não altera o aplicativo até você aplicar.")
        intro.setWordWrap(True)
        root.addWidget(intro)
        body = QHBoxLayout()
        self.theme_list = QListWidget()
        self.theme_list.setObjectName("themeList")
        self.theme_list.setAccessibleName("Temas disponíveis")
        self.theme_list.setMinimumWidth(220)
        self.theme_list.currentItemChanged.connect(self._selection_changed)
        body.addWidget(self.theme_list)
        self.preview_widget = QWidget()
        self.preview_widget.setObjectName("themePreview")
        preview_layout = QVBoxLayout(self.preview_widget)
        preview_layout.setContentsMargins(20, 18, 20, 18)
        self.preview_name = QLabel()
        self.preview_name.setObjectName("pageTitle")
        self.preview_name.setWordWrap(True)
        preview_layout.addWidget(self.preview_name)
        self.preview_sidebar = QFrame()
        self.preview_sidebar.setObjectName("sidebar")
        side = QVBoxLayout(self.preview_sidebar)
        side.addWidget(QLabel("AURALUME"))
        side.addWidget(QLabel("Início  ·  Biblioteca  ·  Favoritos"))
        preview_layout.addWidget(self.preview_sidebar)
        self.preview_card = QFrame()
        self.preview_card.setObjectName("trackCard")
        card = QVBoxLayout(self.preview_card)
        self.preview_track = QLabel("Uma tarde tranquila")
        self.preview_track.setObjectName("cardTitle")
        self.preview_artist = QLabel("Artista de exemplo")
        self.preview_artist.setObjectName("mutedText")
        card.addWidget(self.preview_track)
        card.addWidget(self.preview_artist)
        preview_layout.addWidget(self.preview_card)
        self.preview_button = QPushButton("Reproduzir")
        self.preview_button.setObjectName("primaryButton")
        preview_layout.addWidget(self.preview_button)
        preview_layout.addStretch(1)
        body.addWidget(self.preview_widget, 1)
        root.addLayout(body, 1)

        actions = QGridLayout()
        self.create_button = self._button("Criar meu tema", "createThemeButton", self._create_theme)
        self.duplicate_button = self._button("Duplicar", "duplicateThemeButton", self._duplicate_theme)
        self.edit_button = self._button("Editar", "editThemeButton", self._edit_theme)
        self.rename_button = self._button("Renomear", "renameThemeButton", self._rename_theme)
        self.delete_button = self._button("Excluir", "deleteThemeButton", self._delete_theme)
        self.import_button = self._button("Importar…", "importThemeButton", self._import_theme)
        self.export_button = self._button("Exportar…", "exportThemeButton", self._export_theme)
        actions.addWidget(self.create_button, 0, 0)
        actions.addWidget(self.duplicate_button, 0, 1)
        actions.addWidget(self.edit_button, 0, 2)
        actions.addWidget(self.rename_button, 0, 3)
        actions.addWidget(self.delete_button, 1, 0)
        actions.addWidget(self.import_button, 1, 1)
        actions.addWidget(self.export_button, 1, 2)
        self.apply_button = QPushButton("Aplicar tema")
        self.apply_button.setObjectName("applyThemeButton")
        self.apply_button.clicked.connect(self._apply_theme)
        actions.addWidget(self.apply_button, 1, 3)
        self.close_button = QPushButton("Fechar")
        self.close_button.setObjectName("closeThemeGalleryButton")
        self.close_button.clicked.connect(self.reject)
        actions.addWidget(self.close_button, 1, 4)
        root.addLayout(actions)

    @staticmethod
    def _button(text, object_name, callback):
        button = QPushButton(text)
        button.setObjectName(object_name)
        button.clicked.connect(callback)
        return button

    def _selected(self) -> ThemeDefinition:
        item = self.theme_list.currentItem()
        theme_id = str(item.data(Qt.ItemDataRole.UserRole)) if item else self.manager.active_theme.id
        return next((theme for theme in self.manager.themes() if theme.id == theme_id), self.manager.active_theme)

    def _refresh(self, *_args) -> None:
        selected_id = self._selected().id if self.theme_list.count() else self.manager.active_theme.id
        self.theme_list.blockSignals(True)
        self.theme_list.clear()
        selected_row = 0
        for index, theme in enumerate(self.manager.themes()):
            active = theme.id == self.manager.active_theme.id
            marker = "  ·  Ativo" if active else ""
            item = QListWidgetItem(f"{theme.name}{marker}")
            item.setData(Qt.ItemDataRole.UserRole, theme.id)
            item.setData(Qt.ItemDataRole.AccessibleTextRole,
                         f"{theme.name}" + (", tema ativo" if active else ""))
            self.theme_list.addItem(item)
            if theme.id == selected_id:
                selected_row = index
        self.theme_list.setCurrentRow(selected_row)
        self.theme_list.blockSignals(False)
        self._selection_changed(self.theme_list.currentItem(), None)

    def _selection_changed(self, current, _previous) -> None:
        if current is None:
            return
        self.preview_theme = self._selected()
        self.preview_widget.setStyleSheet(stylesheet(self.preview_theme))
        self.preview_widget.setPalette(palette(self.preview_theme))
        self.preview_widget.setAutoFillBackground(True)
        self.preview_name.setText(self.preview_theme.name)
        self.preview_widget.setAccessibleName(f"Prévia do tema {self.preview_theme.name}")
        user_theme = self.preview_theme.id not in {theme.id for theme in PRESETS}
        self.edit_button.setEnabled(user_theme)
        self.rename_button.setEnabled(user_theme)
        self.delete_button.setEnabled(user_theme)
        self.export_button.setEnabled(True)

    def _apply_theme(self) -> None:
        try:
            self.manager.set_active(self._selected().id)
        except Exception as exc:
            self._show_error(str(exc))
            return
        self.accept()

    def _editor(self, source: ThemeDefinition, *, is_new: bool = False, draft_name: str | None = None):
        seed = source
        if is_new:
            name = self._suggest_name(draft_name or "Meu tema")
            seed = ThemeDefinition(self._draft_id(name), name, source.colors, source.author)
        editor = ThemeEditorDialog(seed, self, is_new=is_new)
        while editor.exec() == QDialog.DialogCode.Accepted and editor.result_theme() is not None:
            try:
                saved = self.manager.save(editor.result_theme())
                if editor.apply_after_save:
                    self.manager.set_active(saved.id)
                self._refresh()
                self._select_id(saved.id)
                return
            except Exception as exc:
                editor.error_label.setText(str(exc))
                editor.setResult(0)

    def _suggest_name(self, base: str) -> str:
        existing = {theme.name.casefold() for theme in self.manager.themes()}
        candidate = base[:60]
        index = 2
        while candidate.casefold() in existing:
            suffix = " (cópia)" if index == 2 else f" (cópia {index - 1})"
            candidate = base[:60 - len(suffix)] + suffix
            index += 1
        return candidate

    @staticmethod
    def _draft_id(name: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:32] or "theme"
        return f"custom-{slug}-{secrets.token_hex(4)}"

    def _select_id(self, theme_id: str) -> None:
        for row in range(self.theme_list.count()):
            if self.theme_list.item(row).data(Qt.ItemDataRole.UserRole) == theme_id:
                self.theme_list.setCurrentRow(row)
                return

    def _create_theme(self) -> None:
        self._editor(self._selected(), is_new=True, draft_name="Meu tema")

    def _duplicate_theme(self) -> None:
        theme = self._selected()
        self._editor(theme, is_new=True, draft_name=f"{theme.name} (cópia)")

    def _edit_theme(self) -> None:
        theme = self._selected()
        if theme.id in {preset.id for preset in PRESETS}:
            return
        self._editor(theme)

    def _rename_theme(self) -> None:
        theme = self._selected()
        name, accepted = QInputDialog.getText(self, "Renomear tema", "Nome", text=theme.name)
        if accepted:
            try:
                renamed = self.manager.rename(theme.id, name)
                self._refresh()
                self._select_id(renamed.id)
            except Exception as exc:
                self._show_error(str(exc))

    def _delete_theme(self) -> None:
        theme = self._selected()
        answer = QMessageBox.question(
            self, "Excluir tema", f"Excluir ‘{theme.name}’?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.manager.delete(theme.id)
            self._refresh()
        except Exception as exc:
            self._show_error(str(exc))

    def _import_theme(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Importar tema", "", "Temas Auralume (*.json);;JSON (*.json)")
        if not path:
            return
        try:
            with open(path, "rb") as source:
                data = source.read(MAX_JSON_BYTES + 1)
            if len(data) > MAX_JSON_BYTES:
                raise ThemeValidationError("O arquivo de tema excede o limite de 64 KiB.")
            incoming = ThemeDefinition.from_json(data)
            collision = any(
                theme.id == incoming.id or theme.name.casefold() == incoming.name.casefold()
                for theme in self.manager.themes()
            )
            conflict = "reject"
            if collision:
                answer = QMessageBox.question(self, "Tema já existe", "Importar este tema como uma cópia segura?")
                if answer != QMessageBox.StandardButton.Yes:
                    return
                conflict = "copy"
            imported = self.manager.import_json(data, conflict=conflict)
            self._refresh()
            self._select_id(imported.id)
        except Exception as exc:
            self._show_error(str(exc))

    def _export_theme(self) -> None:
        theme = self._selected()
        path, _ = QFileDialog.getSaveFileName(self, "Exportar tema", f"{theme.id}.json", "JSON (*.json)")
        if not path:
            return
        if not path.lower().endswith(".json"):
            path += ".json"
        try:
            with open(path, "w", encoding="utf-8", newline="\n") as target:
                target.write(self.manager.export_json(theme.id))
        except Exception as exc:
            self._show_error(str(exc))

    def _show_error(self, message: str) -> None:
        QMessageBox.warning(self, "Temas do Auralume", message)
