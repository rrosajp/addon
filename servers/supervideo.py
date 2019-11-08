# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertoolsV2
from lib import jsunpack
from platformcode import config, logger
import ast


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)

    data = httptools.downloadpage(page_url, cookies=False).data
    if 'File Not Found' in data:
        return False, config.get_localized_string(70449) % "SuperVideo"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    data = httptools.downloadpage(page_url).data
    code_data = scrapertoolsV2.find_single_match(data, "<script type='text/javascript'>(eval.*)")
    if code_data:
        code = jsunpack.unpack(code_data)
        match = scrapertoolsV2.find_single_match(code, r'sources:(\[[^]]+\])')
        lSrc = ast.literal_eval(match)

        lQuality = ['360p', '720p', '1080p', '4k'][:len(lSrc)-1]
        lQuality.reverse()

        for n, source in enumerate(lSrc):
            quality = 'auto' if n==0 else lQuality[n-1]
            video_urls.append(['.' + source.split('.')[-1] + '(' + quality + ') [SuperVideo]', source])
    else:
        matches = scrapertoolsV2.find_multiple_matches(data, r'src:\s*"([^"]+)",\s*type:\s*"[^"]+"\s*, res:\s(\d+)')
        for url, quality in matches:
            video_urls.append(['mp4 [' + quality + ']', url])
    return video_urls
