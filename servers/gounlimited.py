# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector GoUnlimited By Alfa development Group
# --------------------------------------------------------

import re

from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger, config


def test_video_exists(page_url):
    data = httptools.downloadpage(page_url).data
    if data == "File was deleted":
        return False, config.get_localized_string(70449) % "Go Unlimited"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    data = httptools.downloadpage(page_url, use_requests=True, verify=False).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    logger.info('GOUN DATA= '+data)
    packed_data = scrapertools.find_single_match(data, "javascript'>(eval.*?)</script>")
    unpacked = jsunpack.unpack(packed_data)
    patron = r"sources..([^\]]+)"
    matches = re.compile(patron, re.DOTALL).findall(unpacked)
    for url in matches:
        url += "|Referer=%s" %page_url
        video_urls.append(['mp4 [Go Unlimited]', url])
    return video_urls
