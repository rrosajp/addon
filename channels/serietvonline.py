# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per serietvonline
# ----------------------------------------------------------
"""

    Novità. Indicare in quale/i sezione/i è presente il canale:
       - film, serie

    Avvisi:
        - Al massimo 25 titoli per le sezioni: Film
        - Al massimo 35 titoli per le sezioni: Tutte le altre


"""
import re
from core import support, httptools, scrapertoolsV2
from platformcode import config
from core.item import Item

__channel__ = "serietvonline"

host = ""
headers = ""

def findhost():
    global host, headers
    data = httptools.downloadpage('https://serietvonline.me/').data
    host = scrapertoolsV2.find_single_match(data, r'<a class="pure-button pure-button-primary" title=\'serie tv online\' href="([^"]+)">')
    headers = [['Referer', host]]
findhost()

list_servers = ['akvideo', 'wstream', 'backin', 'vidtome', 'nowvideo']
list_quality = ['default']


@support.menu
def mainlist(item):
    support.log()

    film = ['/ultimi-film-aggiunti/',
            ('Lista', ['/lista-film/', 'peliculas', 'lista'])
        ]

    tvshow = ['',
            ('Aggiornamenti', ['/ultimi-episodi-aggiunti/', 'peliculas', 'update']),
            ('Tutte', ['/lista-serie-tv/', 'peliculas', 'qualcosa']),
            ('Italiane', ['/lista-serie-tv-italiane/', 'peliculas', 'qualcosa']),
            ('Anni 50-60-70-80-90', ['/lista-serie-tv-anni-60-70-80/', 'peliculas', 'qualcosa']),
            ('HD', ['/lista-serie-tv-in-altadefinizione/', 'peliculas', 'qualcosa'])
        ]

    anime = ['/lista-cartoni-animati-e-anime/']

    documentari = [('Documentari', ['/lista-documentari/' , 'peliculas' , 'doc', 'tvshow'])]

    search = ''

    return locals()

@support.scrape
def peliculas(item):
    support.log()

    blacklist = ['DMCA', 'Contatti', 'Attenzione NON FARTI OSCURARE', 'Lista Ccartoni Animati e Anime']
    patronBlock = r'<h1>.+?</h1>(?P<block>.*?)<div class="footer_c">'
    patronNext = r'<div class="siguiente"><a href="([^"]+)" >'

##    if 'film' in item.url:
##        contentType = 'movie'
##        action = 'findvideos'
##    else:
##        contentType = 'tvshow'
##        action = 'episodios'

    if item.args == 'search':
        patronBlock = r'>Lista Serie Tv</a></li></ul></div><div id="box_movies">(?P<block>.*?)<div id="paginador">'
        patron = r'<div class="movie">[^>]+[^>]+>\s?<img src="(?P<thumb>[^"]+)" alt="(?P<title>.+?)\s?(?P<year>[\d\-]+)?"[^>]+>\s?<a href="(?P<url>[^"]+)">'

