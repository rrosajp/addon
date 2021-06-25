from core import httptools
from core import scrapertools, support
from lib import jsunpack
from platformcode import logger, config
import re, ast, requests, sys

if sys.version_info[0] >= 3:
    import urllib.parse as urlparse
else:
    import urlparse

def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)

    global data
    data = httptools.downloadpage(page_url).data

    if "file was deleted" in data:
        return False, config.get_localized_string(70449) % "MaxStream"

    return True, ""



def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)
    video_urls = []
    url_video = ''

    lastIndexStart = data.rfind('<script>')
    lastIndexEnd = data.rfind('</script>')

    script = data[ (lastIndexStart + len('<script>')):lastIndexEnd ]

    match = scrapertools.find_single_match(script, r'(\[[^\]]+\])[^\{]*\{[^\(]+\(parseInt\(value\)\s?-\s?([0-9]+)')
    if match:
        char_codes = ast.literal_eval(match[0])
        hidden_js = "".join([chr(c - int(match[1])) for c in char_codes])

        newurl = scrapertools.find_single_match(hidden_js, r'\$.get\(\'([^\']+)')
        castpage = httptools.downloadpage(newurl, headers={'x-requested-with': 'XMLHttpRequest', 'Referer': page_url }).data
        url_video = scrapertools.find_single_match(castpage, r"cc\.cast\('(http[s]?.[^']+)'")
    else:
        logger.debug('Something wrong: no url found before that :(')

    if url_video:
        parse = urlparse.urlparse(url_video)
        video_urls.append(['mp4 [MaxStream]', url_video])
        try:
            video_urls.append(['m3u8 [MaxStream]', '{}://{}/hls/{}/master.m3u8'.format(parse.scheme, parse.netloc, parse.path.split('/')[1]) ])
        except:
            logger.debug('Something wrong: Impossible get HLS stream')
    return video_urls




