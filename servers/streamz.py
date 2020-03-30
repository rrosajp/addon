# -*- coding: utf-8 -*-
from core import httptools
from core import scrapertools
from lib import jsunpack
from platformcode import logger


def get_video_url(page_url, video_password):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []
    url = httptools.downloadpage(page_url).url
    data = httptools.downloadpage(url).data
    data = scrapertools.find_single_match(data, '<footer id="Footer" class="clearfix">(.*?)</html>')
    packed = scrapertools.find_single_match(data, r'(eval.*?)</script>')
    unpacked = jsunpack.unpack(packed)
    url = scrapertools.find_single_match(unpacked, '(https://streamz.cc/getlink.*?.dll)')
    video_urls.append(["[streamz]", url])
    return video_urls

