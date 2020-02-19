# -*- coding: utf-8 -*-
# by DrZ3r0

import urllib

from core import httptools
from core import scrapertools
from platformcode import logger, config
from core.support import dbg


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data
    # dbg()
    page = httptools.downloadpage(page_url)
    logger.info(page.data)
    if 'embed_ak.php' in page_url:
        code = scrapertools.find_single_match(page.url, '/embed-([0-9a-z]+)\.html')
        if not code:
            code = scrapertools.find_single_match(page.data, r"""input\D*id=(?:'|")[^'"]+(?:'|").*?value='([a-z0-9]+)""")
        if code :
            page = httptools.downloadpage('http://akvideo.stream/video/' + code)
        else:
            return False, config.get_localized_string(70449) % "Akvideo"
    data = page.data

    # ID, code = scrapertools.find_single_match(data, r"""input\D*id=(?:'|")([^'"]+)(?:'|").*?value='([a-z0-9]+)""")
    # post = urllib.urlencode({ID: code})
    logger.info('PAGE DATA' + data)
    if "File Not Found" in data:
        return False, config.get_localized_string(70449) % "Akvideo"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info(" url=" + page_url)
    video_urls = []

    global data
    vres = scrapertools.find_multiple_matches(data, 'nowrap[^>]+>([^,]+)')
    data_pack = scrapertools.find_single_match(data, "</div>\n\s*<script[^>]+>(eval.function.p,a,c,k,e,.*?)\s*</script>")
    if data_pack != "":
        from lib import jsunpack
        data = jsunpack.unpack(data_pack)

    # URL
    # logger.info(data)
    matches = scrapertools.find_multiple_matches(data, '(http.*?\.mp4)')
    # logger.info(str(matches))
    _headers = urllib.urlencode(httptools.default_headers)

    i = 0
    for media_url in matches:
        # URL del vídeo
        video_urls.append([vres[i] + " mp4 [Akvideo] ", media_url.replace('https://', 'http://') + '|' + _headers])
        i = i + 1

    for video_url in video_urls:
        logger.info(" %s - %s" % (video_url[0], video_url[1]))
    return sorted(video_urls, key=lambda x: x[0].split('x')[1])
