# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Popcorn Stream
# ------------------------------------------------------------

from core import support, httptools
from core.item import Item
from platformcode import config

# __channel__ = "streamingaltadefinizione"
# host = config.get_channel_url(__channel__)

# host = headers = ''
host = 'https://www.popcornstream.fun'
list_servers = ['verystream', 'openload', 'wstream']
list_quality = ['1080p', 'HD', 'DVDRIP', 'SD', 'CAM']

def findhost():
    pass
    # global host, headers
    # permUrl = httptools.downloadpage('https://www.popcornstream.info', follow_redirects=False).headers
    # if 'google' in permUrl['location']:
    #     if host[:4] != 'http':
    #         host = 'https://'+permUrl['location'].replace('https://www.google.it/search?q=site:', '')
    #     else:
    #         host = permUrl['location'].replace('https://www.google.it/search?q=site:', '')
    # else:
    #     host = permUrl['location']
    # headers = [['Referer', host]]

@support.menu
def mainlist(item):
    findhost()
    film = ["/film/"]
    anime = ["/genere/anime/"]
    tvshow = ["/serietv/"]
    top = [('Generi',['', 'generos'])]

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
    findhost()
    return support.dooplay_peliculas(item, True if "/genere/" in item.url else False)


def episodios(item):
    findhost()
    return support.dooplay_get_episodes(item)


def findvideos(item):
    findhost()
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
