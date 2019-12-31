from core import httptools
from core import scrapertools
from platformcode import config


def test_video_exists(page_url):
    stream_url = get_stream_url(page_url)
    data = httptools.downloadpage(stream_url).data
    if "Error Playlist" in data:
        return False, config.get_localized_string(70449) % "HDPlayer"
    return True, ""

def get_stream_url(url):
    id = scrapertools.find_single_match(url, 'id=([a-z0-9]+)')
    return 'https://hdplayer.casa/hls/' + id + '/' + id + '.playlist.m3u8'

def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    return [('.m3u8', get_stream_url(page_url))]
