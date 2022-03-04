# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per 133x
# ------------------------------------------------------------

from core import httptools, support, jsontools
from platformcode import logger
import requests

# host = support.config.get_channel_url()
host = 'https://www.1337x.to'
# headers = {
# 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
# 'accept-encoding': 'gzip, deflate, br',
# 'accept-language': 'it,en;q=0.9,it-IT;q=0.8,en-GB;q=0.7,en-US;q=0.6',
# 'cache-control': 'no-cache',
# 'pragma': 'no-cache',
# 'referer': 'https://www.1337x.to/',
# 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36 Edg/98.0.1108.62'}

# def getData(item):
#     support.dbg()
#     json = jsontools.load(base64.b64decode(support.match(item, patron=r'window.park\s*=\s*"([^"]+)').match))
#     data = support.match(json['page_url'], headers=json['page_headers']).data
#     return data

@support.menu
def mainlist(item):
    
    film = ['/movie-lib-sort/all/it/release/desc/all/1/']
    
    tvshow = ['/popular-movies',
              ('Popolari', ['/popular-movies', 'popular'])]

    # menu = [
    #     ('BDRiP {film}', ['/categoria.php?active=0&category=1&order=data&by=DESC&page=', 'peliculas', [0, 'movie', True], 'undefined']),
    #     ('Cerca BDRiP... {submenu} {film}', ['/torrent-ita/1/', 'search', ['search', 'movie', True], 'movie']),
    #     ('DVD {film}', ['/categoria.php?active=0&category=20&order=data&by=DESC&page=', 'peliculas', [0, 'movie', True], 'undefined']),
    #     ('Cerca DVD... {submenu} {film}', ['/torrent-ita/20/', 'search', ['search', 'movie', True], 'movie']),
    #     ('Screener {film}', ['/categoria.php?active=0&category=19&order=data&by=DESC&page=', 'peliculas', [0, 'movie', True], 'undefined']),
    #     ('Cerca Screener.. {submenu} {film}', ['/torrent-ita/19/', 'search', ['search', 'movie', True], 'movie']),
    #     ('Serie TV', ['/categoria.php?active=0&category=15&order=data&by=DES&page=', 'peliculas', [0 , 'tvshow', True], 'tvshow']),
    #     ('Cerca Serie TV.. {submenu}', ['/torrent-ita/15/', 'search', ['search', 'tvshow',True], 'tvshow']),
    #     ('Anime', ['/categoria.php?active=0&category=5&order=data&by=DESC&page=', 'peliculas', [0, 'anime', True], 'tvshow']),
    #     ('Cerca Anime.. {submenu}', ['/torrent-ita/5/', 'search', ['search', 'anime', True], 'tvshow']),
    #     ('Musica', ['/categoria.php?active=0&category=2&order=data&by=DESC&page=', 'peliculas', [0, 'music', False], 'music']),
    #     ('Cerca Musica.. {submenu}', ['/torrent-ita/2/', 'search', ['search', 'music', False], 'music']),
    #     ('Audiolibri {musica}', ['/categoria.php?active=0&category=18&order=data&by=DESC&page=', 'peliculas', [0, 'music', False], 'music']),
    #     ('Cerca Audiolibri.. {submenu}', ['/torrent-ita/18/', 'search', ['search', 'music', False], 'music']),
    #     # mostrerebbe anche risultati non "multimediali" e allungherebbero inutilmente la ricerca globale
    #     # ('Altro {film}', ['/categoria.php?active=0&category=4&order=data&by=DESC&page=', 'peliculas', [0, 'other', False]]),
    #     # ('Cerca altro.. {submenu}', ['/torrent-ita/4/', 'search', ['search', 'other', False]]),
    #     # ('Cerca Tutto... {color kod bold}', ['/argh.php?search=', 'search', ['search', 'all', False]])
    # ]

    return locals()


@support.scrape
def peliculas(item):
    patron = r'<img alt="[^"]*" data-original="(?P<thumb>[^"]+)(?:[^>]+>){15}(?P<title>[^<]+)(?:[^>]+>){18,23}\s*<a href="(?P<url>[^"]+)'
    patronNext = r'"([^"]+)">&gt;&gt;'
    return locals()


def search(item, text):
    support.info(item, text)
    if 'all' in item.args:
        item.url += text
    else:
        item.url += text + '.html'
    try:
        return peliculas(item)
    # Cattura la eccezione così non interrompe la ricerca globle se il canale si rompe!
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("search except: %s" % line)
        return []


def findvideos(item):
    from lib.guessit import guessit
    itemlist = []
    items = support.match(item.url, patron=r'<a href="([^"]+)">([^<]+)<(?:[^>]+>){3}([^<]+)<(?:[^>]+>){6}([^<]+)<span').matches

    for url, title, seed, size in items:
        title = guessit(title).get('title', '')
        itemlist.append(item.clone(title = f'{title} [Seed={seed}] [{size}]', url=host + url, server='torrent', action='play'))

    Videolibrary = True if 'movie' in item.args else False
    return support.server(item, itemlist=itemlist, Videolibrary=Videolibrary)


def play(item):
    from core import servertools
    data = support.match(item.url, patron=r'href="(magnet[^"]+)').match
    return servertools.find_video_items(item, data=data)