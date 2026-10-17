import re

from auralume.themes import PRESETS
from auralume.themes.style import palette, stylesheet
from auralume.ui.theme_dialog import contrast_ratio


def test_stylesheet_derives_semantic_controls_from_theme_tokens():
    theme = PRESETS[0]

    generated = stylesheet(theme)

    assert theme.colors["background"] in generated
    assert theme.colors["accent"] in generated
    assert theme.colors["focus"] in generated
    assert theme.colors["menu_background"] in generated
    assert theme.colors["hero_start"] in generated
    assert theme.colors["cover_start"] not in generated  # CoverArt paints its gradient.
    assert set(re.findall(r"#[0-9A-Fa-f]{6}", generated)) <= set(theme.colors.values())
    assert "#navButton:focus" in generated
    assert "#primaryButton:focus" in generated
    assert "#playButton:focus" in generated
    assert "QToolTip" in generated


def test_palette_uses_theme_background_surface_text_and_accent():
    theme = PRESETS[0]

    generated = palette(theme)

    assert generated.color(generated.ColorRole.Window).name().upper() == theme.colors["background"]
    assert generated.color(generated.ColorRole.Base).name().upper() == theme.colors["surface"]
    assert generated.color(generated.ColorRole.WindowText).name().upper() == theme.colors["text_primary"]
    assert generated.color(generated.ColorRole.Highlight).name().upper() == theme.colors["selection"]


def test_text_combinations_used_by_native_presets_meet_wcag_contrast_target():
    text_backgrounds = (
        "background", "surface", "surface_alt", "sidebar", "player_background",
        "menu_background", "card_background", "card_hover", "selection", "hero_start",
        "hero_middle", "hero_end",
    )
    for theme in PRESETS:
        colors = theme.colors
        assert all(contrast_ratio(colors["text_primary"], colors[key]) >= 4.5 for key in text_backgrounds)
        assert all(contrast_ratio(colors["text_secondary"], colors[key]) >= 4.5
                   for key in ("background", "surface", "sidebar"))
        assert contrast_ratio(colors["accent_foreground"], colors["accent"]) >= 4.5
        assert contrast_ratio(colors["accent_foreground"], colors["accent_hover"]) >= 4.5
        assert all(contrast_ratio(colors[key], colors["surface_alt"]) >= 4.5
                   for key in ("success", "warning", "error"))
