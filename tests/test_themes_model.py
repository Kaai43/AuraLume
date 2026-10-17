import json

import pytest

from auralume.themes import PRESETS, ThemeDefinition, ThemeValidationError


def valid_document(**overrides):
    colors = dict(PRESETS[0].colors)
    document = {
        "schema_version": 1,
        "id": "community-theme",
        "name": "Community Theme",
        "colors": colors,
    }
    document.update(overrides)
    return document


def test_preset_catalog_has_five_named_immutable_themes():
    assert [theme.name for theme in PRESETS] == [
        "Auralume Original",
        "Midnight Blue",
        "Rose Velvet",
        "Forest",
        "Soft Daylight",
    ]
    assert len({theme.id for theme in PRESETS}) == 5
    with pytest.raises(TypeError):
        PRESETS[0].colors["background"] = "#FFFFFF"


def test_json_round_trip_is_canonical_and_keeps_optional_author():
    theme = ThemeDefinition.from_json(json.dumps(valid_document(author="Auralume user")))

    encoded = theme.to_json()

    assert ThemeDefinition.from_json(encoded) == theme
    assert json.loads(encoded)["author"] == "Auralume user"
    assert encoded.endswith("\n")


@pytest.mark.parametrize(
    "overrides",
    [
        {"schema_version": 2},
        {"schema_version": True},
        {"id": "../unsafe"},
        {"id": "A theme"},
        {"name": "  "},
        {"author": "x" * 81},
        {"extra": "unexpected"},
        {"qss": "QWidget { color: red }"},
    ],
)
def test_parser_rejects_invalid_metadata_and_unknown_fields(overrides):
    with pytest.raises(ThemeValidationError):
        ThemeDefinition.from_json(json.dumps(valid_document(**overrides)))


def test_parser_rejects_missing_extra_and_non_hex_colors():
    missing = valid_document()
    del missing["colors"]["focus"]
    extra = valid_document()
    extra["colors"]["external_url"] = "https://example.org"
    malformed = valid_document()
    malformed["colors"]["accent"] = "red"

    for document in (missing, extra, malformed):
        with pytest.raises(ThemeValidationError):
            ThemeDefinition.from_json(json.dumps(document))


def test_parser_rejects_oversized_json_duplicate_keys_and_deep_json():
    duplicate_key = '{"schema_version":1,"schema_version":1}'
    too_deep = json.dumps(valid_document())[:-1] + ', "nested": {"child": {}}}'

    for raw in (b" " * (64 * 1024 + 1), duplicate_key, too_deep):
        with pytest.raises(ThemeValidationError):
            ThemeDefinition.from_json(raw)


def test_parser_requires_utf8_json_object():
    for raw in (b"\xff", b"[]", b"null"):
        with pytest.raises(ThemeValidationError):
            ThemeDefinition.from_json(raw)


@pytest.mark.parametrize("author", [None, "bad\x7fcontrol", "bad\ud800surrogate"])
def test_parser_rejects_invalid_present_author_values(author):
    with pytest.raises(ThemeValidationError):
        ThemeDefinition.from_json(json.dumps(valid_document(author=author)))


def test_parser_rejects_c1_controls_in_name_and_author():
    with pytest.raises(ThemeValidationError):
        ThemeDefinition.from_json(json.dumps(valid_document(name="bad\u0085name")))
    with pytest.raises(ThemeValidationError):
        ThemeDefinition.from_json(json.dumps(valid_document(author="bad\u009f")))


def test_serialization_sorts_keys_for_canonical_json():
    theme = ThemeDefinition.from_json(json.dumps(valid_document()))
    encoded = theme.to_json()

    document = json.loads(encoded)
    assert list(document) == sorted(document)
    assert list(document["colors"]) == sorted(document["colors"])
