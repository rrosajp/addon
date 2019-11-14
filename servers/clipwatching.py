# -*- coding: utf-8 -*-

import re
from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger, config


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if "File Not Found" in data or "File was deleted" in data:
        return False, config.get_localized_string(70292) % "ClipWatching"
    return True, ""


def get_video_url(page_url, user="", password="", video_password=""):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    data = re.sub('\t|\n','',data)
    logger.info('CLIP DATA= ' + data)
    packed = scrapertools.find_single_match(data, r"text/javascript'>(.*?)\s*</script>")
    try: unpacked = jsunpack.unpack(packed)
    except: unpacked = data
    video_urls = []
    videos = scrapertools.find_multiple_matches(unpacked, r'(?:file|src):\s*"([^"]+).*?type:\s*"video/([^"]+)".*?label:\s*"([^"]+)')
    for video, Type, label in videos:
        logger.info(Type)
        logger.info(label)
        if ".jpg" not in video:
            video_urls.append(['%s [%sp] [ClipWatching]' % (Type, label), video])
    return video_urls
