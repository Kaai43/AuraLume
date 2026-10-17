import json

import pytest

from auralume.themes import PRESETS, ThemeDefinition, ThemeManager, ThemeValidationError


class MemorySettings:
    def __init__(self, value=None):
        self.values = {} if value is None else {"themes_v1": value}
        self.writes = []

    def get_setting(self, key, default=None):
        return self.values.get(key, default)

    def set_setting(self, key, value):
        self.writes.append((key, value))
        self.values[key] = value


def custom_theme(theme_id="my-theme", name="My Theme", accent="#CB8A46"):
    colors = dict(PRESETS[0].colors)
    colors["accent"] = accent
    return ThemeDefinition(theme_id, name, colors)


def test_manager_defaults_to_original_and_exposes_all_presets():
    manager = ThemeManager()

    assert manager.active_theme == PRESETS[0]
    assert manager.themes() == list(PRESETS)


def test_manager_persists_active_and_custom_themes_as_one_setting_and_reloads():
    settings = MemorySettings()
    manager = ThemeManager(settings)
    created = manager.save(custom_theme())
    manager.set_active(created.id)

    saved_state = settings.values["themes_v1"]
    reopened = ThemeManager(settings)

    assert [key for key, _ in settings.writes] == ["themes_v1", "themes_v1"]
    assert saved_state["schema_version"] == 1
    assert saved_state["active_id"] == "my-theme"
    assert [theme.id for theme in reopened.themes() if theme not in PRESETS] == ["my-theme"]
    assert reopened.active_theme == created


def test_manager_duplicate_rename_and_delete_are_user_theme_only():
    manager = ThemeManager()
    copy = manager.duplicate("auralume-original", "Original Custom")
    renamed = manager.rename(copy.id, "Renamed Theme")
    manager.set_active(renamed.id)

    manager.delete(renamed.id)

    assert manager.active_theme == PRESETS[0]
    assert all(theme.id != renamed.id for theme in manager.themes())
    with pytest.raises(ThemeValidationError):
        manager.rename("auralume-original", "Cannot Rename Preset")
    with pytest.raises(ThemeValidationError):
        manager.delete("auralume-original")


def test_manager_rejects_collisions_and_import_copy_uses_safe_new_identity():
    manager = ThemeManager()
    created = manager.save(custom_theme())

    with pytest.raises(ThemeValidationError):
        manager.save(custom_theme("other-id", created.name))
    with pytest.raises(ThemeValidationError):
        manager.import_json(created.to_json(), conflict="reject")

    copied = manager.import_json(created.to_json(), conflict="copy")

    assert copied.id != created.id
    assert copied.name != created.name
    assert copied.id.startswith("custom-")


def test_manager_round_trip_export_import_and_emits_active_theme_changes():
    manager = ThemeManager()
    created = manager.save(custom_theme())
    exported = manager.export_json(created.id)
    changed = []
    manager.theme_changed.connect(changed.append)

    manager.set_active(created.id)

    assert ThemeDefinition.from_json(exported) == created
    assert changed == [created]


def test_manager_corrupt_or_unknown_saved_state_falls_back_with_warning():
    settings = MemorySettings({"schema_version": 2, "active_id": "removed", "custom": []})

    manager = ThemeManager(settings)

    assert manager.active_theme == PRESETS[0]
    assert manager.warning
    assert settings.values["themes_v1"]["schema_version"] == 2


def test_manager_does_not_overwrite_settings_when_a_theme_mutation_fails():
    settings = MemorySettings()
    manager = ThemeManager(settings)

    with pytest.raises(ThemeValidationError):
        manager.set_active("missing-theme")

    assert settings.writes == []


def test_saving_changed_active_theme_persists_then_emits_updated_definition():
    settings = MemorySettings()
    manager = ThemeManager(settings)
    active = manager.save(custom_theme())
    manager.set_active(active.id)
    changed = []
    manager.theme_changed.connect(changed.append)
    edited = ThemeDefinition(active.id, active.name, {
        **active.colors,
        "accent": "#AA55CC",
    })

    manager.save(edited)

    assert manager.active_theme == edited
    assert changed == [edited]
    assert settings.values["themes_v1"]["custom"][0]["colors"]["accent"] == "#AA55CC"


def test_load_recovers_valid_custom_entries_from_partially_corrupt_state():
    valid = json.loads(custom_theme().to_json())
    state = {
        "schema_version": 1,
        "active_id": "missing-theme",
        "custom": [valid, {"schema_version": 1, "id": "broken"}],
    }
    settings = MemorySettings(state)

    manager = ThemeManager(settings)

    assert [theme.id for theme in manager.themes() if theme not in PRESETS] == ["my-theme"]
    assert manager.active_theme == PRESETS[0]
    assert manager.warning
    assert settings.writes == []


def test_unknown_saved_schema_preserves_custom_export_but_activates_original_without_write():
    custom = json.loads(custom_theme().to_json())
    state = {"schema_version": 99, "active_id": "soft-daylight", "custom": [custom]}
    settings = MemorySettings(state)

    manager = ThemeManager(settings)

    assert manager.active_theme == PRESETS[0]
    assert manager.export_json("my-theme")
    assert manager.warning
    assert settings.values["themes_v1"] == state
    assert settings.writes == []


def test_import_rejects_unknown_conflict_policy():
    manager = ThemeManager()

    with pytest.raises(ThemeValidationError):
        manager.import_json(custom_theme().to_json(), conflict="replace")
