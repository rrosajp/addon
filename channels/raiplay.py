# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per SerieHD
# ------------------------------------------------------------

import requests
from core import support
from lib.concurrent import futures
current_session = requests.Session()
host = support.config.get_channel_url()
menuURL = 'http://www.rai.it/dl/RaiPlay/2016/menu/PublishingBlock-20b274b1-23ae-414f-b3bf-4bdc13b86af2.html?homejson'
channels = 'http://www.rai.it/dl/RaiPlay/2016/PublishingBlock-9a2ff311-fcf0-4539-8f8f-c4fee2a71d58.html?json'


@support.menu
def mainlist(item):
    film =   ['/film/index.json',
             ('Genere', ['/film/index.json', 'menu', 'genre']),
             ('A-Z', ['/film/index.json', 'menu', 'az'])
             ]
    tvshow = ['/serietv/index.json',
             ('Genere', ['/serietv/index.json', 'menu', 'genre']),
             ('A-Z', ['/serietv/index.json', 'menu', 'az'])
             ]
    fiction = [('Fiction {bullet bold}', ['/fiction/index.json', 'peliculas']),
             ('Genere {submenu}', ['/fiction/index.json', 'menu', 'genre']),
             ('A-Z {submenu}', ['/fiction/index.json', 'menu', 'az']),
             ('Cerca Fiction... {submenu bold}', ['/fiction/index.json', 'search'])
             ]

    top = [('Dirette TV {bold}', ['', 'dirette']),
            #  ('Genere {submenu}', ['/fiction/index.json', 'menu', 'genre']),
            #  ('A-Z {submenu}', ['/fiction/index.json', 'menu', 'az']),
            #  ('Cerca Fiction... {submenu bold}', ['/fiction/index.json', 'search'])
             ]
    return locals()


def menu(item):
    itemlist = []
    json = current_session.get(item.url).json()['contents'][-1]['contents']
    if item.args == 'az':
        json_url = getUrl(json[-1]['path_id'])
        json = current_session.get(json_url).json()['contents']
        for key in json:
            itemlist.append(
                support.Item(
                    channel = item.channel,
                    title = support.typo(key,'bold'),
                    fulltitle = key,
                    show = key,
                    url = json[key],
                    thumbnail = item.thumbnail,
                    action = 'peliculas',
                    args = item.args
                ))
    else:
        for key in json:
            support.log('KEY',key)
            itemlist.append(
                support.Item(
                    channel = item.channel,
                    title = support.typo(key['name'],'bold'),
                    fulltitle = key['name'],
                    show = key['name'],
                    thumbnail = getUrl(key['image']),
                    action = 'peliculas',
                    args = item.args
                ))
    support.thumb(itemlist)
    return itemlist


def search(item, text):
    support.log()
    if 'film' in item.url: item.contentType ='movie'
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


def peliculas(item):
    support.log()
    itemlist = []
    keys = []
    key_list = []

    # pagination options
    pag = item.page if item.page else 1
    pagination = 40

    # load json
    if item.args == 'az':
        json = item.url
        for key in json:
            if item.search.lower() in key['name'].lower():
                keys.append(key)
    else:
        json = current_session.get(item.url).json()

        # load json for main menu item
        if not item.args:
            json_url = getUrl(json['contents'][-1]['contents'][-1]['path_id'])
            json = current_session.get(json_url).json()['contents']
        for key in json:
            if len(json[key]) > 0:
                for key in json[key]:
                    if item.search.lower() in key['name'].lower():
                        keys.append(key)


    for i, key in enumerate(keys):
        if pagination and (pag - 1) * pagination > i: continue  # pagination
        if pagination and i >= pag * pagination: break 
        key_list.append(key)

    if 'film' in item.url: item.contentType ='movie'
    else: item.contentType = 'tvshow'
    with futures.ThreadPoolExecutor() as executor:
        itlist = [executor.submit(addinfo, key, item) for key in key_list]
        for res in futures.as_completed(itlist):
            if res.result():
                itemlist.append(res.result())
    itemlist = sorted(itemlist, key=lambda it: it.title)


    if len(keys) > pag * pagination and not item.search:
        itemlist.append(
            support.Item(channel=item.channel,
                    action = item.action,
                    contentType=item.contentType,
                    title=support.typo(support.config.get_localized_string(30992), 'color kod bold'),
                    fulltitle= item.fulltitle,
                    show= item.show,
                    url=item.url,
                    args=item.args,
                    page=pag + 1,
                    thumbnail=support.thumb()))
    return itemlist


