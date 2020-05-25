# -*- coding: utf-8 -*-

from core import httptools, scrapertools, filetools
from platformcode import logger, config

baseUrl = 'https://hdmario.live'

def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    global data

    page = httptools.downloadpage(page_url)
    logger.info(page.url)
    if 'unconfirmed' in page.url:
        from lib import onesecmail
        id = page_url.split('/')[-1]
        mail = onesecmail.getRandom()
        postData = {
            'email': mail,
            'hls_video_id': id
        }
        httptools.downloadpage(page.url, post=postData)
        jsonMail = onesecmail.waitForMail(mail)
        logger.info(jsonMail)
        code = jsonMail['subject'].split(' - ')[0]
        page = httptools.downloadpage(page_url + '?code=' + code)
    data = page.data
    if "the page you are looking for could not be found" in data:
        return False, config.get_localized_string(70449) % "HDmario"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    global data
    logger.info(data)
    # p,a,c,k,e,d data -> xhr.setRequestHeader
    global secureProof, server
    secureProof = scrapertools.find_single_match(data, '\|(\w{22})\|')
    logger.info('X-Secure-Proof=' + secureProof)

    data = httptools.downloadpage(baseUrl + '/pl/' + page_url.split('/')[-1].replace('?', '') + '.m3u8', headers=[['X-Secure-Proof', secureProof]]).data
    filetools.write('special://temp/hdmario.m3u8', data, 'w')

    video_urls = [['.m3u8 [HDmario]', 'special://temp/hdmario.m3u8']]

    return video_urls
