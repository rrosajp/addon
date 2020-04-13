# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per HD4ME
# ------------------------------------------------------------

from core import scrapertools, httptools, support
from core.item import Item
from platformcode import config, logger

#impostati dinamicamente da findhost()


# host = config.get_channel_url(findhost)
host = 'https://hd4me.net'
headers = [['Referer', host]]

list_servers = ['mixdrop','vidoza','cloudvideo','vup','supervideo','gounlimited']
list_quality = ['default']

@support.menu
def mainlist(item):

    film = [('Genere', ['', 'genre'])]

    return locals()

@support.scrape
def peliculas(item):
    # debug = True
    patron = r'<a href="(?P<url>[^"]+)" rel="[^"]+" title="(?P<title>[^\(]+)(?!\()\s*\((?P<year>\d+)\)\s\D+(?P<quality>\d+p) ... (?P<lang>[^ ]+).*?<img id="cov" src="(?P<thumb>[^"]+)"'
    patronNext = r'rel="next" href="([^"]+)"'
    return locals()

@support.scrape
def genre(item):
    action = 'peliculas'
    blacklist =['prova ']
    patronMenu = r'<a href="(?P<url>[^"]+)" class="menu-link\s*sub-menu-link">(?P<title>[^<]+)<'
    return locals()


def search(item, text):
    support.log(text)
    item.url = host + '/?s=' + text
    try:
        return peliculas(item)
    # Cattura la eccezione così non interrompe la ricerca globle se il canale si rompe!
    except:
        import sys
        for line in sys.exc_info():
            logger.error("search except: %s" % line)
        return []


def findvideos(item):
    url = support.match(item, patron=r'<a class="bot1" href="([^"]+)"').match
    url = support.httptools.downloadpage(url, followredirect=True).url
    return support.server(item, url)
