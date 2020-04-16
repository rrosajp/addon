# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per ilcorsaronero
# ------------------------------------------------------------

from core import support

host = support.config.get_channel_url()
# host = 'https://ilcorsaronero.xyz'
headers = [['Referer', host]]

list_servers = ['torrent']
list_quality = ['default']

@support.menu
def mainlist(item):

    menu = [
        ('Film BDRiP', ['/categoria.php?active=0&category=1&order=data&by=DESC&page=', 'peliculas', [0, 'movie']]),
        ('Film DVD', ['/categoria.php?active=0&category=20&order=data&by=DESC&page=', 'peliculas', [0, 'movie']]),
        ('Film Screener', ['/categoria.php?active=0&category=19&order=data&by=DESC&page=', 'peliculas', [0, 'movie']]),
        ('Serie TV', ['/categoria.php?active=0&category=15&order=data&by=DES&page=', 'peliculas', [0 , 'tvshow']]),
        ('Anime', ['/categoria.php?active=0&category=5&order=data&by=DESC&page=', 'peliculas', [0, 'anime']]),
        ('Musica', ['/categoria.php?active=0&category=2&order=data&by=DESC&page=', 'peliculas', [0, 'music']]),
        ('Audiolibri {musica}', ['/categoria.php?active=0&category=18&order=data&by=DESC&page=', 'peliculas', [0, 'music']]),
        ('Altro {film}', ['/categoria.php?active=0&category=4&order=data&by=DESC&page=', 'peliculas', [0, 'movie']]),
        ('Cerca... submenu', ['/argh.php?search=', 'search', 'search'])
    ]

    return locals()


@support.scrape
def peliculas(item):
    patron = r'>(?P<quality>[^"<]+)</td> <TD[^>]+><A class="tab" HREF="(?P<url>[^"]+)"\s*>(?P<title>[^<]+)<[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<size>[^<]+)<[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<seed>[^<]+)'
    def itemHook(item):
        item.title = item.title.replace('.',' ')
        thumb = (item.args[1] if type(item.args) == list else item.args) + '.png'
        item.thumbnail = support.thumb(thumb=thumb)
        return item
    if 'search' not in item.args:
        support.log('OK')
        item.url += str(item.args[0])
        def itemlistHook(itemlist):
            itemlist.append(
                support.Item(channel=item.channel,
                            action = item.action,
                            contentType=item.contentType,
                            title=support.typo(support.config.get_localized_string(30992), 'color kod bold'),
                            url=item.url,
                            args=item.args[0] + 1,
                            thumbnail=support.thumb()))
            return itemlist
    return locals()


def search(item, text):
    support.log(item, text)

    itemlist = []
    item.url += text
    try:
        return peliculas(item)
    # Cattura la eccezione così non interrompe la ricerca globle se il canale si rompe!
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("search except: %s" % line)
        return []


def findvideos(item):
    return support.server(item, support.match(item.url, patron=r'"(magnet[^"]+)').match)
