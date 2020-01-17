# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Filmi Gratis
# ------------------------------------------------------------
"""
    La voce "Al cinema" si riferisce ai titoli che scorrono nella home page

    Problemi:
        - Nessuno noto

    Novità, il canale, è presente in:
       - FILM
"""
import re

from core import servertools, httptools, support
from core.item import Item
from platformcode import config

host = config.get_channel_url()

list_servers = ['verystream', 'openload', 'streamango', 'vidoza', 'okru']
list_quality = ['1080p', '720p', '480p', '360']

headers = [['Referer', host]]


@support.menu
def mainlist(item):
    film = [
        ('Generi', ['', 'menu', 'Film']),
        ('Più Visti', ['','peliculas', 'most'])
    ]

    tvshow = ['',
        ('Generi', ['', 'menu', 'Serie Tv']),
        ('Ultimi Episodi', ['','peliculas', 'last'])
    ]

    search = ''
    return locals()


@support.scrape
def menu(item):
    action = 'peliculas'
    patronBlock = item.args + r' Categorie</a>\s*<ul(?P<block>.*?)</ul>'
    patronMenu = r'<a href="(?P<url>[^"]+)"[^>]+>(?P<title>[^>]+)<'
    return locals()


def search(item, text):
    support.log('search', item)

    text = text.replace(' ', '+')
    item.url = host + '/search/keyword/' + text
    try:
        item.args = 'search'
        return peliculas(item)
    # Se captura la excepcion, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            support.log('search log:', line)
        return []


def newest(categoria):
    support.log(categoria)
    itemlist = []
    item = support.Item()
    item.url = host
    item.action = 'peliculas'
    try:
        if categoria == 'peliculas':
            item.contentType = 'movie'
            itemlist = peliculas(item)
        else:
            item.args = 'last'
            item.contentType = 'tvshow'
            itemlist = peliculas(item)

            if itemlist[-1].action == 'peliculas':
                itemlist.pop()
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.log({0}.format(line))
        return []

    return itemlist


@support.scrape
def peliculas(item):
    # debug = True
    if item.contentType == 'tvshow' and not item.args:
        action = 'episodios'
        patron = r'<div class="movie-box">\s*<a href="(?P<url>[^"]+)">[^>]+>[^>]+>\D+Streaming\s(?P<lang>[^"]+)[^>]+>[^>]+>[^>]+>(?P<quality>[^<]+)[^>]+>[^>]+>[^>]+>\s*<img src="(?P<thumb>[^"]+)"[^>]+>[^>]+>[^>]+>[^>]+>(?P<rating>[^<]+)<[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<title>[^<]+)[^>]+>[^>]+>[^>]+>\s*(?P<year>\d+)'
    elif item.contentType == 'movie' and not item.args:
        patron = r'<div class="existing_item col-6 col-lg-3 col-sm-4 col-xl-4">\s*<div class="movie-box">\s*<a href="(?P<url>(?:http(?:s)://[^/]+)?/(?P<type>[^/]+)/[^"]+)">[^>]+>[^>]+>\D+Streaming\s*(?P<lang>[^"]+)">[^>]+>[^>]+>(?P<quality>[^<]+)<[^>]+>[^>]+>[^>]+>\s*<img src="(?P<thumb>[^"]+)"[^>]+>[^>]+>[^>]+>[^>]+>(?P<rating>[^<]+)<[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<title>[^<]+)[^>]+>[^>]+>[^>]+>\s*(?:(?P<year>\d+))?[^>]+>[^>]+>[^>]+>[^>]+>(?P<plot>[^<]*)<'
    elif item.args == 'last':
        patron = r'<div class="episode-box">[^>]+>[^>]+>[^>]+>\D+Streaming\s(?P<lang>[^"]+)">[^>]+>[^>]+>(?P<quality>[^<]+)<[^>]+>[^>]+>[^>]+>[^^>]+>[^>]+>\s*<img src="(?P<thumb>[^"]+)"[^[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>\s*<a href="(?P<url>[^"]+)"[^>]+>[^>]+>(?P<title>[^<]+)<[^>]+>[^>]+>[^>]+>\D*(?P<season>\d+)[^>]+>\D*(?P<episode>\d+)'
    elif item.args == 'most':
        patron =r'div class="sm-113 item">\s*<a href="(?P<url>[^"]+)">[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>\s<img src="(?P<thumb>[^"]+)"[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>\s*(?P<title>[^<]+)'
    else:
        patron = r'<div class="movie-box">\s*<a href="(?P<url>(?:http(?:s)://[^/]+)?/(?P<type>[^/]+)/[^"]+)">[^>]+>[^>]+>\D+Streaming\s*(?P<lang>[^"]+)">[^>]+>[^>]+>(?P<quality>[^<]+)<[^>]+>[^>]+>[^>]+>\s*<img src="(?P<thumb>[^"]+)"[^>]+>[^>]+>[^>]+>[^>]+>(?P<rating>[^<]+)<[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<title>[^<]+)[^>]+>[^>]+>[^>]+>\s*(?:(?P<year>\d+))?[^>]+>[^>]+>[^>]+>[^>]+>(?P<plot>[^<]*)<'
        typeActionDict = {'findvideos':['movie'], 'episodios':['tvshow']}
        typeContentDict = {'movie':['movie'], 'tvshow':['tvshow']}
    patronNext = r'<a href="([^"]+)"[^>]+>&raquo;'
    return locals()


@support.scrape
def episodios(item):
    patron = r'<div class="episode-box">[^>]+>[^>]+>[^>]+>\D+Streaming\s(?P<lang>[^"]+)">[^>]+>[^>]+>(?P<quality>[^<]+)<[^>]+>[^>]+>[^>]+>\s*<img src="(?P<thumb>[^"]+)"[^[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>\s*<a href="(?P<url>[^"]+)"[^>]+>[^>]+>(?P<title>[^<]+)<[^>]+>[^>]+>[^>]+>\D*(?P<season>\d+)[^>]+>\D*(?P<episode>\d+)'
    return locals()


def findvideos(item):
    support.log()
    # match = support.match(item, patron)
    return support.server(item)
