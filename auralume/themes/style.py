"""Qt palette and QSS generated entirely from semantic theme tokens."""

from PySide6.QtGui import QColor, QPalette


def stylesheet(theme) -> str:
    c = theme.colors
    return f"""
    QWidget {{ background: {c['background']}; color: {c['text_primary']};
        font-family: 'DejaVu Sans'; font-size: 13px; }}
    QWidget:disabled {{ color: {c['text_disabled']}; }}
    QCheckBox {{ background: transparent; spacing: 9px; }}
    #brand, #mutedText, #pageTitle, #eyebrow, #heroTitle, #sectionTitle,
    #cardTitle, #nowTitle, #timeLabel, #collectionTitle {{ background: transparent; }}
    #sidebar {{ background: {c['sidebar']}; border-right: 1px solid {c['border']}; }}
    #brand {{ color: {c['accent']}; font-size: 20px; font-weight: 800; letter-spacing: 2px; }}
    #mutedText, #timeLabel {{ color: {c['text_secondary']}; }}
    #navButton {{ text-align: left; padding: 11px 12px; border: 0; border-radius: 8px;
        color: {c['text_secondary']}; background: transparent; }}
    #navButton:hover {{ background: {c['surface_alt']}; color: {c['text_primary']}; }}
    #navButton:checked {{ background: {c['selection']}; color: {c['text_primary']};
        border-left: 3px solid {c['accent']}; font-weight: 700; }}
    #navButton:focus {{ border: 1px solid {c['focus']}; }}
    QPushButton {{ background: {c['surface_alt']}; border: 1px solid {c['border']};
        border-radius: 8px; padding: 8px 12px; }}
    QPushButton:hover {{ background: {c['card_hover']}; border-color: {c['focus']}; }}
    QPushButton:pressed {{ background: {c['selection']}; }}
    QPushButton:focus, QLineEdit:focus, QSpinBox:focus, QComboBox:focus,
    QListWidget:focus, QTableWidget:focus {{ border: 1px solid {c['focus']}; }}
    #primaryButton, #playButton {{ background: {c['accent']}; color: {c['accent_foreground']};
        border: 0; font-weight: 800; }}
    #primaryButton:hover, #playButton:hover {{ background: {c['accent_hover']}; }}
    #primaryButton:focus, #playButton:focus {{ border: 1px solid {c['focus']}; }}
    #playButton {{ border-radius: 19px; min-width: 38px; max-width: 38px;
        min-height: 38px; max-height: 38px; padding: 0; font-size: 16px; }}
    #playerBar {{ background: {c['player_background']}; border-top: 1px solid {c['border']}; }}
    #nowTitle {{ font-weight: 700; }}
    #playerToggle:checked {{ color: {c['accent']}; border-color: {c['accent']}; }}
    #pageTitle {{ color: {c['text_primary']}; font-size: 26px; font-weight: 750; }}
    #searchInput {{ color: {c['text_primary']}; background: {c['surface']};
        border: 1px solid {c['border']}; border-radius: 8px; padding: 9px; }}
    #heroPanel {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 {c['hero_start']}, stop:0.55 {c['hero_middle']}, stop:1 {c['hero_end']});
        border: 1px solid {c['border']}; border-radius: 16px; }}
    #eyebrow {{ color: {c['accent']}; font-size: 10px; font-weight: 800; letter-spacing: 1.7px; }}
    #heroTitle {{ font-size: 24px; font-weight: 750; }}
    #sectionTitle {{ font-size: 12px; font-weight: 800; letter-spacing: 1.1px;
        color: {c['text_primary']}; }}
    #collectionTitle {{ color: {c['text_primary']}; font-size: 17px; font-weight: 700; }}
    #shortcutCard {{ min-height: 70px; text-align: left; font-size: 15px; font-weight: 700;
        background: {c['surface_alt']}; }}
    #shortcutCard[destination="library"] {{ border-left: 3px solid {c['accent']}; }}
    #shortcutCard[destination="recommendations"] {{ border-left: 3px solid {c['focus']}; }}
    #shortcutCard[destination="favorites"] {{ border-left: 3px solid {c['error']}; }}
    #trackCard {{ background: {c['card_background']}; border: 1px solid {c['border']}; border-radius: 12px; }}
    #trackCard:hover {{ background: {c['card_hover']}; border-color: {c['focus']}; }}
    #cardTitle {{ font-weight: 700; }}
    #trackTable {{ background: transparent; alternate-background-color: {c['surface']};
        border: 0; selection-background-color: {c['selection']}; }}
    #trackTable::item {{ padding: 8px; border-bottom: 1px solid {c['border']}; }}
    QHeaderView::section {{ background: transparent; color: {c['text_secondary']}; border: 0;
        border-bottom: 1px solid {c['border']}; padding: 9px 8px; font-size: 10px; font-weight: 800; }}
    QLineEdit, QSpinBox, QComboBox, QListWidget {{ background: {c['surface']};
        border: 1px solid {c['border']}; border-radius: 8px; padding: 9px;
        selection-background-color: {c['selection']}; }}
    QComboBox QAbstractItemView {{ background: {c['menu_background']};
        selection-background-color: {c['selection']}; }}
    QSlider::groove:horizontal {{ height: 4px; background: {c['slider_track']}; border-radius: 2px; }}
    QSlider::sub-page:horizontal {{ background: {c['slider_fill']}; border-radius: 2px; }}
    QSlider::handle:horizontal {{ width: 12px; margin: -5px 0; background: {c['accent_hover']}; border-radius: 6px; }}
    #statusLabel {{ padding: 8px 12px; color: {c['warning']}; background: {c['surface_alt']}; border-radius: 7px; }}
    #statusLabel[error="true"] {{ color: {c['error']}; background: {c['surface_alt']}; }}
    #statusLabel[state="success"] {{ color: {c['success']}; }}
    #contrastWarning {{ color: {c['text_primary']}; background: {c['surface']};
        border: 1px solid {c['warning']}; border-radius: 6px; padding: 7px; }}
    #coverArt {{ background: transparent; border: 0; }}
    QScrollArea {{ border: 0; background: transparent; }}
    QScrollBar:vertical {{ background: {c['background']}; width: 8px; margin: 0; border: 0; }}
    QScrollBar::handle:vertical {{ background: {c['border']}; min-height: 28px; border-radius: 4px; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
    QMenu {{ background: {c['menu_background']}; border: 1px solid {c['border']}; }}
    QMenu::item {{ padding: 6px 22px; }}
    QMenu::item:selected {{ background: {c['selection']}; color: {c['text_primary']}; }}
    QToolTip {{ background: {c['menu_background']}; color: {c['text_primary']};
        border: 1px solid {c['border']}; padding: 5px; }}
    """


