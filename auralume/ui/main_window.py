"""The main Auralume window.

This module contains presentation and Qt signals only. Services and models are
provided by the application controller; model access is intentionally
duck-typed so the window can be created before any service is initialized.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QDesktopServices, QKeyEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHeaderView,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .widgets import CoverArt, ElidedLabel, TrackCard


PAGES = {
    "home": "Início",
    "recommendations": "Para Você",
    "search": "Pesquisar",
    "library": "Biblioteca",
    "playlists": "Playlists",
    "favorites": "Favoritos",
    "history": "Histórico",
    "settings": "Configurações",
}


class MainWindow(QMainWindow):
    """Service-free application shell; the controller connects the signals."""

    navigate = Signal(str)
    import_files_requested = Signal()
    import_folder_requested = Signal()
    search_requested = Signal(str)
    play_requested = Signal(str)
    favorite_requested = Signal(str)
    enqueue_requested = Signal(str)
    playlist_create_requested = Signal(str)
    playlist_selected = Signal(str)
    playlist_add_requested = Signal(str, str)
    playlist_remove_requested = Signal(str, str)
    playlist_delete_requested = Signal(str)
    play_pause_requested = Signal()
    next_requested = Signal()
    previous_requested = Signal()
    seek_requested = Signal(float)
    volume_requested = Signal(int)
    shuffle_requested = Signal(bool)
    repeat_requested = Signal(str)
    source_requested = Signal(str)
    preferences_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Auralume — Your Music, Your Way")
        self.setMinimumSize(980, 650)
        self.resize(1240, 800)
        self.current_page = "home"
        self._tracks: list[object] = []
        self._playlists: list[object] = []
        self._queue: list[object] = []
        self._page_track_tables: dict[str, QTableWidget] = {}
        self._page_card_layouts: dict[str, QHBoxLayout] = {}
        self._collection_labels: dict[str, QLabel] = {}
        self._selected_playlist_id = ""
        self._settings = (70, False, "off", "")
        self._duration = 0.0
        self._repeat = "off"
        self._build_shell()
        self.display_page("home")

    def showEvent(self, event) -> None:  # noqa: N802 - Qt virtual method
        super().showEvent(event)
        # Reapply the top controls after the native window becomes visible so
        # both Fusion and platform styles paint their foreground consistently.
        self.page_title.setStyleSheet("color: #F4F0EA; font-size: 26px; font-weight: 750;")
        self.search_input.setStyleSheet(
            "color: #F4F0EA; background: #1D1A24; border: 1px solid #393541; "
            "border-radius: 8px; padding: 9px;"
        )

    def _build_shell(self) -> None:
        central = QWidget(self)
        central.setObjectName("appRoot")
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        root.addLayout(body, 1)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(220)
        side = QVBoxLayout(self.sidebar)
        side.setContentsMargins(17, 21, 15, 18)
        side.setSpacing(7)
        brand = QLabel("AURALUME")
        brand.setObjectName("brand")
        side.addWidget(brand)
        tagline = QLabel("Your Music, Your Way")
        tagline.setObjectName("mutedText")
        side.addWidget(tagline)
        side.addSpacing(17)
        self.nav_buttons: dict[str, QPushButton] = {}
        for page, title in PAGES.items():
            button = QPushButton(title)
            button.setObjectName("navButton")
            button.setCheckable(True)
            button.setAccessibleName(title)
            button.clicked.connect(lambda checked=False, page_id=page: self._navigate(page_id))
            self.nav_buttons[page] = button
            side.addWidget(button)
        side.addStretch(1)
        self.import_file_button = QPushButton("＋  Importar arquivos")
        self.import_folder_button = QPushButton("▤  Importar pasta")
        self.import_file_button.clicked.connect(self.import_files_requested.emit)
        self.import_folder_button.clicked.connect(self.import_folder_requested.emit)
        self.import_file_button.setAccessibleName("Importar arquivos de música")
        self.import_folder_button.setAccessibleName("Importar pasta de música")
        self.open_source_button = QPushButton("↗  Abrir origem autorizada")
        self.open_source_button.setAccessibleName("Abrir uma origem autorizada")
        self.open_source_button.clicked.connect(self.open_source_dialog)
        side.addWidget(self.import_file_button)
        side.addWidget(self.import_folder_button)
        side.addWidget(self.open_source_button)
        body.addWidget(self.sidebar)

        content_shell = QWidget()
        content_shell.setObjectName("contentShell")
        content_layout = QVBoxLayout(content_shell)
        content_layout.setContentsMargins(27, 18, 27, 15)
        content_layout.setSpacing(16)
        top = QHBoxLayout()
        self.page_title = QLabel("Início")
        self.page_title.setObjectName("pageTitle")
        top.addWidget(self.page_title)
        top.addStretch(1)
        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText("Pesquisar na sua música…")
        self.search_input.setAccessibleName("Pesquisar na biblioteca")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setMaximumWidth(330)
        self.search_input.setMinimumWidth(260)
        self.search_input.returnPressed.connect(self._submit_search)
        top.addWidget(self.search_input)
        content_layout.addLayout(top)
        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        self.status_label.hide()
        content_layout.addWidget(self.status_label)
        self.page_stack = QStackedWidget()
        self.page_stack.setObjectName("pageStack")
        content_layout.addWidget(self.page_stack, 1)
        self.page_widgets: dict[str, QWidget] = {}
        body.addWidget(content_shell, 1)
        root.addWidget(self._build_player())
        self.setCentralWidget(central)
        self.setStyleSheet(self._stylesheet())
        self.search_input.setStyleSheet(
            "color: #F4F0EA; background: #1D1A24; border: 1px solid #393541; "
            "border-radius: 8px; padding: 9px;"
        )

    def _build_player(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("playerBar")
        outer = QVBoxLayout(bar)
        outer.setContentsMargins(19, 8, 19, 10)
        outer.setSpacing(5)
        controls = QHBoxLayout()
        controls.setSpacing(10)
        self.now_art = CoverArt(size=46)
        controls.addWidget(self.now_art)
        now = QVBoxLayout()
        self.now_title = ElidedLabel("Escolha uma música")
        self.now_title.setObjectName("nowTitle")
        self.now_artist = ElidedLabel("Sua biblioteca está pronta")
        self.now_artist.setObjectName("mutedText")
        now.addWidget(self.now_title)
        now.addWidget(self.now_artist)
        controls.addLayout(now, 2)
        self.shuffle_button = QPushButton("⤨")
        self.shuffle_button.setObjectName("playerToggle")
        self.shuffle_button.setCheckable(True)
        self.shuffle_button.setToolTip("Aleatório")
        self.shuffle_button.setAccessibleName("Reprodução aleatória")
        self.shuffle_button.toggled.connect(self.shuffle_requested.emit)
        controls.addWidget(self.shuffle_button)
        self.previous_button = QPushButton("⏮")
        self.previous_button.setToolTip("Anterior")
        self.previous_button.setAccessibleName("Faixa anterior")
        self.previous_button.clicked.connect(self.previous_requested.emit)
        controls.addWidget(self.previous_button)
        self.play_button = QPushButton("▶")
        self.play_button.setObjectName("playButton")
        self.play_button.setToolTip("Reproduzir ou pausar (Espaço)")
        self.play_button.setAccessibleName("Reproduzir")
        self.play_button.clicked.connect(self.play_pause_requested.emit)
        controls.addWidget(self.play_button)
        self.next_button = QPushButton("⏭")
        self.next_button.setToolTip("Próxima")
        self.next_button.setAccessibleName("Próxima faixa")
        self.next_button.clicked.connect(self.next_requested.emit)
        controls.addWidget(self.next_button)
        self.repeat_button = QPushButton("↻")
        self.repeat_button.setObjectName("playerToggle")
        self.repeat_button.setCheckable(True)
        self.repeat_button.setToolTip("Repetição: desativada")
        self.repeat_button.setAccessibleName("Modo de repetição")
        self.repeat_button.clicked.connect(self._cycle_repeat)
        controls.addWidget(self.repeat_button)
        controls.addStretch(1)
        self.queue_button = QPushButton("Fila")
        self.queue_button.setAccessibleName("Abrir fila de reprodução")
        self.queue_button.clicked.connect(lambda: self.show_queue(self._queue))
        controls.addWidget(self.queue_button)
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setObjectName("volumeSlider")
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.valueChanged.connect(self.volume_requested.emit)
        controls.addWidget(QLabel("Vol"))
        controls.addWidget(self.volume_slider)
        outer.addLayout(controls)
        progress = QHBoxLayout()
        self.position_label = QLabel("0:00")
        self.position_label.setObjectName("timeLabel")
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setObjectName("progressSlider")
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.sliderReleased.connect(self._seek_from_slider)
        self.duration_label = QLabel("0:00")
        self.duration_label.setObjectName("timeLabel")
        progress.addWidget(self.position_label)
        progress.addWidget(self.progress_slider, 1)
        progress.addWidget(self.duration_label)
        outer.addLayout(progress)
        return bar

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802 - Qt virtual method
        if isinstance(self.focusWidget(), QLineEdit):
            return super().keyPressEvent(event)
        key = event.key()
        modifiers = event.modifiers()
        control = bool(modifiers & Qt.KeyboardModifier.ControlModifier)
        shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)
        if key == Qt.Key.Key_Space and modifiers == Qt.KeyboardModifier.NoModifier:
            self.play_pause_requested.emit()
        elif control and key == Qt.Key.Key_F:
            self.search_input.setFocus()
        elif control and key == Qt.Key.Key_O and shift:
            self.import_folder_requested.emit()
        elif control and key == Qt.Key.Key_O:
            self.import_files_requested.emit()
        elif control and key == Qt.Key.Key_L:
            self.open_source_dialog()
        elif control and key in (Qt.Key.Key_1, Qt.Key.Key_2, Qt.Key.Key_3):
            page = {Qt.Key.Key_1: "home", Qt.Key.Key_2: "recommendations", Qt.Key.Key_3: "search"}[key]
            self._navigate(page)
        else:
            return super().keyPressEvent(event)
        event.accept()

    def _navigate(self, page: str) -> None:
        if page not in PAGES:
            return
        self.navigate.emit(page)
        self.display_page(page)

    def _submit_search(self) -> None:
        query = self.search_input.text().strip()
        if query:
            self.search_requested.emit(query)
            self._navigate("search")

    def display_page(self, page: str) -> None:
        """Select a page by its stable controller-facing id."""
        if page not in PAGES:
            return
        if page != "playlists":
            self._selected_playlist_id = ""
        self.current_page = page
        for page_id, button in self.nav_buttons.items():
            button.setChecked(page_id == page)
        self.page_title.setText(PAGES[page])
        if page not in self.page_widgets:
            widget = self._create_page(page)
            self.page_widgets[page] = widget
            self.page_stack.addWidget(widget)
        self.page_stack.setCurrentWidget(self.page_widgets[page])
        if page in self._page_track_tables:
            self.track_table = self._page_track_tables[page]
        if page in self._page_card_layouts:
            self.cards_layout = self._page_card_layouts[page]
        if page in self._collection_labels:
            label = self._collection_labels[page]
            label.setVisible(bool(label.text()) and page not in ("home", "recommendations"))
        self._refresh_page()

    def _create_page(self, page: str) -> QWidget:
        if page == "settings":
            return self._create_settings_page()
        if page == "playlists":
            return self._create_playlists_page()
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)
        if page in ("home", "recommendations"):
            hero = QFrame()
            hero.setObjectName("heroPanel")
            hero_layout = QVBoxLayout(hero)
            hero_layout.setContentsMargins(25, 22, 25, 23)
            hero_layout.setSpacing(8)
            eyebrow = QLabel("SUA MÚSICA, DO SEU JEITO")
            eyebrow.setObjectName("eyebrow")
            headline = QLabel("Descubra o próximo som que combina com você.")
            headline.setObjectName("heroTitle")
            headline.setWordWrap(True)
            detail = QLabel("Recomendações privadas, feitas a partir da sua biblioteca e do seu gosto.")
            detail.setObjectName("mutedText")
            detail.setWordWrap(True)
            hero_layout.addWidget(eyebrow)
            hero_layout.addWidget(headline)
            hero_layout.addWidget(detail)
            layout.addWidget(hero)
            if page == "home":
                row = QHBoxLayout()
                for label, target, color in (
                    ("Sua biblioteca", "library", "#D9A14A"),
                    ("Para Você", "recommendations", "#9D78D0"),
                    ("Seus favoritos", "favorites", "#C7788B"),
                ):
                    card = QPushButton(label)
                    card.setObjectName("shortcutCard")
                    card.setStyleSheet(f"border-left: 3px solid {color};")
                    card.clicked.connect(lambda checked=False, target=target: self._navigate(target))
                    row.addWidget(card)
                layout.addLayout(row)
        else:
            help_text = {
                "search": "Encontre uma música na biblioteca ou explore seus resultados.",
                "library": "Arquivos locais organizados em um só lugar.",
                "favorites": "As músicas que você guardou para ouvir de novo.",
                "history": "Continue de onde sua escuta parou.",
            }.get(page, "")
            description = QLabel(help_text)
            description.setObjectName("mutedText")
            layout.addWidget(description)
        if page in ("search", "library"):
            actions = QHBoxLayout()
            actions.addWidget(QLabel("MÚSICAS"), 1)
            add_file = QPushButton("Importar arquivos")
            add_folder = QPushButton("Importar pasta")
            add_file.clicked.connect(self.import_files_requested.emit)
            add_folder.clicked.connect(self.import_folder_requested.emit)
            actions.addWidget(add_file)
            actions.addWidget(add_folder)
            layout.addLayout(actions)
        if page in ("home", "recommendations"):
            section = QLabel("ESCOLHIDAS PARA VOCÊ" if page == "recommendations" else "TOCADAS RECENTEMENTE")
            section.setObjectName("sectionTitle")
            layout.addWidget(section)
            self.cards_scroll = QScrollArea()
            self.cards_scroll.setWidgetResizable(True)
            self.cards_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.cards_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.cards_widget = QWidget()
            self.cards_layout = QHBoxLayout(self.cards_widget)
            self.cards_layout.setContentsMargins(0, 0, 0, 6)
            self.cards_layout.setSpacing(12)
            self.cards_scroll.setWidget(self.cards_widget)
            self.cards_scroll.setFixedHeight(238)
            self._page_card_layouts[page] = self.cards_layout
            layout.addWidget(self.cards_scroll)
        self.collection_label = QLabel("")
        self.collection_label.setObjectName("collectionTitle")
        self.collection_label.hide()
        self._collection_labels[page] = self.collection_label
        layout.addWidget(self.collection_label)
        self.track_table = self._create_track_table(page)
        layout.addWidget(self.track_table, 1)
        return container

    def _create_track_table(self, page: str) -> QTableWidget:
        table = QTableWidget(0, 4)
        table.setObjectName("trackTable")
        table.setAccessibleName(f"Músicas em {PAGES[page]}")
        table.setHorizontalHeaderLabels(["TÍTULO", "ARTISTA", "ÁLBUM", "DURAÇÃO"])
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setShowGrid(False)
        table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        table.customContextMenuRequested.connect(self._show_track_menu)
        table.cellDoubleClicked.connect(self._play_table_row)
        header = table.horizontalHeader()
        header.setMinimumSectionSize(60)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        table.setTextElideMode(Qt.TextElideMode.ElideRight)
        self._page_track_tables[page] = table
        return table

    def _create_playlists_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        description = QLabel("Crie coleções locais para cada momento.")
        description.setObjectName("mutedText")
        layout.addWidget(description)
        top = QHBoxLayout()
        top.addWidget(QLabel("SUAS PLAYLISTS"), 1)
        create = QPushButton("＋  Nova playlist")
        create.clicked.connect(self._prompt_create_playlist)
        top.addWidget(create)
        layout.addLayout(top)
        self.playlist_list = QListWidget()
        self.playlist_list.setObjectName("playlistList")
        self.playlist_list.itemDoubleClicked.connect(self._select_playlist_item)
        self.playlist_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.playlist_list.customContextMenuRequested.connect(self._show_playlist_menu)
        layout.addWidget(self.playlist_list, 1)
        self.collection_label = QLabel("")
        self.collection_label.setObjectName("collectionTitle")
        self.collection_label.hide()
        self._collection_labels["playlists"] = self.collection_label
        layout.addWidget(self.collection_label)
        self.track_table = self._create_track_table("playlists")
        layout.addWidget(self.track_table, 2)
        return page

    def _create_settings_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        info = QLabel("Ajuste sua experiência. Suas preferências ficam neste dispositivo.")
        info.setObjectName("mutedText")
        layout.addWidget(info)
        form = QFormLayout()
        self.settings_volume = QSpinBox()
        self.settings_volume.setRange(0, 100)
        self.settings_volume.setSuffix("%")
        self.settings_volume.setValue(self._settings[0])
        form.addRow("Volume padrão", self.settings_volume)
        self.settings_shuffle = QCheckBox("Ativar reprodução aleatória")
        self.settings_shuffle.setChecked(self._settings[1])
        form.addRow("Reprodução", self.settings_shuffle)
        self.settings_repeat = QComboBox()
        self.settings_repeat.addItem("Desativada", "off")
        self.settings_repeat.addItem("Repetir fila", "all")
        self.settings_repeat.addItem("Repetir música", "one")
        self.settings_repeat.setCurrentIndex(max(0, self.settings_repeat.findData(self._settings[2])))
        form.addRow("Repetição", self.settings_repeat)
        self.settings_preferences = QLineEdit()
        self.settings_preferences.setText(self._settings[3])
        self.settings_preferences.setPlaceholderText("ex.: jazz, ambient, música instrumental")
        form.addRow("Seus gostos", self.settings_preferences)
        layout.addLayout(form)
        save = QPushButton("Salvar preferências")
        save.setObjectName("primaryButton")
        save.clicked.connect(self._save_preferences)
        layout.addWidget(save, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addStretch(1)
        privacy = QLabel("Sem conta e sem perfil remoto. As preferências ajudam a organizar suas recomendações locais.")
        privacy.setObjectName("mutedText")
        privacy.setWordWrap(True)
        layout.addWidget(privacy)
        return page

    def _refresh_page(self) -> None:
        if self.current_page in ("home", "recommendations", "search", "library", "favorites", "history"):
            if self._tracks or self.current_page not in ("home", "recommendations"):
                self._populate_table(self._tracks)
            if self.current_page in ("home", "recommendations"):
                self._populate_cards(self._tracks)
        elif self.current_page == "playlists":
            self._populate_playlists()
            self._populate_table(self._tracks if self._selected_playlist_id else [])

    def show_tracks(self, title: str, tracks: list[object], subtitle: str = "") -> None:
        """Display a supplied collection in the active track-oriented page."""
        self._tracks = list(tracks)
        if self.current_page in self._collection_labels:
            label = self._collection_labels[self.current_page]
            label.setText(title)
            label.setVisible(bool(title) and self.current_page not in ("home", "recommendations"))
        if subtitle:
            self.set_status(subtitle)
        self._populate_table(self._tracks)
        self._populate_cards(self._tracks)

    def _populate_table(self, tracks: list[object]) -> None:
        table = self._page_track_tables.get(self.current_page)
        if table is None:
            return
        table.setRowCount(len(tracks))
        for row, track in enumerate(tracks):
            track_id = str(getattr(track, "id", ""))
            title = str(getattr(track, "title", "Sem título"))
            is_favorite = bool(getattr(track, "favorite", False))
            values = (
                f"♥  {title}" if is_favorite else title,
                str(getattr(track, "artist", "Artista desconhecido")),
                str(getattr(track, "album", "")),
                self._format_time(float(getattr(track, "duration", 0) or 0)),
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setToolTip(value)
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, track_id)
                    if is_favorite:
                        item.setToolTip("Salva nos favoritos")
                table.setItem(row, column, item)

    def _populate_cards(self, tracks: list[object]) -> None:
        if self.current_page not in ("home", "recommendations"):
            return
        layout = self._page_card_layouts.get(self.current_page)
        if layout is None:
            return
        cards_widget = layout.parentWidget()
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        for track in tracks[:6]:
            card = TrackCard(track, self.play_requested.emit, cards_widget)
            card.setFixedWidth(152)
            layout.addWidget(card)
        if not tracks:
            empty = QLabel("Importe músicas para começar sua coleção.")
            empty.setObjectName("mutedText")
            layout.addWidget(empty)
        layout.addStretch(1)

    def show_playlists(self, playlists: list[object]) -> None:
        self.set_playlists(playlists)
        if self.current_page != "playlists":
            self.display_page("playlists")

    def set_playlists(self, playlists: list[object]) -> None:
        """Update playlist data and visible list without changing navigation."""
        self._playlists = list(playlists)
        self._populate_playlists()

    def set_active_playlist(self, playlist_id: str) -> None:
        """Remember the playlist whose tracks are currently displayed."""
        self._selected_playlist_id = str(playlist_id)
        if hasattr(self, "playlist_list"):
            for index in range(self.playlist_list.count()):
                item = self.playlist_list.item(index)
                if str(item.data(Qt.ItemDataRole.UserRole) or "") == self._selected_playlist_id:
                    self.playlist_list.setCurrentItem(item)
                    break

    def _populate_playlists(self) -> None:
        if not hasattr(self, "playlist_list"):
            return
        self.playlist_list.clear()
        for playlist in self._playlists:
            name = str(getattr(playlist, "name", "Playlist"))
            count = int(getattr(playlist, "track_count", 0) or 0)
            item = QListWidgetItem(f"♫   {name}     ·     {count} músicas")
            item.setData(Qt.ItemDataRole.UserRole, str(getattr(playlist, "id", "")))
            self.playlist_list.addItem(item)

    def show_queue(self, tracks: list[object]) -> None:
        self.set_queue(tracks)
        dialog = QDialog(self)
        dialog.setWindowTitle("Fila de reprodução")
        dialog.resize(520, 440)
        layout = QVBoxLayout(dialog)
        label = QLabel("A SEGUIR")
        label.setObjectName("sectionTitle")
        layout.addWidget(label)
        listing = QListWidget()
        for track in self._queue:
            listing.addItem(f"{getattr(track, 'title', 'Sem título')}  ·  {getattr(track, 'artist', '')}")
        layout.addWidget(listing, 1)
        close = QPushButton("Fechar")
        close.clicked.connect(dialog.accept)
        layout.addWidget(close, 0, Qt.AlignmentFlag.AlignRight)
        dialog.exec()

    def set_queue(self, tracks: list[object]) -> None:
        """Refresh the queue state without opening its dialog."""
        self._queue = list(tracks)
        count = len(self._queue)
        self.queue_button.setText("Fila" if count == 0 else f"Fila ({count})")
        self.queue_button.setAccessibleName(f"Abrir fila de reprodução, {count} músicas")

    def set_now_playing(self, track: object | None, playing: bool) -> None:
        if track is None:
            self.now_title.setText("Escolha uma música")
            self.now_artist.setText("Sua biblioteca está pronta")
            self.now_art.set_artwork("")
        else:
            self.now_title.setText(str(getattr(track, "title", "Sem título")))
            self.now_artist.setText(str(getattr(track, "artist", "Artista desconhecido")))
            self.now_art.set_artwork(str(getattr(track, "artwork", "")))
        self.play_button.setText("Ⅱ" if playing else "▶")
        self.play_button.setAccessibleName("Pausar" if playing else "Reproduzir")

    def set_progress(self, position: float, duration: float) -> None:
        self._duration = max(0.0, float(duration))
        safe_position = min(max(0.0, float(position)), self._duration) if self._duration else 0.0
        self.position_label.setText(self._format_time(safe_position))
        self.duration_label.setText(self._format_time(self._duration))
        if not self.progress_slider.isSliderDown():
            was_blocked = self.progress_slider.blockSignals(True)
            self.progress_slider.setValue(round(safe_position / self._duration * 1000) if self._duration else 0)
            self.progress_slider.blockSignals(was_blocked)

    def set_status(self, message: str, error: bool = False) -> None:
        self.status_label.setText(message)
        self.status_label.setProperty("error", bool(error))
        self.status_label.setVisible(bool(message))
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def set_busy(self, busy: bool) -> None:
        self.set_status("Carregando sua música…" if busy else "")
        for control in (self.import_file_button, self.import_folder_button, self.open_source_button):
            control.setEnabled(not busy)

    def set_settings(self, volume: int, shuffle: bool, repeat: str, preferences: str) -> None:
        self._settings = (min(100, max(0, int(volume))), bool(shuffle), repeat, preferences)
        volume_blocked = self.volume_slider.blockSignals(True)
        shuffle_blocked = self.shuffle_button.blockSignals(True)
        self.volume_slider.setValue(min(100, max(0, int(volume))))
        self.shuffle_button.setChecked(bool(shuffle))
        self.volume_slider.blockSignals(volume_blocked)
        self.shuffle_button.blockSignals(shuffle_blocked)
        self._set_repeat(str(repeat))
        if "settings" in self.page_widgets:
            self.settings_volume.setValue(min(100, max(0, int(volume))))
            self.settings_shuffle.setChecked(bool(shuffle))
            repeat_index = self.settings_repeat.findData(repeat)
            self.settings_repeat.setCurrentIndex(max(0, repeat_index))
            self.settings_preferences.setText(preferences)

    def open_source_dialog(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Abrir uma origem")
        dialog.setModal(True)
        layout = QVBoxLayout(dialog)
        title = QLabel("Adicionar música de uma origem")
        title.setObjectName("sectionTitle")
        detail = QLabel(
            "Cole um link público cujo acesso e reprodução você está autorizado a usar. "
            "O Auralume não pede credenciais, cookies ou dados de conta."
        )
        detail.setWordWrap(True)
        self.source_url = QLineEdit()
        self.source_url.setPlaceholderText("https://…")
        self.source_authorized = QCheckBox("Confirmo que tenho autorização para acessar e reproduzir este conteúdo.")
        self.source_authorized.setToolTip("A caixa precisa estar marcada para habilitar a abertura do link.")
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Open)
        open_button = buttons.button(QDialogButtonBox.StandardButton.Open)
        browser_button = buttons.addButton("Abrir no navegador", QDialogButtonBox.ButtonRole.ActionRole)
        browser_button.setObjectName("openSourceBrowserButton")
        browser_button.setAccessibleName("Abrir origem no navegador padrão")
        browser_button.clicked.connect(
            lambda checked=False: self.open_url_in_browser(self.source_url.text())
        )

        def update_source_actions() -> None:
            allowed = self.source_authorized.isChecked() and self._http_url(self.source_url.text()) is not None
            open_button.setEnabled(allowed)
            browser_button.setEnabled(allowed)

        self.source_authorized.toggled.connect(update_source_actions)
        self.source_url.textChanged.connect(update_source_actions)
        update_source_actions()
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(title)
        layout.addWidget(detail)
        layout.addWidget(self.source_url)
        layout.addWidget(self.source_authorized)
        layout.addWidget(buttons)
        if dialog.exec() == QDialog.DialogCode.Accepted and self.source_authorized.isChecked():
            url = self.source_url.text().strip()
            if self._http_url(url):
                self.source_requested.emit(url)

    @staticmethod
    def _http_url(source: str) -> QUrl | None:
        url = QUrl(source.strip())
        if url.scheme().lower() in ("http", "https") and url.isValid() and url.host():
            return url
        return None

    def open_url_in_browser(self, source: str) -> bool:
        """Explicitly open a validated public HTTP(S) URL in the default browser."""
        url = self._http_url(source)
        return QDesktopServices.openUrl(url) if url is not None else False

    def _show_track_menu(self, position) -> None:
        table = self._page_track_tables.get(self.current_page)
        if table is None:
            return
        row = table.rowAt(position.y())
        if row < 0 or row >= len(self._tracks):
            return
        track = self._tracks[row]
        track_id = str(getattr(track, "id", ""))
        menu = QMenu(self)
        menu.addAction("Reproduzir", lambda: self.play_requested.emit(track_id))
        favorite_label = "Remover dos favoritos" if bool(getattr(track, "favorite", False)) else "Adicionar aos favoritos"
        menu.addAction(favorite_label, lambda: self.favorite_requested.emit(track_id))
        menu.addAction("Adicionar à fila", lambda: self.enqueue_requested.emit(track_id))
        if bool(getattr(track, "is_remote", False)):
            menu.addAction("Abrir origem no navegador", lambda: self.open_track_source(track_id))
        if self._selected_playlist_id:
            menu.addAction(
                "Remover desta playlist",
                lambda: self.playlist_remove_requested.emit(self._selected_playlist_id, track_id),
            )
        if self._playlists:
            playlist_menu = menu.addMenu("Adicionar à playlist")
            for playlist in self._playlists:
                playlist_id = str(getattr(playlist, "id", ""))
                playlist_name = str(getattr(playlist, "name", "Playlist"))
                playlist_menu.addAction(
                    playlist_name,
                    lambda playlist_id=playlist_id: self.playlist_add_requested.emit(playlist_id, track_id),
                )
        menu.exec(table.viewport().mapToGlobal(position))

    def open_track_source(self, track_id: str) -> bool:
        """Open a remote track's source in the user's default browser."""
        track = next((item for item in self._tracks if str(getattr(item, "id", "")) == track_id), None)
        if track is None or not bool(getattr(track, "is_remote", False)):
            return False
        return self.open_url_in_browser(str(getattr(track, "source", "")))

    def _play_table_row(self, row: int, column: int) -> None:
        if 0 <= row < len(self._tracks):
            self.play_requested.emit(str(getattr(self._tracks[row], "id", "")))

    def _prompt_create_playlist(self) -> None:
        name, accepted = QInputDialog.getText(self, "Nova playlist", "Nome da playlist")
        if accepted and name.strip():
            self.playlist_create_requested.emit(name.strip())

    def _select_playlist_item(self, item: QListWidgetItem) -> None:
        self._selected_playlist_id = str(item.data(Qt.ItemDataRole.UserRole) or "")
        self.playlist_selected.emit(self._selected_playlist_id)

    def _show_playlist_menu(self, position) -> None:
        item = self.playlist_list.itemAt(position)
        if item is None:
            return
        playlist_id = str(item.data(Qt.ItemDataRole.UserRole) or "")
        menu = QMenu(self)
        menu.addAction("Abrir", lambda: self._select_playlist_item(item))
        menu.addAction("Excluir playlist", lambda: self.playlist_delete_requested.emit(playlist_id))
        menu.exec(self.playlist_list.viewport().mapToGlobal(position))

    def _save_preferences(self) -> None:
        # Controller signal handlers may immediately refresh all controls.
        # Snapshot the whole form before emitting the first synchronous signal.
        volume = self.settings_volume.value()
        shuffle = self.settings_shuffle.isChecked()
        repeat = str(self.settings_repeat.currentData())
        preferences = self.settings_preferences.text().strip()
        self._settings = (volume, shuffle, repeat, preferences)
        self._set_repeat(repeat)
        self.volume_requested.emit(volume)
        self.shuffle_requested.emit(shuffle)
        self.repeat_requested.emit(repeat)
        self.preferences_requested.emit(preferences)
        self.set_status("Preferências salvas")

    def _seek_from_slider(self) -> None:
        if self._duration > 0:
            self.seek_requested.emit(self.progress_slider.value() / 1000 * self._duration)

    def _cycle_repeat(self) -> None:
        values = ("off", "all", "one")
        self._set_repeat(values[(values.index(self._repeat) + 1) % len(values)])
        self.repeat_requested.emit(self._repeat)

    def _set_repeat(self, repeat: str) -> None:
        self._repeat = repeat if repeat in ("off", "all", "one") else "off"
        labels = {"off": "↻", "all": "↻", "one": "↻¹"}
        tooltips = {"off": "Repetição: desativada", "all": "Repetir fila", "one": "Repetir música"}
        self.repeat_button.setText(labels[self._repeat])
        self.repeat_button.setToolTip(tooltips[self._repeat])
        self.repeat_button.setChecked(self._repeat != "off")

    @staticmethod
    def _format_time(seconds: float) -> str:
        total = max(0, int(seconds))
        minutes, remainder = divmod(total, 60)
        return f"{minutes}:{remainder:02d}"

    @staticmethod
    def _stylesheet() -> str:
        return """
        QWidget { background: #14131A; color: #F4F0EA; font-family: 'DejaVu Sans'; font-size: 13px; }
        QCheckBox { background: transparent; }
        #brand, #mutedText, #pageTitle, #eyebrow, #heroTitle, #sectionTitle,
        #cardTitle, #nowTitle, #timeLabel, #collectionTitle { background: transparent; }
        #sidebar { background: #100F15; border-right: 1px solid #292631; }
        #brand { color: #E7B76B; font-size: 20px; font-weight: 800; letter-spacing: 2px; }
        #mutedText, #timeLabel { color: #A7A1B0; }
        #navButton { text-align: left; padding: 11px 12px; border: 0; border-radius: 8px; color: #BDB7C5; background: transparent; }
        #navButton:hover { background: #211E29; color: #FFFFFF; }
        #navButton:checked { background: #30283A; color: #E9BE79; font-weight: 700; }
        QPushButton { background: #25222D; border: 1px solid #393541; border-radius: 8px; padding: 8px 12px; }
        QPushButton:hover { background: #332F3C; border-color: #62566E; }
        QPushButton:pressed { background: #413A4A; }
        #primaryButton, #playButton { background: #DCA756; color: #21170A; border: 0; font-weight: 800; }
        #playButton { border-radius: 20px; min-width: 38px; max-width: 38px; min-height: 38px; max-height: 38px; padding: 0; font-size: 16px; }
        #playerBar { background: #100F15; border-top: 1px solid #302D38; }
        #nowTitle { font-weight: 700; }
        #playerToggle:checked { color: #DFAE62; border-color: #84683B; }
        #pageTitle { color: #F4F0EA; font-size: 26px; font-weight: 750; }
        #searchInput { color: #F4F0EA; background: #1D1A24; border: 1px solid #393541; border-radius: 8px; padding: 9px; }
        #heroPanel { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #34283D, stop:0.55 #292637, stop:1 #423523); border: 1px solid #514453; border-radius: 16px; }
        #eyebrow { color: #E7B76B; font-size: 10px; font-weight: 800; letter-spacing: 1.7px; }
        #heroTitle { font-size: 24px; font-weight: 750; }
        #sectionTitle { font-size: 12px; font-weight: 800; letter-spacing: 1.1px; color: #DAD4E0; }
        #collectionTitle { color: #DAD4E0; font-size: 17px; font-weight: 700; background: transparent; }
        #shortcutCard { min-height: 70px; text-align: left; font-size: 15px; font-weight: 700; background: #201D27; }
        #trackCard { background: #1D1A24; border: 1px solid #2F2B37; border-radius: 12px; }
        #trackCard:hover { background: #282431; border-color: #64556E; }
        #cardTitle { font-weight: 700; }
        #trackTable { background: transparent; alternate-background-color: #191720; border: 0; selection-background-color: #393047; }
        #trackTable::item { padding: 8px; border-bottom: 1px solid #27242E; }
        QHeaderView::section { background: transparent; color: #A7A1B0; border: 0; border-bottom: 1px solid #393541; padding: 9px 8px; font-size: 10px; font-weight: 800; }
        QLineEdit, QSpinBox, QComboBox, QListWidget { background: #1D1A24; border: 1px solid #393541; border-radius: 8px; padding: 9px; selection-background-color: #5B4870; }
        QCheckBox { spacing: 9px; }
        QSlider::groove:horizontal { height: 4px; background: #48434F; border-radius: 2px; }
        QSlider::sub-page:horizontal { background: #DCA756; border-radius: 2px; }
        QSlider::handle:horizontal { width: 12px; margin: -5px 0; background: #F3D49A; border-radius: 6px; }
        #statusLabel { padding: 8px 12px; color: #E8CA90; background: #28241E; border-radius: 7px; }
        #statusLabel[error="true"] { color: #F0A1A1; background: #362024; }
        #coverArt { border: 1px solid #FFFFFF22; }
        QScrollArea { border: 0; background: transparent; }
        QScrollBar:vertical { background: #14131A; width: 8px; margin: 0; border: 0; }
        QScrollBar::handle:vertical { background: #51495C; min-height: 28px; border-radius: 4px; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
        QMenu { background: #211E29; border: 1px solid #494352; }
        QMenu::item:selected { background: #393047; }
        """
