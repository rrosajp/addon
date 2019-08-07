# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per seriehd
# ------------------------------------------------------------
import urlparse
import re

from channelselector import thumb
from lib import cloudscraper
from core import scrapertoolsV2, servertools, httptools, support
from core.item import Item
from core.support import menu, log
from platformcode import logger, config
from specials import autoplay


__channel__ = "seriehd"
host = config.get_channel_url(__channel__)

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['verystream', 'openload', 'streamango', 'thevideome']
list_quality = ['1080p', '720p', '480p', '360']

checklinks = config.get_setting('checklinks', 'seriehd')
checklinks_number = config.get_setting('checklinks_number', 'seriehd')

headers = [['Referer', host]]

@support.menu
def mainlist(item):    
    tvshow = [('Genere', ['', 'genre', 'tv']),
              ('Americane', ['/serie-tv-streaming/serie-tv-americane', 'peliculas', 'tv']),
              ('Italiane', ['/serie-tv-streaming/serie-tv-italiane', 'peliculas', 'tv']),]
    return locals()


def search(item, texto):
    log(texto)
    item.url = host + "/?s=" + texto
    try:
        return peliculas(item)

    # Continua la ricerca in caso di errore .
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def newest(categoria):
    log(categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "series":
            item.url = host
            itemlist = peliculas(item)

            if config.get_localized_string(30992) in itemlist[-1].title:
                itemlist.pop()

    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


@support.scrape
def genre(item):
    patronMenu = '<a href="(?P<url>[^"]+)">(?P<title>[^<]+)</a>'
    blacklist = ['Serie TV','Serie TV Americane','Serie TV Italiane','altadefinizione']
    patronBlock = '<ul class="sub-menu">(?P<block>.*)</ul>'
   
    return locals()

@support.scrape
def peliculas(item):
    patron = r'<h2>(?P<title>.*?)</h2>\s*<img src="(?P<thumb>[^"]+)" alt="[^"]*" />\s*<A HREF="(?P<url>[^"]+)">.*?<span class="year">(?P<year>[0-9]{4}).*?<span class="calidad">(?P<quality>[A-Z]+)'
    patronNext=r'<span class="current">\d+</span><a rel="nofollow" class="page larger" href="([^"]+)">\d+</a>'
    action='episodios'
    return locals()

def episodios(item):
    log()
    itemlist = []    
    url = support.match(item, patronBlock=r'<iframe width=".+?" height=".+?" src="([^"]+)" allowfullscreen frameborder="0">')[1]
    seasons = support.match(item, r'<a href="([^"]+)">(\d+)<', r'<h3>STAGIONE</h3><ul>(.*?)</ul>', headers, url)[0]
    for season_url, season in seasons:
        season_url = urlparse.urljoin(url, season_url)
        episodes = support.match(item, r'<a href="([^"]+)">(\d+)<', '<h3>EPISODIO</h3><ul>(.*?)</ul>', headers, season_url)[0]
        for episode_url, episode in episodes:
            episode_url = urlparse.urljoin(url, episode_url)
            title = season + "x" + episode.zfill(2)

            itemlist.append(
                Item(channel=item.channel,
                     action="findvideos",
                     contentType="episode",
                     title=support.typo(title + ' - ' +item.show,'bold'),
                     url=episode_url,
                     fulltitle=item.fulltitle,
                     show=item.show,
                     thumbnail=item.thumbnail))

    support.videolibrary(itemlist, item, 'color kod bold')

    return itemlist


def findvideos(item):
    log()
    itemlist = []
    itemlist = support.hdpass_get_servers(item)  
    return support.controls(itemlist, item)



