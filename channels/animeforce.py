# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per AnimeForce
# ------------------------------------------------------------

from servers.decrypters import adfly
from core import support

host = support.config.get_channel_url()

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['directo', 'openload', 'vvvvid']
list_quality = ['default']


headers = [['Referer', host]]


@support.menu
def mainlist(item):
    anime = ['/lista-anime/',
             ('In Corso',['/lista-anime-in-corso/', 'peliculas', 'corso']),
             ('Ultime Serie',['/category/anime/articoli-principali/','peliculas','last'])
            ]
    return locals()


def newest(categoria):
    support.log(categoria)
    itemlist = []
    item = support.Item()
    try:
        if categoria == "anime":
            item.contentType = 'tvshow'
            item.url = host
            item.args = 'newest'
            return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("{0}".format(line))
        return []

    return itemlist

@support.scrape
def search(item, texto):
    # debug = True
    search = texto
    item.contentType = 'tvshow'
    patron = r'<a href="(?P<url>[^"]+)">\s*<strong[^>]+>(?P<title>[^<]+)<'
    action = 'episodios'
    return locals()


@support.scrape
def peliculas(item):
    anime = True
    action = 'episodios'

    if item.args == 'newest':
        patron = r'<a href="(?P<url>[^"]+)">\s*<img src="(?P<thumb>[^"]+)" alt="(?P<title>.*?)(?: Sub| sub| SUB|")'
        action = 'findvideos'

    elif item.args == 'last':
        patron = r'<a href="(?P<url>[^"]+)">\s*<img src="(?P<thumb>[^"]+)" alt="(?P<title>.*?)(?: Sub| sub| SUB|")'

    elif item.args == 'corso':
        pagination = ''
        patron = r'<strong><a href="(?P<url>[^"]+)">(?P<title>.*?) [Ss][Uu][Bb]'
    else:
        pagination = ''
        patron = r'<a href="(?P<url>[^"]+)">\s*<strong[^>]+>(?P<title>[^<]+)<'

    def itemHook(item):
        if 'sub-ita' in item.url:
            if item.args != 'newest': item.title = item.title + support.typo('Sub-ITA','_ [] color kod')
            item.contentLanguage = 'Sub-ITA'
        if item.args == 'newest':
            url = support.match(item, '<a href="([^"]+)" title="[^"]+" target="[^"]+" class="btn', headers=headers)[0]
            item.url = url[0] if url else ''
            delete = support.scrapertoolsV2.find_single_match(item.fulltitle, r'( Episodi.*)')
            episode = support.scrapertoolsV2.find_single_match(item.title, r'Episodi(?:o)? (?:\d+÷)?(\d+)')
            item.title = support.typo(episode + ' - ','bold') + item.title.replace(delete,'')
            item.fulltitle = item.show = item.title.replace(delete,'')
            item.episode = episode
        return item

    return locals()


@support.scrape
def episodios(item):
    anime = True
    patron = r'<td style[^>]+>\s*.*?(?:<span[^>]+)?<strong>(?P<title>[^<]+)<\/strong>.*?<td style[^>]+>\s*<a href="(?P<url>[^"]+)"[^>]+>'
    def itemHook(item):
        item.url = item.url.replace(host, '')
        return item
    action = 'findvideos'
    return locals()


def findvideos(item):
    support.log(item)

    itemlist = []

    if item.episode:
        from lib import unshortenit
        url, c = unshortenit.unshorten(item.url)
        url = support.match(item, r'<a href="([^"]+)"[^>]*>', patronBlock=r'Episodio %s(.*?)</tr>' % item.episode ,url=url)[0]
        item.url = url[0] if url else ''

    if 'vvvvid' in item.url:
        item.action = 'play'
        itemlist.append(item)

    if 'http' not in item.url:
        if '//' in item.url[:2]:
            item.url = 'http:' + item.url
        elif host not in item.url:
            item.url = host + item.url

    if 'adf.ly' in item.url:
        item.url = adfly.get_long_url(item.url)
    elif 'bit.ly' in item.url:
        item.url = support.httptools.downloadpage(item.url, only_headers=True, follow_redirects=False).headers.get("location")

    matches = support.match(item, r'button"><a href="([^"]+)"')[0]

    for video in matches:
        itemlist.append(
            support.Item(channel=item.channel,
                        action="play",
                        title='diretto',
                        url=video,
                        server='directo'))

    return support.server(item, itemlist=itemlist)
