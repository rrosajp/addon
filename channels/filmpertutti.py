# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per filmpertutti.py
# ------------------------------------------------------------
"""
    Questi sono commenti per i beta-tester.

    Su questo canale, nella categoria 'Ricerca Globale'
    non saranno presenti le voci 'Aggiungi alla Videoteca'
    e 'Scarica Film'/'Scarica Serie', dunque,
    la loro assenza, nel Test, NON dovrà essere segnalata come ERRORE.

    Novità (globale). Indicare in quale/i sezione/i è presente il canale:
       - film, serie
       - I titoli in questa sezione a gruppi di 20

"""
import re

from core import scrapertoolsV2, httptools, support
from core.item import Item
from platformcode import config


__channel__ = 'filmpertutti'
host = config.get_channel_url(__channel__)
headers = [['Referer', host]]
list_servers = ['speedvideo', 'verystream', 'openload', 'streamango', 'wstream', 'akvideo']
list_quality = ['HD', 'SD']

@support.menu
def mainlist(item):

    film = ['/category/film/',
        ('Generi', ['/category/film/', 'genres', 'lettersF'])
        ]

    tvshow = ['/category/serie-tv/',
              ('Aggiornamenti', ['/aggiornamenti-serie-tv/', 'peliculas', 'newest']),
              ('Per Lettera', ['/category/serie-tv/', 'genres', 'lettersS'])
        ]

    search = ''
    return locals()

@support.scrape
def peliculas(item):
    support.log()

    if item.args != 'newest':
        patronBlock = r'<ul class="posts">(?P<block>.*)<\/ul>'
        patron = r'<li><a href="(?P<url>[^"]+)" data-thumbnail="(?P<thumb>[^"]+)">.*?<div class="title">(?P<title>.+?)(?:\[(?P<lang>Sub-ITA)\])?(?:[ ]\[?(?P<quality>[HD]+)?\])?(?:[ ]\((?P<year>\d+)\)?)?<\/div>'
        patronNext = r'<a href="([^"]+)" >Pagina'

    else:
        patronBlock = r'<ul class="posts">(?P<block>.*)<div class="clear">'
        patron = r'<li>\s?<a href="(?P<url>[^"]+)" data-thumbnail="(?P<thumb>[^"]+)">.*?<div class="title">(?P<title>.+?)(?:\s\[(?P<quality>HD)\])?<\/div>[^>]+>(?:[\dx]+)\s?(?:[ ]\((?P<lang>[a-zA-Z\-]+)\))?.+?</div>'
        pagination = ''
        
    if item.args == 'search':
        action = 'select'
    elif item.contentType == 'tvshow':
        action = 'episodios'
    elif item.contentType == 'movie':
        action ='findvideos'
    else:
        action = 'select'

    def itemHook(item):
        item.title = item.title.replace(r'-', ' ')
        return item
    #debug = True
    return locals()

@support.scrape
def episodios(item):
    support.log()

    data = httptools.downloadpage(item.url, headers=headers).data
    data = re.sub('\n|\t', ' ', data)
    data = re.sub(r'>\s+<', '> <', data)

    if 'accordion-item' in data:
        #patronBlock = r'<span class="season(?:|-title)">(?P<season>\d+)[^>]+>[^>]+>\s+?[^>]+>[^>]+>.+?(?:STAGIONE|Stagione).+?\s(?P<lang>[a-zA-Z\-]+).+?</span>(?P<block>.*?)<div id="disqus_thread">'
        patronBlock = r'<span class="season(?:|-title)">(?P<season>\d+)[^>]+>[^>]+>\s+?[^>]+>[^>]+>.+?(?:STAGIONE|Stagione).+?\s(?P<lang>[a-zA-Z\-]+)</span>(?P<block>.*?)\s*(?:<li class="s_title">|<div id="disqus_thread">)'
        patron = r'<img src="(?P<thumb>[^"]+)">.*?<li class="season-no">(?P<episode>.*?)<\/li>(?P<url>.*?javascript:;">(?P<title>[^<]+)<.+?)<\/table>'
    else:
        patronBlock = r'<div id="info" class="pad">(?P<block>.*?)<div id="disqus_thread">'
        patron = r'<strong>(?P<lang>.*?)<\/strong>.*?<p>(?P<season>.*?)<span'

    #debug = True
    return locals()


@support.scrape
def genres(item):
    support.log()
    itemlist = []

    if item.args == 'lettersF':
        item.contentType = 'movie'
    else:
        item.contentType = 'tvshow'

    action = 'peliculas'
    patronBlock = r'<select class="cats">(?P<block>.*?)<\/select>'
    patron = r'<option data-src="(?P<url>[^"]+)">(?P<title>.*?)<\/option>'

    return locals()

def select(item):
    support.log()


    data = httptools.downloadpage(item.url, headers=headers).data
    patronBlock = scrapertoolsV2.find_single_match(data, r'class="taxonomy category" ><span property="name">(.*?)</span></a><meta property="position" content="2">')
    if patronBlock.lower() != 'film':
        support.log('select = ### è una serie ###')
        return episodios(Item(channel=item.channel,
                              title=item.title,
                              fulltitle=item.fulltitle,
                              contentSerieName = item.fulltitle,
                              url=item.url,
                              contentType='tvshow'))
    else:
        support.log('select = ### è un movie ###')
        return findvideos(Item(channel=item.channel,
                              title=item.title,
                              fulltitle=item.fulltitle,
                              url=item.url,
                              contentType='movie'))


def search(item, texto):
    support.log()
    item.url = host + "/?s=" + texto
    item.contentType = 'episode'
    item.args = 'search'
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.log("%s" % line)
        return []


def newest(categoria):
    support.log()
    itemlist = []
    item = Item()
    try:
        if categoria == "peliculas":
            item.url = host + "/category/film/"
            item.action = "peliculas"
            item.extra = "movie"
            item.contentType = 'movie'
            itemlist = peliculas(item)
        else:
            item.url = host + "/aggiornamenti-serie-tv/"
            item.action = "peliculas"
            item.args = "newest"
            item.contentType = 'tvshow'
            itemlist = peliculas(item)

##        if itemlist[-1].action == "peliculas":
##            itemlist.pop()

    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.log("{0}".format(line))
        return []

    return itemlist


def findvideos(item):
    if item.contentType == 'movie':
        return support.server(item)
    else:
        return support.server(item, item.url)
