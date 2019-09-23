# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per vvvvid
# ----------------------------------------------------------
import requests, re
from core import  support, tmdb
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
host += '/vvvvid/ondemand'
list_servers = ['vvvvid']
list_quality = ['default']

@support.menu
def mainlist(item):
    anime = ['/anime/channels/',
             ('In Evidenza',['/anime/channel/10005/last/', 'peliculas', 'sort']),
             ('Popolari',['/anime/channel/10003/last/', 'peliculas', 'sort']),
             ('Nuove Uscite',['/anime/channel/10007/last/', 'peliculas', 'sort']),
             ('Generi',['/anime/channels/', 'peliculas', '/anime/channel/10004/last/?category=']),
             ('A-Z',['/anime/channels/', 'peliculas', '/anime/channel/10003/last/?filter=']),
             ('Extra',['/anime/channels/', 'peliculas', '/anime/channel/10010/last/?extras='])
             ]
    return locals()

def peliculas(item):
    itemlist = []
    blacklist = ['Generi','A - Z', 'Extra']
    json_file = current_session.get(item.url, headers=headers, params=payload).json()
    support.log(json_file)
    if 'data' in json_file:
        if not item.args:
            names = [i['filter'] for i in json_file['data'] if 'filter' in i][0]
            for name in names:
                support.log(name)
                url =  item.url + '10003/last/?filter=' + str(name)
                json_file = current_session.get(url, headers=headers, params=payload).json()
                if 'data' in json_file:
                    json_file = current_session.get(url, headers=headers, params=payload).json()
                    for key in json_file['data']:
                        support.log(key['thumbnail'])
                        itemlist.append(
                            Item(
                                channel = item.channel,
                                title = key['title'],
                                fulltitle= key['title'],
                                show= key['title'],
                                url=  host + '/' + str(key['show_id']) + '/seasons/',
                                action= 'episodios'
                        ))
        elif item.args == 'sort':
            for key in json_file['data']:
                for key in json_file['data']:
                    itemlist.append(
                        Item(
                            channel = item.channel,
                            title = key['title'],
                            fulltitle= key['title'],
                            show= key['title'],
                            url=  host + '/' + str(key['show_id']) + '/seasons/',
                            action= 'episodios',
                            thumbnail= key['thumbnail']
                        ))
        elif 'last' in item.args:
            Filter = support.match(item.args,r'\?([^=]+)=')[0][0]
            keys = [i[Filter] for i in json_file['data'] if Filter in i][0]
            for key in keys:
                itemlist.append(
                    Item(channel = item.channel,
                        title = key if Filter == 'filter' else key['name'],
                        url =  host + item.args + (key if Filter == 'filter' else str(key['id'])),
                        action = 'peliculas',
                        args = 'sort'))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist

def episodios(item):
    itemlist = []
    json_file = current_session.get(item.url, headers=headers, params=payload).json()
    show_id = str(json_file['data'][0]['show_id'])

    for key in json_file['data'][0]['episodes']:
        support.log(key)
        support.log('KEY= ',key)
        itemlist.append(
            Item(
                channel = item.channel,
                title = 'Episodio ' + str(key['number']) + ' - ' + key['title'],
                fulltitle= item.fulltitle,
                show= item.show,
                url=  host + '/' + show_id + '/season/' + str(key['season_id']) + '/',
                action= 'findvideos',
                video_id= key['video_id']
            ))
    return itemlist

def findvideos(item):
    from lib import vvvvid_decoder
    itemlist = []
    json_file = current_session.get(item.url, headers=headers, params=payload).json()
    support.log(json_file['data'])
    for episode in json_file['data']:
        if episode['video_id'] == item.video_id:
            url = vvvvid_decoder.dec_ei(episode['embed_info'])
            item.url = url.replace('manifest.f4m','master.m3u8').replace('http://','https://').replace('/z/','/i/')
            if 'https' not in item.url: item.url = url='https://or01.top-ix.org/videomg/_definst_/mp4:' + item.url + '/playlist.m3u'
    return support.server(item)
