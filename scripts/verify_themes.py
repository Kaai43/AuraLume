"""Render reproducible theme evidence without opening any user library."""
import argparse
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=Path('docs/evidence/themes'))
    args = parser.parse_args()
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import QApplication
    from auralume.models import Track
    from auralume.themes import ThemeManager
    from auralume.ui.main_window import MainWindow
    from auralume.ui.theme_dialog import ThemeEditorDialog, ThemeGalleryDialog

    app = QApplication.instance() or QApplication([])
    app.setFont(QFont('DejaVu Sans', 10))
    args.output.mkdir(parents=True, exist_ok=True)
    manager = ThemeManager()
    window = MainWindow(theme_manager=manager)
    # Metadata authored for this verification; no personal music/files loaded.
    tracks = [Track(f'evidence-{i}', f'/not-played-{i}.wav', title, artist='Auralume · Demonstração')
              for i, title in enumerate(('Luz da manhã', 'Horizonte azul', 'Uma tarde tranquila'))]
    artifacts = []

    def capture(widget, name, width, height):
        widget.resize(width, height)
        widget.show()
        app.processEvents()
        path = args.output / name
        if not widget.grab().save(str(path)):
            raise RuntimeError(f'Failed to save {path}')
        artifacts.append({'file': str(path), 'width': widget.width(), 'height': widget.height()})
        if widget.width() > width or widget.height() > height:
            raise RuntimeError(f'{name} exceeds requested size {width}x{height}: {widget.size()}')

    try:
        for theme in ('auralume-original', 'soft-daylight'):
            manager.set_active(theme)
            window.display_page('recommendations')
            window.show_tracks('Sua música', tracks)
            window.set_now_playing(tracks[0], False)
            for width, height in ((1240, 800), (980, 650)):
                capture(window, f'{theme}-{width}x{height}.png', width, height)
            gallery = ThemeGalleryDialog(manager, window)
            try:
                capture(gallery, f'{theme}-gallery.png', 980, 650)
            finally:
                gallery.close()
            editor = ThemeEditorDialog(manager.active_theme, window, is_new=True)
            try:
                capture(editor, f'{theme}-editor.png', 980, 650)
            finally:
                editor.close()
        report = {'qt_platform': app.platformName(), 'artifacts': artifacts,
                  'physical_audio_tested': False, 'user_data_opened': False}
        (args.output / 'render-report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report))
    finally:
        window.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
