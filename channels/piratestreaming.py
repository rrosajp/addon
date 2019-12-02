# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per piratestreaming
# ----------------------------------------------------------


from core import support
from core.support import config, log

__channel__ = "piratestreaming"
host = config.get_channel_url(__channel__)

list_servers = ['mixdrop', 'speedvideo', 'gounlimited', 'onlystream', 'youtube']
list_quality = ['default']


checklinks = config.get_setting('checklinks', 'piratestreaming')
checklinks_number = config.get_setting('checklinks_number', 'piratestreaming')

headers = [['Referer', host]]

@support.menu
def mainlist(item):

    film = ['/category/films']
    tvshow = ['/category/serie']
    anime = ['/category/anime-cartoni-animati']
    search = ''

    return locals()


def search(item, texto):
    log(texto)
    item.url = host + "/?s=" + texto
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("%s" % line)
        return []


@support.scrape
def peliculas(item):
    patron = r'data-placement="bottom" title="(?P<title>[^"]+)" alt=[^=]+="(?P<url>[^"]+)"> <img class="[^"]+" title="[^"]+" alt="[^"]+" src="(?P<thumb>[^"]+)"'
    patronNext = r'<a\s*class="nextpostslink" rel="next" href="([^"]+)">Avanti'
    def itemHook(item):
        item.thumbnail = item.thumbnail.replace('locandina-film-small','locandina-film-big')
        if 'serie' in item.url:
            item.contentType = 'tvshow'
            item.action = 'episodios'
        return item
    return locals()


@support.scrape
def episodios(item):
    if item.data:
        data = item.data
    title = item.title
    patron = r'link-episode">\s*(?P<title>\d+.\d+)[^>]+<\/span>\s*(?P<url>.*?)</div>'
    def itemHook(item):
        item.title += support.typo(' - ', 'bold') + title
        return item
    return locals()


def findvideos(item):
    if item.contentType == 'episode':
        data = item.url
    else:
        data = support.match(item)[1]
        if 'link-episode' in data:
            item.data = data
            return episodios(item)
    return support.server(item, data=data)
