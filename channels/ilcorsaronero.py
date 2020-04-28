# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per ilcorsaronero
# ------------------------------------------------------------

from core import support

def findhost():
    data = support.httptools.downloadpage('https://lagazzettadelcorsaro.com/').data
    return support.scrapertools.find_single_match(data, '<li><a href="([^"]+)')

host = support.config.get_channel_url(findhost)
# host = 'https://ilcorsaronero.xyz'
headers = [['Referer', host]]

list_servers = ['torrent']
list_quality = ['default']

@support.menu
def mainlist(item):

    menu = [
        ('BDRiP {film}', ['/categoria.php?active=0&category=1&order=data&by=DESC&page=', 'peliculas', [0, 'movie', True]]),
        ('Cerca BDRiP... submenu {film}', ['/categoria.php?active=0&category=1&order=data&by=DESC&argh.php?search=', 'search', ['search', 'movie', True]]),
        ('DVD {film}', ['/categoria.php?active=0&category=20&order=data&by=DESC&page=', 'peliculas', [0, 'movie', True]]),
        ('Cerca DVD... submenu {film}', ['/categoria.php?active=0&category=20&order=data&by=DESC&argh.php?search=', 'search', ['search', 'movie', True]]),
        ('Screener {film}', ['/categoria.php?active=0&category=19&order=data&by=DESC&page=', 'peliculas', [0, 'movie', True]]),
        ('Cerca Screener.. submenu {film}', ['/categoria.php?active=0&category=19&order=data&by=DESC&argh.php?search=', 'search', ['search', 'movie', True]]),
        ('Serie TV', ['/categoria.php?active=0&category=15&order=data&by=DES&page=', 'peliculas', [0 , 'tvshow', True]]),
        ('Cerca Serie TV.. submenu', ['/categoria.php?active=0&category=15&order=data&by=DESC&argh.php?search=', 'search', ['search', 'tvshow',True]]),
        ('Anime', ['/categoria.php?active=0&category=5&order=data&by=DESC&page=', 'peliculas', [0, 'anime', True]]),
        ('Cerca Anime.. submenu', ['/categoria.php?active=0&category=5&order=data&by=DESC&argh.php?search=', 'search', ['search', 'anime', True]]),
        ('Musica', ['/categoria.php?active=0&category=2&order=data&by=DESC&page=', 'peliculas', [0, 'music', False]]),
        ('Cerca Musica.. submenu', ['/categoria.php?active=0&category=2&order=data&by=DESC&argh.php?search=', 'search', ['search', 'music', False]]),
        ('Audiolibri {musica}', ['/categoria.php?active=0&category=18&order=data&by=DESC&page=', 'peliculas', [0, 'music', False]]),
        ('Cerca Audiolibri.. submenu', ['/categoria.php?active=0&category=18&order=data&by=DESC&argh.php?search=', 'search', ['search', 'music', False]]),
        ('Altro {film}', ['/categoria.php?active=0&category=4&order=data&by=DESC&page=', 'peliculas', [0, 'movie', False]]),
        ('Cerca altro.. submenu', ['/categoria.php?active=0&category=4&order=data&by=DESC&argh.php?search=', 'search', ['search', 'movie', False]]),
        ('Cerca Tutto... color kod bold', ['/argh.php?search=', 'search', ['search', 'all', False]])
    ]

    return locals()


@support.scrape
def peliculas(item):
    sceneTitle = item.args[2]
    if item.args[1] in ['tvshow', 'anime', 'music']:
        patron = r'>[^"<]+'
    else:
        patron = r'>(?P<quality>[^"<]+)'
    patron += '</td> <TD[^>]+><A class="tab" HREF="(?P<url>[^"]+)"\s*>(?P<title>[^<]+)<[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<size>[^<]+)<[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<seed>[^<]+)'
    def itemHook(item):
        # item.title = item.title.replace('.',' ')
        item.contentType = item.args[1]
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
                            args=[item.args[0] + 1, item.args[1]],
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
    video_library = True if 'movie' in item.args else False
    return support.server(item, support.match(item.url, patron=r'"(magnet[^"]+)').match,down_load=False, video_library=video_library)
