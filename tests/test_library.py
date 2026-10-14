import wave

from auralume.library import scan_paths


def make_wave(path, seconds=1):
    with wave.open(str(path), 'wb') as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8000)
        audio.writeframes(b'\x00\x00' * (8000 * seconds))
    return path


def test_scan_reads_duration_and_deduplicates_paths(tmp_path):
    path = make_wave(tmp_path / 'Lume - Aurora.wav')
    result = scan_paths([tmp_path, path])
    assert len(result.tracks) == 1
    track = result.tracks[0]
    assert track.title == 'Aurora'
    assert track.artist == 'Lume'
    assert track.duration == 1.0
    assert track.source == str(path)
    assert scan_paths([path]).tracks[0].id == track.id
    assert not result.errors


def test_scan_reports_corrupt_and_missing_files_without_losing_good_track(tmp_path):
    valid = make_wave(tmp_path / 'ok.wav')
    bad = tmp_path / 'broken.mp3'
    bad.write_bytes(b'not audio')
    result = scan_paths([bad, valid, tmp_path / 'missing.wav'])
    assert [t.title for t in result.tracks] == ['ok']
    assert len(result.errors) == 2
