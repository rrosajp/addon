# -*- coding: utf-8 -*-

import urllib
import time
from core import httptools
from core import scrapertools
from platformcode import logger, config
from lib import jsunpack

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if "Not Found" in data or "File Does not Exist" in data:
        return False, config.get_localized_string(70449) % "Deltabit"
    return True, ""
    pass

def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("(deltabit page_url='%s')" % page_url)
    video_urls = []
    data = httptools.downloadpage(page_url).data
    data = data.replace('"', "'")

    page_url_post = scrapertools.find_single_match(data, "<Form method='POST' action='([^']+)'>")
    imhuman = ''
    post = urllib.urlencode({k: v for k, v in scrapertools.find_multiple_matches(data, "name='([^']+)' value='([^']*)'")})+ imhuman
    time.sleep(6)
    data = httptools.downloadpage(page_url, post=post).data

    videos_packed = scrapertools.find_single_match(data, r"</div>\s*<script type='text/javascript'>(eval.function.p,a,c,k,e,.*?)\s*</script>")

    video_unpacked = jsunpack.unpack(videos_packed)
    videos_urls = []
    videos = scrapertools.find_single_match(video_unpacked, r'sources:\["([^"]+)"\]')
    video_urls.append(['[DeltaBit]', videos.replace('https:','http:')])

    logger.info("videos_urls #### {}".format(video_urls))
    return video_urls
