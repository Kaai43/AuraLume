<div align="center">

<img src="packaging/auralume.svg" alt="Auralume logo" width="88" />

Auralume
Your Music, Your Way.
A home for the music you've made your own.
Download · Explore the app · Build from source
</div>

There's something special about a music collection you've built yourself. The album you always come back to. That one song you never skip. The playlists that somehow tell your story.
Auralume is a free, open-source desktop music player built to give those songs a place to live.
It plays music from your computer, remembers what you love, and helps you rediscover your own library through a personal For You section. All in a dark, carefully arranged interface that stays out of the music's way.
No account to create. No subscription to keep up with. No internet connection required to play your local files.
Just your music, your way.

More than a play button
- Your library, all in one place. Import tracks or entire folders. Auralume reads available metadata and supports album artwork stored alongside your music.
- Find the song you're thinking of. Search by title, artist, album, or genre — even when you forget an accent.
- Keep the good ones close. Save favorites, build playlists, and pick up from your listening history.
- Make listening effortless. Queue tracks, skip, seek, shuffle, repeat, and control the volume.
- Rediscover your own collection. For You uses favorites, listening history, playlists, and metadata to recommend tracks already in your library.
- Keep things personal. Your library, favorites, playlists, preferences, and history are stored locally in SQLite. Auralume doesn't require an account or run its own listening-history server.
Auralume isn't a streaming service in disguise. It starts with the music you already have.
Take a look
Find your next favorite	Make space for every mood
	
Suggestions based on your library.	Playlists that feel like yours.


You'll also find a searchable library, favorites, listening history, and a persistent player bar. These screenshots show the early 0.1.0 interface; there's more to come.
Download Auralume
Version 0.1.1 is available for Linux x86-64 and Windows x64. It's an early release, and wider compatibility work is still underway.
Get the latest release →
Platform	Status	Download
Linux x86-64	Available; initially tested on Ubuntu 26.04.1	AppImage · tar.gz
Windows x64	Available; verified on Windows Server 2022 (bundled runtime)	Auralume-0.1.1-windows-x64.zip


Run the AppImage on Linux
Download the AppImage, open a terminal in the directory where you saved it, and run:
chmod +x Auralume-0.1.0-x86_64.AppImage
./Auralume-0.1.0-x86_64.AppImage
On systems where AppImage launch fails due to missing FUSE support, you can try:
APPIMAGE_EXTRACT_AND_RUN=1 ./Auralume-0.1.0-x86_64.AppImage
Prefer the tar.gz archive? Extract it and run the included Auralume executable, keeping the _internal/ directory beside it. The packaged app doesn't require a separate Python installation.
Compatibility note: The original Linux build was verified on Ubuntu 26.04.1 x86-64, not on every Linux distribution. Depending on your system and package format, you may need native libmpv2 and graphical libraries. Original automated audio tests used null audio output; physical speakers/headphones were not separately validated.

Run on Windows
Download `Auralume-0.1.1-windows-x64.zip`, extract the whole folder, and run `Auralume.exe`. Keep `Auralume.exe` together with the bundled `_internal/` directory, which contains the mpv runtime, the Vulkan loader, and the Qt libraries. No separate Python installation is required. The executable is unsigned, so Windows SmartScreen may show a warning.

Build it yourself
Auralume is made with Python 3.12+, PySide6 / Qt 6, libmpv, SQLite, Mutagen, and yt-dlp for explicitly authorized external sources.
On Ubuntu, install Python with venv support, libmpv2, and the relevant Qt/graphics runtime libraries. Then:
git clone https://github.com/Kaai43/AuraLume.git
cd AuraLume
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m auralume
Run the test suite:
QT_QPA_PLATFORM=offscreen python -m pytest -q
Build the Linux executable:
./scripts/build.sh
The original Ubuntu release passed 58 automated tests. Those tests covered the library, database, UI integration, playback behavior, and authorized local test media, but do not prove compatibility with all devices or platforms.
<details>
<summary><strong>Shortcuts, data location, and diagnostics</strong></summary>

- Double-click a track or click its card to play it.
- Right-click a track to queue it or add it to favorites or a playlist.
- Ctrl+O imports files; Ctrl+F focuses search; Space toggles playback outside text fields.
- On Linux, the default music database is ${XDG_DATA_HOME:-~/.local/share}/Auralume/library.sqlite3. You can choose another location with --data-dir.
From the project directory, with the virtual environment activated:
python -m auralume --diagnostics
python -m auralume --smoke-test
For more technical context, see [development progress](docs/progress.md), [next steps](docs/next-task.md), and [dependencies](docs/dependencies.md).
</details>

What about online music?
Auralume can attempt to stream individual public URLs that you're authorized to access, where supported, using yt-dlp and libmpv. This depends on the source's availability, permissions, and restrictions.
It does not include a remote music catalog, bypass DRM, access private streaming APIs, or promise unrestricted access to commercial music. Local playback stays offline; accessing an external URL necessarily connects to that provider.
What comes next?
There's a lot this little player could grow into. First, the foundations need to be solid.
- [x] Local music library, playback, search, favorites, playlists, history, and personal recommendations
- [x] First public Linux release
- [ ] A tested Windows build with the native libmpv dependencies bundled correctly
- [ ] Wider Linux portability and physical-device audio validation
- [ ] Embedded album artwork, playlist import/export, and desktop media controls
- [ ] More thoughtful details across the interface and discovery experience
Found a bug? Have an idea? Want to help shape what's next? Open an issue — contributions and thoughtful feedback are welcome.
Made to be yours
Auralume is independent, free software released under GPL-3.0-or-later. Third-party dependencies keep their own licenses; see [dependency details](docs/dependencies.md) and packaging/licenses/.
Auralume is not affiliated with Spotify, YouTube, or YouTube Music, and doesn't reuse their proprietary code or assets.
<div align="center">

Good music deserves a good place to live.
Auralume — Your Music, Your Way.
</div>

## Windows x64 — preparação em andamento

O porte possui carregamento privado de DLLs, diagnósticos e um pipeline manual de build/testes. **Ainda não há pacote Windows validado nesta sessão.** Instruções, dependências fixadas e limitações: [docs/windows-build.md](docs/windows-build.md). Nenhuma release é publicada automaticamente; revisão de licenças e aprovação do responsável são necessárias antes de distribuir binários.
