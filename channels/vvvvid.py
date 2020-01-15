# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per vvvvid
# ----------------------------------------------------------
import requests, re
from core import  support, tmdb
from core.item import Item
from specials import autorenumber
from lib.concurrent import futures


host = support.config.get_channel_url()

# Creating persistent session
current_session = requests.Session()
headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0'}

# Getting conn_id token from vvvvid and creating payload
login_page = host + '/user/login'
try:
    conn_id = current_session.get(login_page, headers=headers).json()['data']['conn_id']
    payload = {'conn_id': conn_id}
except:
    conn_id = ''


main_host = host
host += '/vvvvid/ondemand/'
list_servers = ['vvvvid']
list_quality = ['default']

@support.menu
def mainlist(item):
    if conn_id:
        anime = ['anime/',
                ('In Evidenza',['anime/', 'peliculas', 'channel/10005/last/']),
                ('Popolari',['anime/', 'peliculas', 'channel/10002/last/']),
                ('Nuove Uscite',['anime/', 'peliculas', 'channel/10007/last/']),
                ('Generi',['anime/', 'peliculas', 'channel/10004/last/?category=']),
                ('A-Z',['anime/', 'peliculas', 'channel/10003/last/?filter='])
                ]
        film =  ['film/',
                ('In Evidenza',['film/', 'peliculas', 'channel/10005/last/']),
                ('Popolari',['film/', 'peliculas', 'channel/10002/last/']),
                ('Nuove Uscite',['film/', 'peliculas', 'channel/10007/last/']),
                ('Generi',['film/', 'peliculas', 'channel/10004/last/?category=']),
                ('A-Z',['film/', 'peliculas', 'channel/10003/last/?filter=']),
                ]
        tvshow = ['series/',
                ('In Evidenza',['series/', 'peliculas', 'channel/10005/last/']),
                ('Popolari',['series/', 'peliculas', 'channel/10002/last/']),
                ('Nuove Uscite',['series/', 'peliculas', 'channel/10007/last/']),
                ('Generi',['series/', 'peliculas', 'channel/10004/last/?category=']),
                ('A-Z',['series/', 'peliculas', 'channel/10003/last/?filter='])
                ]
        show = [('Show bold {tv}',['show/', 'peliculas', 'channel/10005/last/', 'tvshow']),
                ('In Evidenza submenu {tv}',['show/', 'peliculas', 'channel/10005/last/', 'tvshow']),
                ('Popolari submenu {tv}',['show/', 'peliculas', 'channel/10002/last/', 'tvshow']),
                ('Nuove Uscite submenu {tv}',['show/', 'peliculas', 'channel/10007/last/', 'tvshow']),
                ('Generi submenu {tv}',['show/', 'peliculas', 'channel/10004/last/?category=', 'tvshow']),
                ('A-Z submenu {tv}',['show/', 'peliculas', 'channel/10003/last/?filter=', 'tvshow']),
                ('Cerca Show... bold submenu {tv}', ['show/', 'search', '', 'tvshow'])
                ]
        kids = [('Kids bold',['kids/', 'peliculas', 'channel/10005/last/', 'tvshow']),
                ('In Evidenza submenu {kids}',['kids/', 'peliculas', 'channel/10005/last/', 'tvshow']),
                ('Popolari submenu {kids}',['kids/', 'peliculas', 'channel/10002/last/', 'tvshow']),
                ('Nuove Uscite submenu {kids}',['kids/', 'peliculas', 'channel/10007/last/', 'tvshow']),
                ('Generi submenu {kids}',['kids/', 'peliculas', 'channel/10004/last/?category=', 'tvshow']),
                ('A-Z submenu {kids}',['kids/', 'peliculas', 'channel/10003/last/?filter=', 'tvshow']),
                ('Cerca Kids... bold submenu {kids}', ['kids/', 'search', '', 'tvshow'])
                ]
    else:
        Top = [("Visibile solo dall'Italia bold",[])]
    return locals()

def search(item, text):
    support.log(text)
    itemlist = []
    if conn_id:
        if 'film' in item.url: item.contentType = 'movie'
        else: item.contentType = 'tvshow'
        item.search = text
        try:
            itemlist = peliculas(item)
        except:
            import sys
            for line in sys.exc_info():
                support.logger.error("%s" % line)
            return []
    return itemlist

def newest(categoria):
    item = Item()
    item.args = 'channel/10007/last/'
    if categoria == 'peliculas':
        item.contentType = 'movie'
        item.url = host + 'film/'
    if categoria == 'series':
        item.contentType = 'tvshow'
        item.url = host + 'series/'
    if categoria == 'anime':
        item.contentType = 'tvshow'
        item.url = host + 'anime/'
    return peliculas(item)


def dl_pages(name,item):
    itemlist = []
    url =  item.url + 'channel/10003/last/?filter=' + str(name)
    json_file = current_session.get(url, headers=headers, params=payload).json()
    if 'data' in json_file:
        json_file = current_session.get(url, headers=headers, params=payload).json()
        make_itemlist(itemlist, item, json_file)
    return itemlist

