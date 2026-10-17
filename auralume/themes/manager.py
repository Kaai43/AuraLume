"""Theme catalog and persistence independent from playback and widgets."""

from __future__ import annotations

import json
import re
import secrets
import unicodedata

from PySide6.QtCore import QObject, Signal

from .catalog import PRESETS
from .model import ThemeDefinition, ThemeValidationError


class ThemeManager(QObject):
    """Owns presets, user themes, active selection and one settings snapshot."""

    theme_changed = Signal(object)
    SETTING_KEY = "themes_v1"

    def __init__(self, settings=None):
        super().__init__()
        self._settings = settings
        self._memory_settings = {}
        self._custom: list[ThemeDefinition] = []
        self._active_id = PRESETS[0].id
        self.warning = ""
        self._load()

    @property
    def active_theme(self) -> ThemeDefinition:
        return self._find(self._active_id)

    def themes(self) -> list[ThemeDefinition]:
        return [*PRESETS, *self._custom]

    def set_active(self, theme_id: str) -> ThemeDefinition:
        theme = self._find(theme_id)
        if theme.id == self._active_id:
            return theme
        self._persist(self._custom, theme.id)
        self._active_id = theme.id
        self.theme_changed.emit(theme)
        return theme

    def save(self, theme: ThemeDefinition) -> ThemeDefinition:
        if not isinstance(theme, ThemeDefinition):
            raise ThemeValidationError("Informe uma definição de tema válida.")
        existing_by_id = next((item for item in self._custom if item.id == theme.id), None)
        if any(item.id == theme.id for item in PRESETS):
            raise ThemeValidationError("Temas nativos não podem ser substituídos.")
        for item in self.themes():
            if item.id != theme.id and item.name.casefold() == theme.name.casefold():
                raise ThemeValidationError("Já existe um tema com esse nome.")
        custom = list(self._custom)
        if existing_by_id is None:
            custom.append(theme)
        else:
            custom[custom.index(existing_by_id)] = theme
        self._persist(custom, self._active_id)
        self._custom = custom
        if self._active_id == theme.id and existing_by_id != theme:
            self.theme_changed.emit(theme)
        return theme

    def duplicate(self, theme_id: str, name: str) -> ThemeDefinition:
        source = self._find(theme_id)
        safe_name = self._validated_name(name)
        self._ensure_name_available(safe_name)
        duplicate = ThemeDefinition(self._new_id(safe_name), safe_name, source.colors, source.author)
        return self.save(duplicate)

    def rename(self, theme_id: str, name: str) -> ThemeDefinition:
        source = self._find(theme_id)
        if source in PRESETS:
            raise ThemeValidationError("Temas nativos não podem ser renomeados.")
        safe_name = self._validated_name(name)
        self._ensure_name_available(safe_name, except_id=theme_id)
        renamed = ThemeDefinition(source.id, safe_name, source.colors, source.author)
        return self.save(renamed)

    def delete(self, theme_id: str) -> None:
        source = self._find(theme_id)
        if source in PRESETS:
            raise ThemeValidationError("Temas nativos não podem ser excluídos.")
        custom = [item for item in self._custom if item.id != theme_id]
        new_active = PRESETS[0].id if self._active_id == theme_id else self._active_id
        self._persist(custom, new_active)
        self._custom = custom
        changed = new_active != self._active_id
        self._active_id = new_active
        if changed:
            self.theme_changed.emit(self.active_theme)

    def import_json(self, data: str | bytes | bytearray, conflict: str = "reject") -> ThemeDefinition:
        if conflict not in ("reject", "copy"):
            raise ThemeValidationError("A política de colisão deve ser reject ou copy.")
        theme = ThemeDefinition.from_json(data)
        collision = any(
            item.id == theme.id or item.name.casefold() == theme.name.casefold()
            for item in self.themes()
        )
        if collision:
            if conflict == "reject":
                raise ThemeValidationError("Já existe um tema com esse identificador ou nome.")
            theme = ThemeDefinition(self._new_id(theme.name), self._copy_name(theme.name), theme.colors, theme.author)
        return self.save(theme)

    def export_json(self, theme_id: str) -> str:
        return self._find(theme_id).to_json()

    def _find(self, theme_id: str) -> ThemeDefinition:
        for theme in self.themes():
            if theme.id == theme_id:
                return theme
        raise ThemeValidationError("O tema selecionado não existe.")

    @staticmethod
    def _validated_name(name: str) -> str:
        if not isinstance(name, str):
            raise ThemeValidationError("O nome do tema deve ser texto.")
        safe_name = name.strip()
        if not safe_name or len(safe_name) > 60 or any(ord(char) < 32 for char in safe_name):
            raise ThemeValidationError("O nome deve ter de 1 a 60 caracteres imprimíveis.")
        return safe_name

    def _ensure_name_available(self, name: str, except_id: str | None = None) -> None:
        if any(item.id != except_id and item.name.casefold() == name.casefold() for item in self.themes()):
            raise ThemeValidationError("Já existe um tema com esse nome.")

    def _copy_name(self, name: str) -> str:
        base = self._validated_name(name)
        suffix = " (cópia)"
        candidate = base[:60 - len(suffix)] + suffix
        index = 2
        while any(item.name.casefold() == candidate.casefold() for item in self.themes()):
            suffix = f" (cópia {index})"
            candidate = base[:60 - len(suffix)] + suffix
            index += 1
        return candidate

    @staticmethod
    def _new_id(name: str) -> str:
        normalized = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii").lower()
        slug = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")[:32] or "theme"
        return f"custom-{slug}-{secrets.token_hex(4)}"

    def _get_saved_state(self):
        if self._settings is None:
            return self._memory_settings.get(self.SETTING_KEY)
        return self._settings.get_setting(self.SETTING_KEY)

    def _write_saved_state(self, state):
        if self._settings is None:
            self._memory_settings[self.SETTING_KEY] = state
        else:
            self._settings.set_setting(self.SETTING_KEY, state)

    def _persist(self, custom: list[ThemeDefinition], active_id: str) -> None:
        state = {
            "schema_version": 1,
            "active_id": active_id,
            "custom": [json.loads(theme.to_json()) for theme in custom],
        }
        try:
            self._write_saved_state(state)
        except Exception as exc:
            self.warning = f"Não foi possível salvar os temas: {exc}"
            raise
        self.warning = ""

    def _load(self) -> None:
        try:
            state = self._get_saved_state()
            if state is None:
                return
            if not isinstance(state, dict):
                raise ThemeValidationError("Formato salvo de temas inválido.")
            warnings = []
            force_original = False
            if set(state) != {"schema_version", "active_id", "custom"}:
                warnings.append("campos do estado salvo estão ausentes ou desconhecidos")
                force_original = True
            if type(state.get("schema_version")) is not int or state.get("schema_version") != 1:
                warnings.append("versão salva de temas não suportada")
                force_original = True
            raw_custom = state.get("custom", [])
            if not isinstance(raw_custom, list):
                warnings.append("lista de temas personalizados inválida")
                raw_custom = []
                force_original = True
            custom = []
            all_themes = list(PRESETS)
            for index, item in enumerate(raw_custom):
                try:
                    theme = ThemeDefinition.from_json(json.dumps(item, ensure_ascii=False))
                    if any(existing.id == theme.id or existing.name.casefold() == theme.name.casefold()
                           for existing in all_themes):
                        raise ThemeValidationError("identificador ou nome repetido")
                    custom.append(theme)
                    all_themes.append(theme)
                except Exception as exc:
                    warnings.append(f"tema personalizado {index + 1} inválido: {exc}")
            active_id = state.get("active_id", PRESETS[0].id)
            if not isinstance(active_id, str) or active_id not in {theme.id for theme in all_themes}:
                warnings.append("tema ativo salvo não existe; Auralume Original foi selecionado")
                force_original = True
            if force_original:
                active_id = PRESETS[0].id
            self._custom = custom
            self._active_id = active_id
            if warnings:
                self.warning = "Temas carregados com recuperação parcial: " + "; ".join(warnings)
        except Exception as exc:
            self._custom = []
            self._active_id = PRESETS[0].id
            self.warning = f"Os temas salvos não puderam ser carregados. Auralume Original foi restaurado: {exc}"