def palette(theme) -> QPalette:
    c = theme.colors
    result = QPalette()
    for group in (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive):
        result.setColor(group, QPalette.ColorRole.Window, QColor(c["background"]))
        result.setColor(group, QPalette.ColorRole.WindowText, QColor(c["text_primary"]))
        result.setColor(group, QPalette.ColorRole.Base, QColor(c["surface"]))
        result.setColor(group, QPalette.ColorRole.AlternateBase, QColor(c["surface_alt"]))
        result.setColor(group, QPalette.ColorRole.Text, QColor(c["text_primary"]))
        result.setColor(group, QPalette.ColorRole.Button, QColor(c["surface_alt"]))
        result.setColor(group, QPalette.ColorRole.ButtonText, QColor(c["text_primary"]))
        result.setColor(group, QPalette.ColorRole.Highlight, QColor(c["selection"]))
        result.setColor(group, QPalette.ColorRole.HighlightedText, QColor(c["text_primary"]))
        result.setColor(group, QPalette.ColorRole.ToolTipBase, QColor(c["menu_background"]))
        result.setColor(group, QPalette.ColorRole.ToolTipText, QColor(c["text_primary"]))
        result.setColor(group, QPalette.ColorRole.PlaceholderText, QColor(c["text_secondary"]))
        result.setColor(group, QPalette.ColorRole.BrightText, QColor(c["error"]))
        result.setColor(group, QPalette.ColorRole.Link, QColor(c["accent"]))
    for role in (QPalette.ColorRole.WindowText, QPalette.ColorRole.Text, QPalette.ColorRole.ButtonText):
        result.setColor(QPalette.ColorGroup.Disabled, role, QColor(c["text_disabled"]))
    result.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Window, QColor(c["background"]))
    result.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Base, QColor(c["surface"]))
    result.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Button, QColor(c["surface_alt"]))
    result.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Highlight, QColor(c["selection"]))
    return result