def select(item):
    itemlist = []
    json = current_session.get(item.url).json()['blocks']
    for key in json:
        itemlist.append(
            support.Item(
                channel = item.channel,
                title = support.typo(key['name'],'bold'),
                fulltitle = key['name'],
                show = key['name'],
                thumbnail = item.thumbnail,
                url = key['sets'],
                action = 'episodios',
                args = item.args
            ))
    return itemlist


def episodios(item):
    itemlist = []
    with futures.ThreadPoolExecutor() as executor:
        itlist = [executor.submit(load_episodes, key, item) for key in item.url]
        for res in futures.as_completed(itlist):
            if res.result():
                itemlist += res.result()
    itemlist = sorted(itemlist, key=lambda it: it.title)
    return itemlist


def findvideos(item):
    itemlist = []
    if item.contentType == 'episode':
        url = item.url
    else:
        url = getUrl(current_session.get(item.url).json()['first_item_path'])
        url = current_session.get(url).json()['video']['content_url']
    itemlist.append(
        support.Item(
            channel = item.channel,
            server = 'directo',
            title = 'Diretto',
            fulltitle = item.fulltitle,
            show = item.show,
            thumbnail = item.thumbnail,
            fanart = item.json,
            url = url,
            action = 'play'
        ))
    return support.server(item, itemlist=itemlist)


def getUrl(pathId):
    url = pathId.replace(" ", "%20")
    if url.startswith("/raiplay/"):
        url = url.replace("/raiplay/","https://raiplay.it/")

    if url.startswith("//"):
        url = "https:" + url
    elif url.startswith("/"):
        url = host[:-1] + url

    # fix old format of url for json
    if url.endswith(".html?json"):
        url = url.replace(".html?json", ".json")
    elif url.endswith("/?json"):
        url = url.replace("/?json","/index.json")
    elif url.endswith("?json"):
        url = url.replace("?json",".json")

    return url


def addinfo(key, item):
    info = current_session.get(getUrl(key['info_url'])).json()
    it = support.Item(
            channel = item.channel,
            title = support.typo(key['name'],'bold'),
            fulltitle = key['name'],
            show = key['name'],
            thumbnail = getUrl(key['images']['portrait_logo']),
            fanart = getUrl(key['images']['landscape']),
            url = getUrl(key['path_id']),
            plot = info['description'],
            action = 'findvideos' if item.contentType == 'movies' else 'select')
    return it


def load_episodes(key, item):
    itemlist=[]
    json = current_session.get(getUrl(key['path_id'])).json()['items']
    for key in json:
        # support.log(key)
        ep = support.match(key['subtitle'].encode('utf8'), patron=r'St\s*(\d+)\s*Ep\s*(\d+)').match
        title = ep[0] + 'x' + ep[1].zfill(2) + support.re.sub(r'St\s*\d+\s*Ep\s*\d+','',key['subtitle'].encode('utf8'))
        itemlist.append(
            support.Item(
                channel = item.channel,
                title = support.typo(title, 'bold'),
                fulltitle = item.fulltitle,
                show = item.show,
                thumbnail = item.thumbnail,
                fanart = getUrl(key['images']['landscape']),
                url = key['video_url'],
                plot = key['description'],
                contentType = 'episode',
                action = 'findvideos'
                ))
    return itemlist


def dirette(item):
    itemlist = []
    json = current_session.get(channels).json()['dirette']
    for key in json:
        itemlist.append(
            support.Item(
                channel = item.channel,
                title = support.typo(key['channel'], 'bold'),
                fulltitle = key['channel'],
                show = key['channel'],
                thumbnail = key['transparent-icon'].replace("[RESOLUTION]", "256x-"),
                fanart = key['stillFrame'],
                url = key['video']['contentUrl'],
                plot = key['description'],
                action = 'play'
                ))
    return itemlist