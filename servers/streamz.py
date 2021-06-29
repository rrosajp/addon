# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector Streamz
# --------------------------------------------------------

import re
from core import httptools
from platformcode import logger, config


def test_video_exists(page_url):
    global data
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url)

    if "<b>File not found, sorry!</b" in data.data:
        return False, config.get_localized_string(70449) % "streamZ"
    return True, ""


def get_video_url(page_url, video_password=""):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    # real_video = scrapertools.find_single_match(data.data, r"var player = [^\(]+\('(video_\d)")
    # packed_data = scrapertools.find_single_match(data.data, r'(eval\(function\(p,a,c,k,e,d\).*?{}[^<]+)'.format(real_video))
    # if packed_data:
    #     url = scrapertools.find_single_match(jsunpack.unpack(packed_data), r"src:\\'([^'\\]+)")
    #     url += "|User-Agent=%s" % httptools.get_user_agent()
    #     video_urls.append([".mp4 [streamZ]", url])
    # else:
    url = re.sub(r'(\.\w{2,3})/\w', '\\1/getl1nk-', data.url) + '.dll'
    url += "|User-Agent=%s" % httptools.get_user_agent()
    video_urls.append([".mp4 [streamZ]", url])

    return video_urls