# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertools
from platformcode import logger, config


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data
    data = httptools.downloadpage(page_url).data
    if "Video not found" in data:
        return False, config.get_localized_string(70449) % "Streamtape"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    global data

    url = scrapertools.find_single_match(data, 'id="videolink"[^>]+>\n?\s*//(.*?)<')
    if url:
        media_url = 'https://' + url + '&stream=1'
        video_urls.append([".mp4 [Streamtape]", media_url])

    return video_urls
