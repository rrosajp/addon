from core import httptools
from core import scrapertools, support
from lib import jsunpack
from platformcode import logger, config
import re, ast, requests

def test_video_exists(page_url):
    logger.debug("(page_url='%s')" % page_url)

    page_url = re.sub(r'(.*\/)([^\/]+)$', '\\1cast/\\2', page_url)
    
    data = httptools.downloadpage(page_url).data

    lastIndexStart = data.rfind('<script>')
    lastIndexEnd = data.rfind('</script>')

    script = data[ (lastIndexStart + len('<script>')):lastIndexEnd ]

    char_codes = ast.literal_eval(re.search('\[[^]+]+]',script).group(0))
    hidden_js = "".join([chr(c - int(re.search('parseInt\(value\)\s?-\s?([0-9]+)', script).group(1))) for c in char_codes])
    
    newurl = re.search('\$.get\(\'([^\']+)', hidden_js).group(1)
    global url_video
    url_video = None

    castpage = httptools.downloadpage(newurl, headers={'x-requested-with': 'XMLHttpRequest', 'Referer': page_url }).data

    url_video = re.search( r"cc\.cast\('(http[s]?.*?)'", castpage)
    if url_video:
        url_video = url_video.group(1)
        return True, ""
    
    return False, config.get_localized_string(70449) % "MaxStream"


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.debug("url=" + page_url)

    # page_url = re.sub(r'(.*\/)([^\/]+)$', '\\1/cast/\\2', page_url)

    # data = httptools.downloadpage(page_url).data

    # packed = scrapertools.find_single_match(data, r'(eval.*?)</script>')
    # unpacked = jsunpack.unpack(packed)
    # return support.get_jwplayer_mediaurl(unpacked, 'MaxStream')

    if url_video:
        video_urls = []
        video_urls.append(["[MaxStream]", url_video])
        return video_urls
    else:
        raise "Something wrong: no url found before :("

