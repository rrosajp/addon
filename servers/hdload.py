# -*- coding: utf-8 -*-

from core import httptools, scrapertoolsV2
from platformcode import config, logger
import base64


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)

    data = httptools.downloadpage(page_url, cookies=False).data
    if 'Not found id' in data:
        return False, config.get_localized_string(70449) % "hdload"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info()
    itemlist = []

    logger.info(page_url)
    data = httptools.downloadpage(page_url, post='').data
    logger.info(data)
    url = base64.b64decode(data)

    itemlist.append([".mp4 [hdload]", url])

    return itemlist
