# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per vedohd
# ------------------------------------------------------------

from core import scrapertoolsV2, httptools, support
from core.item import Item
from platformcode import logger, config
from specials import autoplay

__channel__ = "netfreex"
host = config.get_channel_url(__channel__)
headers = ""

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['wstream']
list_quality = ['1080p', 'HD', 'SD', 'CAM']


@support.menu
def mainlist(item):

    film = ['/film',
        ('Generi', ['', 'menu', 'genres']),
        ('Anno', ['', 'menu', 'releases']),
    ]
    tvshow = ['/serietv']
    anime = ['/genere/anime']
    return locals()


def search(item, text):
    logger.info("[vedohd.py] " + item.url + " search " + text)
    item.url = item.url + "/?s=" + text

    return support.dooplay_search(item)


def peliculas(item):
    if 'anime' in item.url:
        return support.dooplay_peliculas(item, True)
    else:
        return support.dooplay_peliculas(item, False)


def episodios(item):
    return support.dooplay_get_episodes(item)


def findvideos(item):
    itemlist = []
    for link in support.dooplay_get_links(item, host):
        if link['title'] != 'Guarda il trailer':
            logger.info(link['title'])
            itemlist.append(
                Item(channel=item.channel,
                     action="play",
                     url=link['url'],
                     fulltitle=item.fulltitle,
                     thumbnail=item.thumbnail,
                     show=item.show,
                     quality=link['title'],
                     contentType=item.contentType,
                     folder=False))
    return support.server(item, itemlist=itemlist)


@support.scrape
def menu(item):
    return support.dooplay_menu(item, item.args)
