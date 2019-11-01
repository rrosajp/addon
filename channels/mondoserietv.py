# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per mondoserietv
# ----------------------------------------------------------

from core import support

__channel__ = "mondoserietv"
host = support.config.get_channel_url(__channel__)

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['akstream', 'wstream', 'vidtome', 'backin', 'nowvideo', 'verystream']
list_quality = ['default']

headers = {'Referer': host}

@support.menu
def mainlist(item):

    film = ['/lista-film',
            ('Ultimi Film Aggiunti', ['/ultimi-film-aggiunti', 'peliculas' , 'last'])]

    tvshow = ['/lista-serie-tv',
              ('HD {TV}', ['/lista-serie-tv-in-altadefinizione']),
              ('Anni 50 60 70 80 {TV}',['/lista-serie-tv-anni-60-70-80']),
              ('Serie Italiane',['/lista-serie-tv-italiane'])]

    anime = ['/lista-cartoni-animati-e-anime']

    docu = [('Documentari bullet bold',['/lista-documentari', 'peliculas', '', 'tvshow']),
            ('Cerca Documentari... submenu bold', ['/lista-documentari', 'search', '', 'tvshow'])]

    return locals()


@support.scrape
def search(item, text):
    support.log(text)
    if item.contentType == 'movie' or item.extra == 'movie':
        action = 'findvideos'
    else:
        action = 'episodios'
    try:
        search = text
        data = support.match(item, headers=headers)[1]
        if 'lcp_nextlink' in data:
            data += support.match(item, url=support.scrapertoolsV2.find_single_match(data, r'href="([^"]+)" title="[^"]+" class="lcp_nextlink"'), headers=headers)[1]
        patron = r'<li><a href="(?P<url>[^"]+)" title="(?P<title>.*?)(?:\s(?P<year>\d{4}))?"[^>]*>'
        return locals()

    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("%s" % line)
        return []


def newest(categoria):
    support.log(categoria)
    item = support.Item()
    try:
        if categoria == "series":
            item.contentType= 'tvshow'
            item.url = host + '/ultimi-episodi-aggiunti'
            item.args = "lastep"
        if categoria == "peliculas":
            item.contentType= 'movie'
            item.url = host + '/ultimi-film-aggiunti'
            item.args = "last"
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("{0}".format(line))
        return []


@support.scrape
def peliculas(item):
    pagination = ''
    patronNext = r'href="([^"]+)" title="[^"]+" class="lcp_nextlink"'
    if item.args == 'last':
        patronBlock = r'<table>(?P<block>.*?)</table>'
        patron = r'<tr><td><a href="(?P<url>[^"]+)">\s*[^>]+>(?P<title>.*?)(?:\s(?P<year>\d{4}))? (?:Streaming|</b>)'
    elif item.args == 'lastep':
        patronBlock = r'<table>(?P<block>.*?)</table>'
        patron = r'<td>\s*<a href="[^>]+>(?P<title>.*?)(?:\s(?P<year>\d{4}))?\s(?:(?P<episode>(?:\d+x\d+|\d+)))\s*(?P<title2>[^<]+)(?P<url>.*?)<tr>'
        action = 'findvideos'
    else:
        patronBlock = r'<div class="entry-content pagess">(?P<block>.*?)</ul>'
        patron = r'<li><a href="(?P<url>[^"]+)" title="(?P<title>.*?)(?:\s(?P<year>\d{4}))?"[^>]*>'
    if item.contentType == 'tvshow':
        action = 'episodios'
        anime = True
    return locals()


@support.scrape
def episodios(item):
    anime = True
    pagination = 50
    patronBlock = r'<table>(?P<block>.*?)</table>'
    patron = r'<tr><td><b>(?P<title>(?:\d+)?.*?)\s*(?:(?P<episode>(?:\d+x\d+|\d+)))\s*(?P<title2>[^<]+)(?P<url>.*?)<tr>'
    def itemHook(item):
        clear = support.re.sub(r'\[[^\]]+\]', '', item.title)
        if clear.isdigit():
            item.title = support. typo('Episodio ' + clear, 'bold')
        return item
    return locals()

def findvideos(item):
    if item.contentType == 'movie': return support.server(item)
    else: return support.server(item, item.url)
