# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Streaming Altadefinizione
# ------------------------------------------------------------

from core import support
from core.item import Item
from specials import autoplay
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
    return support.dooplay_films(item)


def episodios(item):
    return support.dooplay_get_episodes(item)


def findvideos(item):
    itemlist = []
    for link in support.dooplay_get_links(item, host):
        server = link['server'][:link['server'].find(".")]
        itemlist.append(
            Item(channel=item.channel,
                 action="play",
                 title=server + " [COLOR blue][" + link['title'] + "][/COLOR]",
                 url=link['url'],
                 server=server,
                 fulltitle=item.fulltitle,
                 thumbnail=item.thumbnail,
                 show=item.show,
                 quality=link['title'],
                 contentType=item.contentType,
                 folder=False))

    autoplay.start(itemlist, item)

    return itemlist