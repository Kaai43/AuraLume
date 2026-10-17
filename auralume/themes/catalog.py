"""Built-in themes whose IDs are stable across app releases."""

from .model import ThemeDefinition


PRESETS = (
    ThemeDefinition("auralume-original", "Auralume Original", {
        "background": "#14131A", "sidebar": "#100F15", "surface": "#1D1A24",
        "surface_alt": "#201D27", "player_background": "#100F15",
        "text_primary": "#F4F0EA", "text_secondary": "#A7A1B0", "text_disabled": "#716C79",
        "accent": "#DCA756", "accent_hover": "#E9BE79", "accent_foreground": "#21170A",
        "border": "#393541", "selection": "#393047", "focus": "#F3D49A",
        "success": "#82C69A", "warning": "#E8CA90", "error": "#F0A1A1",
        "slider_track": "#48434F", "slider_fill": "#DCA756",
        "card_background": "#1D1A24", "card_hover": "#282431", "menu_background": "#211E29",
        "cover_start": "#7548A8", "cover_middle": "#3F497E", "cover_end": "#D79444",
        "cover_foreground": "#FFF5E4", "hero_start": "#34283D", "hero_middle": "#292637",
        "hero_end": "#423523",
    }),
    ThemeDefinition("midnight-blue", "Midnight Blue", {
        "background": "#101722", "sidebar": "#0B111B", "surface": "#182331",
        "surface_alt": "#1E2B3B", "player_background": "#0B111B",
        "text_primary": "#F2F6FC", "text_secondary": "#AAB9CC", "text_disabled": "#718096",
        "accent": "#69B9F2", "accent_hover": "#91D0FF", "accent_foreground": "#071A28",
        "border": "#334457", "selection": "#29445D", "focus": "#A4D8FF",
        "success": "#86D5A2", "warning": "#F2CE7D", "error": "#F39A9A",
        "slider_track": "#435367", "slider_fill": "#69B9F2",
        "card_background": "#182331", "card_hover": "#24364A", "menu_background": "#182331",
        "cover_start": "#285E92", "cover_middle": "#203D72", "cover_end": "#51A7C8",
        "cover_foreground": "#E9F7FF", "hero_start": "#19324B", "hero_middle": "#1A283F",
        "hero_end": "#203C4C",
    }),
    ThemeDefinition("rose-velvet", "Rose Velvet", {
        "background": "#20151D", "sidebar": "#180F16", "surface": "#2C1E29",
        "surface_alt": "#35232F", "player_background": "#180F16",
        "text_primary": "#FFF1F4", "text_secondary": "#D0B5C0", "text_disabled": "#927B86",
        "accent": "#E58AA8", "accent_hover": "#F1ADC1", "accent_foreground": "#32131F",
        "border": "#553B4A", "selection": "#553244", "focus": "#F2B8CA",
        "success": "#8ED0A5", "warning": "#EBCB86", "error": "#F3979B",
        "slider_track": "#5A4653", "slider_fill": "#E58AA8",
        "card_background": "#2C1E29", "card_hover": "#3B2836", "menu_background": "#2C1E29",
        "cover_start": "#A74772", "cover_middle": "#6A3D6C", "cover_end": "#E8A86F",
        "cover_foreground": "#FFF2E8", "hero_start": "#42263A", "hero_middle": "#352337",
        "hero_end": "#4A2B37",
    }),
    ThemeDefinition("forest", "Forest", {
        "background": "#131A17", "sidebar": "#0D1411", "surface": "#1B2620",
        "surface_alt": "#233129", "player_background": "#0D1411",
        "text_primary": "#F0F5F0", "text_secondary": "#AEBBAF", "text_disabled": "#748277",
        "accent": "#8FCB8D", "accent_hover": "#B1E3A7", "accent_foreground": "#102112",
        "border": "#3C5042", "selection": "#2D4937", "focus": "#B7E9B2",
        "success": "#8FCB8D", "warning": "#E6C982", "error": "#EB9993",
        "slider_track": "#4A5A4D", "slider_fill": "#8FCB8D",
        "card_background": "#1B2620", "card_hover": "#28392D", "menu_background": "#1B2620",
        "cover_start": "#42775A", "cover_middle": "#355D52", "cover_end": "#B3A75B",
        "cover_foreground": "#F4F6D8", "hero_start": "#233C2D", "hero_middle": "#20332E",
        "hero_end": "#3B4930",
    }),
    ThemeDefinition("soft-daylight", "Soft Daylight", {
        "background": "#F3F1ED", "sidebar": "#E8E5DF", "surface": "#FBFAF8",
        "surface_alt": "#EDEAE4", "player_background": "#E6E2DC",
        "text_primary": "#25232A", "text_secondary": "#57535D", "text_disabled": "#77737C",
        "accent": "#80501C", "accent_hover": "#663D13", "accent_foreground": "#FFFFFF",
        "border": "#C8C3BB", "selection": "#D4C4E3", "focus": "#5C3483",
        "success": "#28623D", "warning": "#76500B", "error": "#8C2929",
        "slider_track": "#B8B2AA", "slider_fill": "#80501C",
        "card_background": "#FBFAF8", "card_hover": "#EDE8E0", "menu_background": "#FBFAF8",
        "cover_start": "#77549B", "cover_middle": "#6476A2", "cover_end": "#BC7B3A",
        "cover_foreground": "#FFFFFF", "hero_start": "#E3D5E8", "hero_middle": "#DDDCEB",
        "hero_end": "#E9DDC8",
    }),
)


def get_presets() -> tuple[ThemeDefinition, ...]:
    return PRESETS
