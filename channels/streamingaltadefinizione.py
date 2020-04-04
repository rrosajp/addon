# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Popcorn Stream
# ------------------------------------------------------------

from core import support, httptools
from core.item import Item
from platformcode import config


list_servers = ['verystream', 'openload', 'wstream']
list_quality = ['1080p', 'HD', 'DVDRIP', 'SD', 'CAM']

def findhost():
    permUrl = httptools.downloadpage('https://www.popcornstream.info', follow_redirects=False).headers
    if 'google' in permUrl['location']:
        host = permUrl['location'].replace('https://www.google.it/search?q=site:', '')
        if host[:4] != 'http':
            host = 'https://'+permUrl['location'].replace('https://www.google.it/search?q=site:', '')
    else:
        host = permUrl['location']
    return host

host = config.get_channel_url(findhost)
headers = [['Referer', host]]

@support.menu
def mainlist(item):

    film = ["/film/"]
    anime = ["/genere/anime/"]
    tvshow = ["/serietv/"]
    top = [('Generi',['', 'genre'])]

    return locals()


def search(item, text):
    support.log("[streamingaltadefinizione.py] " + item.url + " search " + text)
    item.url = item.url + "/?s=" + text
    try:
        return support.dooplay_search(item)
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("%s" % line)
        return []


@support.scrape
def genre(item):
    patronMenu = '<a href="(?P<url>[^"#]+)">(?P<title>[a-zA-Z]+)'
    patronBlock='<a href="#">Genere</a><ul class="sub-menu">(?P<block>.*?)</ul>'
    action='peliculas'

    return locals()


def peliculas(item):

    return support.dooplay_peliculas(item, True if "/genere/" in item.url else False)


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