##        def itemHook(item):
##            if 'film' in item.url:
##                item.action = 'findvideos'
##                item.contentType = 'movie'
##            else:
##                item.contentType = 'tvshow'
##                item.action = 'episodios'
##            return item

    elif item.contentType == 'tvshow':
        # SEZIONE Serie TV- Anime - Documentari
        pagination = 35

        if not item.args and 'anime' not in item.url:
            patron = r'<div class="movie">[^>]+>.+?src="(?P<thumb>[^"]+)" alt="[^"]+".+?href="(?P<url>[^"]+)">[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[ ](?P<rating>\d+.\d+|\d+)<[^>]+>[^>]+><h2>(?P<title>[^"]+)</h2>[ ]?(?:<span class="year">(?P<year>\d+|\-\d+))?<'
        else:
            patron = r'(?:<td>)?<a href="(?P<url>[^"]+)"(?:[^>]+)?>\s?(?P<title>[^<]+)(?P<episode>[\d\-x]+)?(?P<title2>[^<]+)?<'
            if item.args == 'update':
                action = 'findvideos'
                patron = r'<td><a href="(?P<url>[^"]+)"(?:[^>]+)?>\s?(?P<title>[^<]+)(?P<episode>[\d\-x]+)?(?P<title2>[^<]+)?<'

    else:
        # SEZIONE FILM
        pagination = 25

        if item.args == 'lista':
            patron = r'href="(?P<url>[^"]+)"[^>]+>(?P<title>.*?)[ ]?(?P<year>\d+)?(?: Streaming | MD iSTANCE )?<'
            patronBlock = r'Lista dei film disponibili in streaming e anche in download\.</p>(?P<block>.*?)<div class="footer_c">'

        else:
            #patronBlock = r'<h1>Ultimi film aggiunti</h1>(?P<block>.*?)<div class="footer_c">'
            patron = r'<tr><td><a href="(?P<url>[^"]+)"(?:|.+?)?>(?:&nbsp;&nbsp;)?[ ]?(?P<title>.*?)[ ]?(?:HD)?[ ]?(?P<year>\d+)?(?: | HD | Streaming | MD(?: iSTANCE)? )?</a>'

    def itemHook(item):
        if 'film' in item.url:
            item.action = 'findvideos'
            item.contentType = 'movie'
        elif item.args == 'update':
            pass
        else:
            item.contentType = 'tvshow'
            item.action = 'episodios'
        return item

    #support.regexDbg(item, patronBlock, headers)
    #debug = True
    return locals()


@support.scrape
def episodios(item):
    support.log()

    action = 'findvideos'
    patronBlock = r'<table>(?P<block>.*?)<\/table>'
    patron = r'<tr><td>(?:[^<]+)[ ](?:Parte)?(?P<episode>\d+x\d+)(?:|[ ]?(?P<title2>.+?)?(?:avi)?)<(?P<url>.*?)</td><tr>'

    #debug = True
    return locals()


def search(item, text):
    support.log("CERCA :" ,text, item)
    item.url = "%s/?s=%s" % (host, text)

    try:
        item.args = 'search'
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.log("%s" % line)
        return []

def newest(categoria):
    support.log(categoria)
    itemlist = []
    item = Item()

    if categoria == 'peliculas':
        item.contentType = 'movie'
        item.url = host + '/ultimi-film-aggiunti/'
    elif categoria == 'series':
        item.args = 'update'
        item.contentType = 'tvshow'
        item.url = host +'/ultimi-episodi-aggiunti/'
    try:
        item.action = 'peliculas'
        itemlist = peliculas(item)

    except:
        import sys
        for line in sys.exc_info():
            support.log("{0}".format(line))
        return []

    return itemlist

def findvideos(item):
    support.log()
    if item.contentType == 'movie':
        return support.server(item, headers=headers)
    else:

        if item.args != 'update':
            return support.server(item, item.url)
        else:
            itemlist = []
            item.infoLabels['mediatype'] = 'episode'

            data = httptools.downloadpage(item.url, headers=headers).data
            data = re.sub('\n|\t', ' ', data)
            data = re.sub(r'>\s+<', '> <', data)
            support.log("DATA - HTML:\n", data)
            url_video = scrapertoolsV2.find_single_match(data, r'<tr><td>(.+?)</td><tr>', -1)
            url_serie = scrapertoolsV2.find_single_match(data, r'<link rel="canonical" href="([^"]+)"\s?/>')
            goseries = support.typo("Vai alla Serie:", ' bold')
            series = support.typo(item.contentSerieName, ' bold color kod')
            itemlist = support.server(item, data=url_video)

            itemlist.append(
                Item(channel=item.channel,
                        title=goseries + series,
                        fulltitle=item.fulltitle,
                        show=item.show,
                        contentType='tvshow',
                        contentSerieName=item.contentSerieName,
                        url=url_serie,
                        action='episodios',
                        contentTitle=item.contentSerieName,
                        plot = goseries + series + "con tutte le puntate",
                        ))

        return itemlist
