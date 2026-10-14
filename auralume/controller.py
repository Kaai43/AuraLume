"""Application coordinator: UI intent -> services -> UI state."""
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, Slot
from PySide6.QtWidgets import QFileDialog

from .library import EXTENSIONS, scan_paths
from .queue import PlayQueue
from .recommendations import recommend
from .sources import SourceService
from .workers import BackgroundTasks


class Controller(QObject):
    def __init__(self, window, database, player, source_service=None):
        super().__init__(window)
        self.window, self.db, self.player = window, database, player
        self.sources = source_service or SourceService()
        self.jobs = BackgroundTasks(self)
        self.queue = PlayQueue()
        self.current_track = None
        self.playing = False
        self._loaded = False
        self._closed = False
        self._expected_url = ''
        self._generation = 0
        self._busy = 0
        self._playlist_id = ''
        self._visible = []
        self._query = ''
        self.page = 'home'
        self.last_error = ''
        self.queue.shuffle = bool(self.db.get_setting('shuffle', False))
        self.queue.repeat = self.db.get_setting('repeat', 'off')
        self.player.set_volume(self.db.get_setting('volume', 70))
        self._connect()
        self._update_settings()
        self.window.set_playlists(self.db.list_playlists())
        self.navigate('home')
        if not self.db.list_tracks():
            self.window.set_status('Importe sua música. Em Configurações, escolha artistas e gêneros para o Para Você.')
        if self.player.initialization_error:
            self._error(self.player.initialization_error)
        self.timer = QTimer(self)
        self.timer.setInterval(250)
        self.timer.timeout.connect(self._tick)
        self.timer.start()

    def _connect(self):
        w = self.window
        w.navigate.connect(self.navigate)
        w.import_files_requested.connect(self._choose_files)
        w.import_folder_requested.connect(self._choose_folder)
        w.search_requested.connect(self.search)
        w.play_requested.connect(self.play)
        w.favorite_requested.connect(self.favorite)
        w.enqueue_requested.connect(self.enqueue)
        w.playlist_create_requested.connect(self.create_playlist)
        w.playlist_selected.connect(self.select_playlist)
        w.playlist_add_requested.connect(self.add_to_playlist)
        w.playlist_remove_requested.connect(self.remove_from_playlist)
        w.playlist_delete_requested.connect(self.delete_playlist)
        w.play_pause_requested.connect(self.toggle_pause)
        w.next_requested.connect(self.next)
        w.previous_requested.connect(self.previous)
        w.seek_requested.connect(self.player.seek)
        w.volume_requested.connect(self.set_volume)
        w.shuffle_requested.connect(self.set_shuffle)
        w.repeat_requested.connect(self.set_repeat)
        w.source_requested.connect(self.open_source)
        w.preferences_requested.connect(self.set_preferences)
        self.player.loaded.connect(self._on_loaded)
        self.player.ended.connect(self._on_ended)
        self.player.error.connect(self._on_playback_error)

    def navigate(self, page):
        self.page = page
        if page != 'playlists':
            self._playlist_id = ''
        self.window.display_page(page)
        self.refresh()

    def refresh(self):
        self.window.set_playlists(self.db.list_playlists())
        if self.page == 'settings':
            self._update_settings()
            return
        if self.page == 'playlists':
            self.window.show_playlists(self.db.list_playlists())
            self.window.set_active_playlist(self._playlist_id)
            self._visible = self.db.playlist_tracks(self._playlist_id) if self._playlist_id else []
            title = next((p.name for p in self.db.list_playlists() if p.id == self._playlist_id), 'Selecione uma playlist')
        elif self.page == 'favorites':
            self._visible, title = self.db.list_tracks(favorites=True), 'Suas favoritas'
        elif self.page == 'history':
            self._visible, title = self.db.history(), 'Continue ouvindo'
        elif self.page == 'recommendations':
            self._visible, title = recommend(self.db), 'Recomendadas para hoje'
        elif self.page == 'home':
            self._visible = self.db.history(12) or recommend(self.db, 12)
            title = 'Sua coleção, à sua maneira'
        elif self.page == 'search':
            self._visible, title = self.db.list_tracks(query=self._query), f'Resultados para “{self._query}”' if self._query else 'Pesquisar na biblioteca'
        else:
            self._visible, title = self.db.list_tracks(), 'Todas as músicas'
        self.window.show_tracks(f'{title} · {len(self._visible)}', self._visible)

    def _choose_files(self):
        pattern = ' '.join('*' + ext for ext in sorted(EXTENSIONS))
        paths, _ = QFileDialog.getOpenFileNames(self.window, 'Importar músicas', str(Path.home()), f'Áudio ({pattern});;Todos os arquivos (*)')
        if paths:
            self.import_paths(paths)

    def _choose_folder(self):
        path = QFileDialog.getExistingDirectory(self.window, 'Importar pasta de música', str(Path.home()))
        if path:
            self.import_paths([path])

    def _submit(self, operation, on_success, generation=None):
        self._busy += 1
        self.window.set_busy(True)

        def finished(result=None, error=None):
            self._busy = max(0, self._busy - 1)
            self.window.set_busy(self._busy > 0)
            if generation is not None and generation != self._generation:
                return
            if error:
                self._error(str(error))
            else:
                try:
                    on_success(result)
                except Exception as caught:
                    self._error(str(caught))

        self.jobs.submit(operation, lambda result: finished(result), lambda error: finished(error=error))

    def import_paths(self, paths, autoplay=False):
        def imported(result):
            self.db.upsert_tracks(result.tracks)
            self.navigate('library')
            message = f'{len(result.tracks)} músicas importadas.'
            if result.errors:
                message += f' {len(result.errors)} arquivos ignorados. {result.errors[0]}'
            self.window.set_status(message, error=bool(result.errors))
            if autoplay and result.tracks:
                self.queue.set([track.id for track in result.tracks])
                self._play_current()
        self._submit(lambda: scan_paths(paths), imported)

    def search(self, query):
        self._query = query.strip()
        self.db.record_search(self._query)
        self.navigate('search')

    def favorite(self, track_id):
        self.db.toggle_favorite(track_id)
        self.refresh()

    def create_playlist(self, name):
        try:
            playlist = self.db.create_playlist(name)
            self.select_playlist(playlist.id)
            self.window.set_status('Playlist criada. Use o menu de uma música para adicioná-la.')
        except ValueError as error:
            self._error(str(error))

    def select_playlist(self, playlist_id):
        self._playlist_id = playlist_id
        self.navigate('playlists')

    def add_to_playlist(self, playlist_id, track_id):
        self.db.add_to_playlist(playlist_id, track_id)
        self.refresh()
        self.window.set_status('Música adicionada à playlist.')

    def remove_from_playlist(self, playlist_id, track_id):
        self.db.remove_from_playlist(playlist_id, track_id)
        self.refresh()

    def delete_playlist(self, playlist_id):
        self.db.delete_playlist(playlist_id)
        if self._playlist_id == playlist_id:
            self._playlist_id = ''
        self.refresh()

    def _update_settings(self):
        self.window.set_settings(self.player.volume, self.queue.shuffle, self.queue.repeat,
                                 ', '.join(self.db.get_setting('preferences', [])))

    def set_volume(self, volume):
        self.player.set_volume(volume)
        self.db.set_setting('volume', min(100, max(0, int(volume))))
        self._update_settings()

    def set_shuffle(self, shuffle):
        self.queue.shuffle = bool(shuffle)
        self.db.set_setting('shuffle', self.queue.shuffle)
        self._update_settings()

    def set_repeat(self, repeat):
        self.queue.repeat = repeat if repeat in ('off', 'one', 'all') else 'off'
        self.db.set_setting('repeat', self.queue.repeat)
        self._update_settings()

    def set_preferences(self, terms):
        values = list(dict.fromkeys(t.strip() for t in terms.split(',') if t.strip()))[:30]
        self.db.set_setting('preferences', values)
        self._update_settings()
        self.window.set_status('Preferências salvas neste dispositivo.')

    def enqueue(self, track_id):
        if self.db.get_track(track_id):
            self.queue.enqueue(track_id)
            self._update_queue()
            self.window.set_status('Adicionada à fila.')

    def _update_queue(self):
        self.window.set_queue([track for key in self.queue.items if (track := self.db.get_track(key))])

    def play(self, track_id):
        ids = [track.id for track in self._visible]
        if track_id not in ids:
            ids = [track_id]
        self.queue.set(ids, track_id)
        self._play_current()

    def _play_current(self):
        track = self.db.get_track(self.queue.current) if self.queue.current else None
        if track is None:
            return
        self._generation += 1
        generation = self._generation
        self.player.stop()
        self.current_track = track
        self._loaded, self.playing = False, False
        self._expected_url = ''
        self.window.set_now_playing(track, False)
        self.window.set_progress(0, track.duration)
        self._update_queue()
        if track.is_remote:
            self._submit(lambda: self.sources.resolve(track.source, authorized=True),
                         self._load_resolved, generation=generation)
        else:
            self._load(track.source)

    def _load(self, url, headers=None):
        self._expected_url = url
        self.last_error = ''
        try:
            self.player.load(url, headers)
            self.window.set_status('Carregando áudio…')
        except Exception as error:
            self._on_playback_error(str(error))

    def _load_resolved(self, resolved):
        self.db.upsert_track(resolved.track)
        self.current_track = self.db.get_track(resolved.track.id)
        self._load(resolved.url, resolved.headers)

    def open_source(self, url):
        self._generation += 1
        generation = self._generation

        def resolved(result):
            self.db.upsert_track(result.track)
            self.queue.set([result.track.id])
            self.player.stop()
            self._loaded, self.playing = False, False
            self.current_track = self.db.get_track(result.track.id)
            self._update_queue()
            self.refresh()
            self._load(result.url, result.headers)
        self._submit(lambda: self.sources.resolve(url, authorized=True), resolved, generation=generation)

    @Slot(str)
    def _on_loaded(self, url):
        if self._closed or url != self._expected_url or self._loaded or not self.current_track:
            return
        self._loaded, self.playing = True, True
        self.db.record_play(self.current_track.id)
        self.window.set_now_playing(self.current_track, True)
        self.window.set_status('')

    @Slot(str)
    def _on_ended(self, url):
        if not self._closed and url == self._expected_url:
            self.playing, self._loaded = False, False
            self.next(automatic=True)

    @Slot(str)
    def _on_playback_error(self, message):
        self.playing, self._loaded = False, False
        self.window.set_now_playing(self.current_track, False)
        self._error(message)

    def next(self, automatic=False):
        if self.queue.next(automatic=automatic):
            self._play_current()
        elif automatic:
            self.playing = False
            self.window.set_now_playing(self.current_track, False)
            self.window.set_status('Fim da fila.')

    def previous(self):
        if self.player.position > 3:
            self.player.seek(0)
        elif self.queue.previous():
            self._play_current()

    def toggle_pause(self):
        if self._loaded:
            self.player.toggle_pause()
            self.playing = not self.player.paused
            self.window.set_now_playing(self.current_track, self.playing)
        elif self.queue.current:
            self._play_current()
        elif self._visible:
            self.play(self._visible[0].id)

    def _tick(self):
        if self._loaded:
            self.window.set_progress(self.player.position, self.player.duration)

    def _error(self, message):
        self.last_error = message
        self.window.set_status(message, error=True)

    def close(self):
        if not self._closed:
            self._closed = True
            self.timer.stop()
            self.jobs.close()
            self.player.close()
