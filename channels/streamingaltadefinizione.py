# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Streaming Altadefinizione
# ------------------------------------------------------------
"""
    Trasformate le sole def per support.menu e support.scrape
    da non inviare nel test.
    Test solo a trasformazione completa

"""

from core import support
from core.item import Item
from platformcode import config

__channel__ = "streamingaltadefinizione"
host = config.get_channel_url(__channel__)

list_servers = ['verystream', 'openload', 'wstream']
list_quality = ['1080p', 'HD', 'DVDRIP', 'SD', 'CAM']

@support.menu
def mainlist(item):
    film = ["/film/"]
    anime = ["/genere/anime/",
        ('Film Anime', ["/genere/anime/", 'peliculas']),
        ('Film Anime per genere', ["/genere/anime/", 'generos'])
    ]
    tvshow = ["/serietv/"]

    return locals()


def search(item, text):
    support.log("[streamingaltadefinizione.py] " + item.url + " search " + text)
    item.url = item.url + "/?s=" + text

    return support.dooplay_search(item)


@support.scrape
def generos(item):
    patron = '<a href="(?P<url>[^"#]+)">(?P<title>[a-zA-Z]+)'
    patronBlock='<a href="#">Genere</a><ul class="sub-menu">(?P<block>.*?)</ul>'
    action='peliculas'

    return locals()


def peliculas(item):
    support.dbg()
    return support.dooplay_peliculas(item, True if "/genere/anime/" in item.url else False)


def episodios(item):
    return support.dooplay_get_episodes(item)


def findvideos(item):
    itemlist = []
    for link in support.dooplay_get_links(item, host):
        if link['title'] != 'Guarda il trailer':
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