def peliculas(item):
    itemlist = []
    if not item.args:
        json_file = current_session.get(item.url + 'channels', headers=headers, params=payload).json()
        names = [i['filter'] for i in json_file['data'] if 'filter' in i][0]
        with futures.ThreadPoolExecutor() as executor:
            json_file = [executor.submit(dl_pages, name, item,) for name in names]
            for res in futures.as_completed(json_file):
                if res.result():
                    itemlist += res.result()
        itemlist = sorted(itemlist, key=lambda it: it.fulltitle)

    elif ('=' not in item.args) and ('=' not in item.url):
        json_file = current_session.get(item.url + item.args, headers=headers, params=payload).json()
        make_itemlist(itemlist, item, json_file)

    elif '=' in item.args:
        json_file = current_session.get(item.url + 'channels', headers=headers, params=payload).json()
        Filter = support.match(item.args, patron=r'\?([^=]+)=').match
        keys = [i[Filter] for i in json_file['data'] if Filter in i][0]
        for key in keys:
            if key not in ['1','2']:
                itemlist.append(
                    Item(channel = item.channel,
                        title = support.typo(key.upper() if Filter == 'filter' else key['name'], 'bold'),
                        url =  item.url + item.args + (key if Filter == 'filter' else str(key['id'])),
                        action = 'peliculas',
                        args = 'filters',
                        contentType = item.contentType))

    else :
        json_file = current_session.get(item.url, headers=headers, params=payload).json()
        make_itemlist(itemlist, item, json_file)
    if item.contentType != 'movie': autorenumber.renumber(itemlist)
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist

def episodios(item):
    itemlist = []
    json_file = current_session.get(item.url, headers=headers, params=payload).json()
    show_id = str(json_file['data'][0]['show_id'])
    season_id = str(json_file['data'][0]['season_id'])
    episodes = []
    support.log('SEASON ID= ',season_id)
    for episode in json_file['data']:
        episodes.append(episode['episodes'])
    for episode in episodes:
        for key in episode:
            if 'stagione' in key['title'].encode('utf8').lower():
                match = support.match(key['title'].encode('utf8'), patron=r'[Ss]tagione\s*(\d+) - [Ee]pisodio\s*(\d+)').match
                title = match[0]+'x'+match[1] + ' - ' + item.fulltitle
                make_item = True
            elif int(key['season_id']) == int(season_id):
                try:
                    title = 'Episodio ' + key['number'] + ' - ' + key['title'].encode('utf8')
                except:
                    title = 'Episodio ' + key['number'] + ' - ' + key['title']
                make_item = True
            else:
                make_item = False
            if make_item == True:
                if type(title) == tuple: title = title[0]
                itemlist.append(
                    Item(
                        channel = item.channel,
                        title = title,
                        fulltitle= item.fulltitle,
                        show= item.show,
                        url=  host + show_id + '/season/' + str(key['season_id']) + '/',
                        action= 'findvideos',
                        video_id= key['video_id'],
                        contentType = item.contentType
                    ))
    autorenumber.renumber(itemlist, item, 'bold')
    if autorenumber.check(item) == True:
        support.videolibrary(itemlist,item)
    return itemlist

def findvideos(item):
    from lib import vvvvid_decoder
    itemlist = []
    if item.contentType == 'movie':
        json_file = current_session.get(item.url, headers=headers, params=payload).json()
        item.url = host + str(json_file['data'][0]['show_id']) + '/season/' + str(json_file['data'][0]['episodes'][0]['season_id']) + '/'
        item.video_id = json_file['data'][0]['episodes'][0]['video_id']

    json_file = current_session.get(item.url, headers=headers, params=payload).json()
    for episode in json_file['data']:
        if episode['video_id'] == item.video_id:
            url = vvvvid_decoder.dec_ei(episode['embed_info'] or episode['embed_info'])
            if 'youtube' in url: item.url = url
            item.url = url.replace('manifest.f4m','master.m3u8').replace('http://','https://').replace('/z/','/i/')
            if 'https' not in item.url:
                url = support.match('https://or01.top-ix.org/videomg/_definst_/mp4:' + item.url + '/playlist.m3u')
                url = url.split()[-1]
                itemlist.append(
                    Item(action= 'play',
                         title='direct',
                         url= 'https://or01.top-ix.org/videomg/_definst_/mp4:' + item.url + '/' + url,
                         server= 'directo')
                )
    return support.server(item, itemlist=itemlist, down_load=False)

def make_itemlist(itemlist, item, data):
    search = item.search if item.search else ''
    infoLabels = {}
    for key in data['data']:
        if search.lower() in key['title'].encode('utf8').lower():
            infoLabels['year'] = key['date_published']
            infoLabels['title'] = infoLabels['tvshowtitle'] = key['title']
            title = key['title'].encode('utf8')
            itemlist.append(
                Item(
                    channel = item.channel,
                    title = support.typo(title, 'bold'),
                    fulltitle= title,
                    show= title,
                    url= host + str(key['show_id']) + '/seasons/',
                    action= 'findvideos' if item.contentType == 'movie' else 'episodios',
                    contentType = item.contentType,
                    contentSerieName= key['title'] if item.contentType != 'movie' else '',
                    contentTitle= title if item.contentType == 'movie' else '',
                    infoLabels=infoLabels
            ))
    return itemlist