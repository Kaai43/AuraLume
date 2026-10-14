import pytest

from auralume.sources import SourceError, SourceService, parse_info


def info(**changes):
    result = {'id': '123', 'title': 'Aurora', 'uploader': 'Lume', 'duration': 62,
              'webpage_url': 'https://example.com/music', 'url': 'https://example.com/audio.opus',
              'acodec': 'opus', 'vcodec': 'none', 'http_headers': {'User-Agent': 'test'}}
    result.update(changes)
    return result


def test_metadata_keeps_origin_and_separates_temporary_stream():
    source = parse_info(info(), 'https://example.com/music')
    assert source.track.source == 'https://example.com/music'
    assert source.track.title == 'Aurora'
    assert source.track.artist == 'Lume'
    assert source.track.duration == 62
    assert source.track.is_remote
    assert source.url == 'https://example.com/audio.opus'
    assert source.headers == {'User-Agent': 'test'}


@pytest.mark.parametrize('changes', [
    {'has_drm': True}, {'availability': 'needs_auth'}, {'url': None},
    {'title': None}, {'_type': 'playlist', 'entries': []}, {'url': 'file:///etc/passwd'},
])
def test_unavailable_or_incomplete_sources_are_rejected(changes):
    with pytest.raises(SourceError):
        parse_info(info(**changes), 'https://example.com/music')


@pytest.mark.parametrize('url', ['file:///a.mp3', 'ftp://example.com/a', 'not a url', 'https://user:password@example.com/a'])
def test_invalid_urls_rejected_before_network(url):
    with pytest.raises(SourceError):
        SourceService().resolve(url, authorized=True)


def test_authorization_required():
    with pytest.raises(SourceError):
        SourceService().resolve('https://example.com/music', authorized=False)


def test_network_failure_becomes_actionable_source_error():
    class Offline:
        def __init__(self, options):
            self.options = options

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def extract_info(self, url, download):
            assert download is False
            raise TimeoutError('Network timed out')

    with pytest.raises(SourceError, match='origem'):
        SourceService(ydl_factory=Offline).resolve('https://example.com/music', authorized=True)
