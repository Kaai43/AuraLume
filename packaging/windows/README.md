# Windows native dependency review

This directory is a build-input record, not a declaration that redistribution
requirements have been fulfilled. Public binary distribution is **blocked**
until the following audit is completed.

* Auralume remains GPL-3.0-or-later; see the project's LICENSE.
* libmpv: community build shinchiro 20261015, baseline AMD64, not x86-64-v3.
  The pinned archive and DLL hashes are in native-lock.json. The archive has
  no license files. mpv-Copyright.txt is copied from the exact mpv revision.
* The pinned FFmpeg recipe enables GPL and version3. It includes static
  codecs/libraries (including x264/x265, LAME, Opus, Vorbis, OpenSSL, libass,
  rubberband, libplacebo and others). An import-table scan cannot identify
  every statically linked component or fulfill its license obligations.
  Recipe: https://github.com/shinchiro/mpv-winbuild-cmake/blob/1f8d2e76255abc48f0456d9be99b4cab9c6566e6/packages/ffmpeg.cmake
* Before distribution: recover the exact source revisions, license/notice
  texts and corresponding build materials for ALL included native components;
  prepare a compliant corresponding-source delivery alongside the binary.
  Merely linking mpv's repository or copying the GPL text is insufficient.
* Vulkan Loader 1.4.328 is built from pinned Khronos sources in the runner.
  Its root LICENSE is Apache-2.0; Headers have their own LICENSES directory.
  The staging script copies both sets of notices. It uses the static MSVC
  runtime configuration from upstream; final PE imports are audited.
* PySide6/Qt/shiboken: use their applicable GPL/LGPL distribution terms;
  package actual wheel notices and review third-party code of the DLLs/plugins
  collected in the Windows bundle. The Ubuntu Qt inventory is not proof of
  Windows compliance. The onedir layout permits replacing shared libraries.
* Python, python-mpv, Mutagen, yt-dlp and their backends keep their own licenses.
  Installed distribution versions and notices are recorded during staging.
* The separate FFmpeg EXE only generates synthetic acceptance-test media;
  it is NOT included in Auralume's ZIP. libmpv still incorporates FFmpeg code.

Windows system DLLs/API sets are not copied out of the runner. Windows 10/11
x64 support, including the exact minimum OS build, must still be validated.
No GPU driver, Python installation or mpv installation should be required for
audio, but this claim requires successful native and clean-machine tests.
