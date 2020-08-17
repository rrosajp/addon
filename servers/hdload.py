# -*- coding: utf-8 -*-

import base64

from core import httptools
from platformcode import config, logger


def test_video_exists(page_url):
    logger.log("(page_url='%s')" % page_url)

    data = httptools.downloadpage(page_url, cookies=False).data
    if 'Not found id' in data:
        return False, config.get_localized_string(70449) % "HDLoad"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.log()
    itemlist = []

    logger.log(page_url)
    data = httptools.downloadpage(page_url, post='').data
    logger.log(data)
    url = base64.b64decode(data)

    itemlist.append([".mp4 [HDLoad]", url])

    return itemlist
