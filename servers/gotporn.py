# -*- coding: utf-8 -*-
from core import httptools
from core import scrapertools
from platformcode import config
from platformcode import logger


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data
    data = httptools.downloadpage(page_url).data
    if "<h2>WE ARE SORRY</h2>" in data or '<title>404 Not Found</title>' in data:
        return False,  config.get_localized_string(70449) % "Mixdrop"
    return True, ""


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    url = scrapertools.find_single_match(data,'<source (?:id="video_source_\d+" |)src="([^"]+)" type=(?:\'|")video/mp4(?:\'|")')
    host = scrapertools.find_single_match(page_url, '(https://.*?.com)')
    url += "|Referer=%s" % host
    logger.debug(url)
    server = scrapertools.find_single_match(page_url, 'https://(?:www.|)([A-z0-9-]+).com')
    video_urls.append(["[%s]" %server, url])
    return video_urls
