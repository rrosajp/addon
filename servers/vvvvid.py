# -*- coding: utf-8 -*-

from core import httptools
from core import scrapertools
from lib import jsunpack, vvvvid_decoder
from platformcode import logger
import requests
import re

# Creating persistent session
current_session = requests.Session()
headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0'}

# Getting conn_id token from vvvvvvvvvvid and creating payload
login_page = 'https://www.vvvvid.it/user/login'
conn_id = current_session.get(login_page, headers=headers).json()['data']['conn_id']
payload = {'conn_id': conn_id}

logger.info('CONNECTION ID= ' + str(payload))


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    data = httptools.downloadpage(page_url).data
    if "Not Found" in data or "File was deleted" in data:
        return False, "[Watchvideo] El fichero no existe o ha sido borrado"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    video_urls = []
    page_url = page_url.replace("/show/","/#!show/")
    # Getting info from given URL
    show_id = re.findall("#!show/([0-9]+)/", page_url)[0]
    name = re.findall(show_id + "/(.+?)/", page_url)[0]
    season_id = re.findall(name + "/(.+?)/", page_url)[0]
    video_id = re.findall(season_id + "/(.+?)/", page_url)[0]


    json_url = "https://www.vvvvid.it/vvvvid/ondemand/" + show_id + '/season/' +season_id + '/'
    logger.info('URL= ' + json_url)
    json_file = current_session.get(json_url, headers=headers, params=payload).json()
    # logger.info(json_file['data'])
    for episode in json_file['data']:
        # import web_pdb; web_pdb.set_trace()
        if episode['video_id'] == int(video_id):
            embed_info = vvvvid_decoder.dec_ei(episode['embed_info'])
            embed_info = embed_info.replace('manifest.f4m','master.m3u8').replace('http://','https://').replace('/z/','/i/')

    # import web_pdb; web_pdb.set_trace()

    video_urls.append(['GUARDA IL VIDEO', str(embed_info)])
    return video_urls