"""Desktop entry point and explicit, isolated startup diagnostics."""
import argparse
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import sys
import tempfile
import time

from . import __version__


def main(argv=None):
    parser = argparse.ArgumentParser(description='Auralume — Your Music, Your Way')
    parser.add_argument('files', nargs='*', help='Arquivos ou pastas para importar')
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('--data-dir', type=Path, help='Pasta alternativa para dados locais')
    parser.add_argument('--diagnostics', action='store_true', help='Diagnóstico JSON sem abrir janela')
    parser.add_argument('--smoke-test', action='store_true', help='Verificar inicialização e encerrar automaticamente')
    parser.add_argument('--screenshot', type=Path, help='Salvar captura da janela durante smoke-test')
    parser.add_argument('--play', action='store_true', help='Reproduzir o primeiro arquivo importado')
    parser.add_argument('--authorized-source', help='Abrir URL cujo acesso e reprodução você autoriza')
    parser.add_argument('--audio-output', help='Saída mpv (ex.: null para diagnóstico silencioso)')
    args = parser.parse_args(argv)
    if args.authorized_source and args.files:
        parser.error('Use uma origem autorizada ou arquivos locais por invocação.')
    if args.diagnostics:
        from .diagnostics import environment_report
        report = environment_report()
        print(json.dumps(report, ensure_ascii=True))
        return 0 if report['native_mpv']['engine_created'] and not report['native_mpv']['error'] else 1
    if args.smoke_test:
        os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PySide6.QtCore import QTimer
    from PySide6.QtGui import QFont, QIcon
    from PySide6.QtWidgets import QApplication, QMessageBox
    from .controller import Controller
    from .database import Database
    from .player import MpvPlayer
    from .ui.main_window import MainWindow
    from .themes import ThemeManager
    from .paths import default_data_dir, resource_path

    app = QApplication.instance() or QApplication([sys.argv[0]])
    app.setApplicationName('Auralume')
    app.setOrganizationName('Auralume')
    app.setApplicationVersion(__version__)
    app.setFont(QFont('DejaVu Sans', 10))
    app.setWindowIcon(QIcon(str(resource_path('auralume.svg'))))
    temporary = tempfile.TemporaryDirectory(prefix='auralume-smoke-') if args.smoke_test and not args.data_dir else None
    data_dir = args.data_dir or (Path(temporary.name) if temporary else default_data_dir())
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(data_dir / 'auralume.log', maxBytes=500_000, backupCount=2)
        logging.basicConfig(level=logging.WARNING, handlers=[handler],
                            format='%(asctime)s %(levelname)s %(message)s', force=True)
        database = Database(data_dir / 'library.sqlite3')
    except Exception as error:
        message = f'Não foi possível abrir os dados locais: {error}'
        if args.smoke_test:
            print(json.dumps({'ok': False, 'error': message}, ensure_ascii=True))
        else:
            QMessageBox.critical(None, 'Auralume', message)
        return 1

    theme_manager = ThemeManager(database)
    window = MainWindow(theme_manager=theme_manager)
    player = MpvPlayer(audio_output=args.audio_output or ('null' if args.smoke_test else None))
    controller = Controller(window, database, player)
    if theme_manager.warning:
        window.set_status(theme_manager.warning)
    old_hook = sys.excepthook
    unhandled_errors = []

    def report_exception(exc_type, exc, traceback):
        logging.error('Unhandled application error', exc_info=(exc_type, exc, traceback))
        unhandled_errors.append(str(exc))
        window.set_status('Ocorreu um erro. Os detalhes estão no diagnóstico local.', error=True)

    sys.excepthook = report_exception
    window.show()
    if args.files:
        controller.import_paths(args.files, autoplay=args.play)
    elif args.authorized_source:
        controller.open_source(args.authorized_source)
    result_code = [0]
    if args.smoke_test:
        started = time.monotonic()
        monitor = QTimer(app)

        def verify():
            elapsed = time.monotonic() - started
            needs_playback = args.play or bool(args.authorized_source)
            ready = controller._busy == 0 and (not needs_playback or controller._loaded or bool(controller.last_error))
            if (ready and elapsed >= .5) or elapsed > 10:
                monitor.stop()
                ok = player.available and not controller.last_error and not unhandled_errors and ready
                if args.files:
                    ok = ok and bool(database.list_tracks())
                if needs_playback:
                    ok = ok and bool(database.history())
                if args.screenshot:
                    args.screenshot.parent.mkdir(parents=True, exist_ok=True)
                    ok = window.grab().save(str(args.screenshot)) and ok
                print(json.dumps({'ok': bool(ok), 'tracks': len(database.list_tracks()),
                                  'history': len(database.history()), 'player_available': player.available,
                                  'playback_started': controller._loaded,
                                  'error': controller.last_error}, ensure_ascii=True), flush=True)
                result_code[0] = 0 if ok else 1
                app.quit()
        monitor.timeout.connect(verify)
        monitor.start(100)
    try:
        app.exec()
    finally:
        controller.close()
        database.close()
        sys.excepthook = old_hook
        logging.shutdown()
        if temporary:
            temporary.cleanup()
    return result_code[0]
