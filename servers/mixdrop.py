# -*- coding: utf-8 -*-
import re
from core import httptools
from core import scrapertoolsV2
from platformcode import config, logger
from lib import jsunpack


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)

    data = httptools.downloadpage(page_url, cookies=False).data
    if 'WE ARE SORRY' in data:
        return False, config.get_localized_string(70449) % "MixDrop"

    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info()
    itemlist = []

    # streaming url
    data = httptools.downloadpage(page_url).data
    data = re.sub(r'\n|\t|\r', ' ', data)
    data = re.sub(r'>\s\s*<', '><', data)
    jsCode = scrapertoolsV2.find_single_match(data, r'<script>\s*MDCore\.ref = "[a-z0-9]+"; (.*?) </script>')
    jsUnpacked = jsunpack.unpack(jsCode)
    url = "https://" + scrapertoolsV2.find_single_match(jsUnpacked, r'vsr[^=]*="(?:/)?(/[^"]+)')

    itemlist.append([".mp4 [MixDrop]", url])

    # download url
    # import urllib
    # try:
    #     import json
    # except:
    #     import simplejson as json
    # page_url = page_url.replace('/e/', '/f/') + '?download'
    # data = httptools.downloadpage(page_url).data
    # csrf = scrapertoolsV2.find_single_match(data, '<meta name="csrf" content="([^"]+)">')
    # postData = {'csrf': csrf, 'a': 'genticket'}
    # resp = httptools.downloadpage(page_url, post=urllib.urlencode(postData)).data
    # resp = json.loads(resp)
    # if resp['type'] == 'ok':
    #     itemlist.append([".mp4 [MixDrop]", 'https:' + resp['url']])

    return itemlist
