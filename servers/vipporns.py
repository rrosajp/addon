# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector vipporns By Alfa development Group
# --------------------------------------------------------
from lib.kt_player import decode

from core import httptools
from core import scrapertools
from platformcode import config
from platformcode import logger


def test_video_exists(page_url):

    response = httptools.downloadpage(page_url)

    if not response.sucess or \
       "Not Found" in response.data \
       or "File was deleted" in response.data \
       or "is no longer available" in response.data:
        return False,  config.get_localized_string(70449) % "vipporns"

    global video_url, license_code
    video_url = scrapertools.find_single_match(response.data, "video_url: '([^']+)'")
    license_code = scrapertools.find_single_match(response.data, "license_code: '([^']+)'")

    return True, ""

def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info()
    return [["[vipporns]", decode(video_url, license_code)]]