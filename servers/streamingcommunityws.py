# -*- coding: utf-8 -*-
from core import httptools, support
from platformcode import logger, config


def test_video_exists(page_url):
    global scws_id
    logger.debug('page url=', page_url)
    # support.dbg()

    scws_id = support.match(page_url, patron=r'scws_id[^:]+:(\d+)').match

    if not scws_id:
        return False, config.get_localized_string(70449) % 'StreamingCommunityWS'
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    from time import time
    from base64 import b64encode
    from hashlib import md5

    global scws_id
    video_urls = list()

    # clientIp = httptools.downloadpage(f'https://scws.work/videos/{scws_id}').json.get('client_ip')
    clientIp = httptools.downloadpage('http://ip-api.com/json/').json.get('query')
    if clientIp:
        expires = int(time() + 172800)
        token = b64encode(md5(f'{expires}{clientIp} Yc8U6r8KjAKAepEA'.encode('utf-8')).digest()).decode('utf-8').replace('=', '').replace('+', '-').replace('/', '_')
        url = f'https://scws.work/master/{scws_id}?token={token}&expires={expires}&n=1'
        video_urls.append(['hls', url])

    return video_urls
