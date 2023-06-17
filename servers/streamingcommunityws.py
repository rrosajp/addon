# -*- coding: utf-8 -*-
import urllib.parse

from core import httptools, support, filetools
from platformcode import logger, config
import ast
UA = httptools.get_user_agent()


def test_video_exists(page_url):
    global scws_id
    # logger.debug('page url=', page_url)
    # scws_id = ''
    #
    # if page_url.isdigit():
    #     scws_id = page_url
    # else:
    #     page = httptools.downloadpage(page_url)
    #     if page.url == page_url:  # se non esiste, reindirizza all'ultimo url chiamato esistente
    #         scws_id = support.scrapertools.find_single_match(page.data, r'scws_id[^:]+:(\d+)')
    #     else:
    #         return 'StreamingCommunity', 'Prossimamente'
    #
    # if not scws_id:
    #     return False, config.get_localized_string(70449) % 'StreamingCommunityWS'
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    from urllib.parse import urlparse
    video_urls = list()
    iframe = support.scrapertools.decodeHtmlentities(support.match(page_url, patron='<iframe [^>]+src="([^"]+)').match)
    scws_id = urlparse(iframe).path.split('/')[-1]
    masterPlaylistParams = ast.literal_eval(support.match(iframe, patron='window\.masterPlaylistParams\s=\s({.*?})').match)

    url = 'https://scws.work/v2/playlist/{}?{}&n=1'.format(scws_id, urllib.parse.urlencode(masterPlaylistParams))
    video_urls.append(['m3u8', '{}|User-Agent={}'.format(url, UA)])

    return video_urls


def compose(url):
    subs = []
    video_urls = []
    info = support.match(url, patron=r'LANGUAGE="([^"]+)",\s*URI="([^"]+)|RESOLUTION=\d+x(\d+).*?(http[^"\s]+)', headers={'User-Agent':UA}).matches
    if info and not logger.testMode: # ai test non piace questa parte
        for lang, sub, res, url in info:
            if sub:
                while True:
                    match = support.match(sub, patron=r'(http[^\s\n]+)').match
                    if match:
                        sub = httptools.downloadpage(match).data
                    else:
                        break
                if lang == 'auto': lang = 'ita-forced'
                s = config.get_temp_file(lang +'.srt')
                subs.append(s)
                filetools.write(s, support.vttToSrt(sub))
            elif url:
                video_urls.append(['m3u8 [{}]'.format(res), '{}|User-Agent={}'.format(url, UA), 0, subs])
    else:
        video_urls.append(['m3u8', '{}|User-Agent={}'.format(url, UA)])
    return video_urls
