# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per vvvvid
# ----------------------------------------------------------
import requests, re
from core import  support, jsontools
from core.item import Item

__channel__ = "vvvvid"
host = support.config.get_channel_url(__channel__)

# Creating persistent session
current_session = requests.Session()
headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0'}

# Getting conn_id token from vvvvid and creating payload
login_page = host + '/user/login'
conn_id = current_session.get(login_page, headers=headers).json()['data']['conn_id']
payload = {'conn_id': conn_id}

main_host = host
host += '/vvvvid/ondemand/'
list_servers = ['vvvvid']
list_quality = ['default']

@support.menu
def mainlist(item):
    anime = ['/anime/channels']
    return locals()

def peliculas(item):
    itemlist = []
    
    json_file = current_session.get(item.url, headers=headers, params=payload).json()
    support.log(json_file['data'])
    if 'channels' in item.url:
        for key in json_file['data']:
            itemlist.append(
                Item(
                    channel = item.channel,
                    title = key['name'],
                    url =  host + 'anime/channel/' + str(key['id']) + '/last/',
                    action = 'peliculas'
                )
            )
    else:
        for key in json_file['data']:
            itemlist.append(
                Item(
                    channel = item.channel,
                    title = key['title'],
                    fulltitle= key['title'],
                    show= key['title'],
                    url=  host + str(key['show_id']) + '/seasons/',
                    action= 'episodios',
                    thumbnail= key['thumbnail']
                )
            )

    return itemlist

def episodios(item):
    itemlist = []
    json_file = current_session.get(item.url, headers=headers, params=payload).json()
    show_id = str(json_file['data'][0]['show_id'])
    
    for key in json_file['data'][0]['episodes']:
        support.log('KEY= ',key)
        itemlist.append(
            Item(
                channel = item.channel,
                title = 'Episodio ' + str(key['number']) + ' - ' + key['title'],
                fulltitle= item.fulltitle,
                show= item.show,
                url=  host + show_id + '/season/' + str(key['season_id']) + '/',
                action= 'findvideos',
                video_id= key['video_id']
            ))
    return itemlist

def findvideos(item):
    from lib import vvvvid_decoder
    json_file = current_session.get(item.url, headers=headers, params=payload).json()
    support.log(json_file['data'])
    for episode in json_file['data']:
        if episode['video_id'] == item.video_id:
            url = vvvvid_decoder.dec_ei(episode['embed_info'])
            item.url = url.replace('manifest.f4m','master.m3u8').replace('http://','https://').replace('/z/','/i/')
    return support.server(item)
