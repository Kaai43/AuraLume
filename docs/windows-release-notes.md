# Windows release draft — NOT PUBLISHED

Suggested version for an isolated Windows port: **v0.1.1**, subject to approval
and successful Windows acceptance/licensing checks. The published v0.1.0 tag
must remain unchanged. Use a new version because the port changes source code;
do not label a new build as an exact v0.1.0-tag artifact.

If the owner later chooses to include the independent desktop-theme work in
the same release, reassess scope/version (for example v0.2.0) separately. That
work is not part of this Windows-only candidate.

Candidate filename produced by the verifier:
`Auralume-0.1.0-candidate-<commit12>-windows-x64.zip`.
The application version is intentionally still 0.1.0 during investigation.
After approving a release version, align pyproject.toml, auralume/__init__.py
and version assertions, then rebuild/retest that exact commit.

Final proposed asset: `Auralume-0.1.1-windows-x64.zip`.
**SHA-256: pending an actual successful Windows build**, generated as a `.sha256`
sidecar by scripts/verify_windows.py. Do not replace this with the native DLL's hash.

## Proposed GitHub text (enable only after verification)

### Auralume 0.1.1 — Windows x64

This release adds a portable Windows distribution of Auralume. It retains the
local music library, search, favorites, playlists, listening history, playback
queue, shuffle and repeat controls. No account is required.

The Windows package includes the Python/Qt runtime and native playback
libraries. Extract the entire ZIP into a writable folder and run `Auralume.exe`.
Keep the `_internal` directory beside the executable. No separate Python or
mpv installation is intended to be necessary; confirm this on a clean machine
before publishing this statement as verified.

User data is stored under `%LOCALAPPDATA%\Auralume`. Existing data from the
earlier development location is preserved in place; `--data-dir` selects an
explicit alternative directory. To collect a diagnostic report, run
`Auralume.exe --diagnostics` from PowerShell. A console window is expected in
this first diagnostic-friendly package.

Target systems: Windows 10/11, x64. The package is unsigned; code signing,
SmartScreen behavior, audible output and device switching require manual
validation. Automated null-output audio checks do not establish audible output.

Auralume is GPL-3.0-or-later. Third-party notices are included under
`_internal/licenses`. Add the reviewed corresponding-source asset and its
checksum before publishing. No personal music is included.

This Windows package does not replace the previously published Linux assets.

## Publication blockers

Native Windows build/test results, the ZIP/checksum, clean Windows validation,
native/Qt source and license review, and explicit owner publication approval
are still pending. Do not turn this draft into a release before resolving them.
