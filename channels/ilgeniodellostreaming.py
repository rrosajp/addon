# -*- coding: utf-8 -*-
# ------------------------------------------------------------
#
# Canale per ilgeniodellostreaming
# ------------------------------------------------------------

"""

    Alcuni video non si aprono sul sito...

    Avvisi per il test:
    i link per le categorie non sono TUTTI visibili nella pagina del sito:
    vanno costruiti con i nomi dei generi che vedete nel CANALE.
    Es:
        https://ilgeniodellostreaming.se/genere/+ genere nel canale
    genere-> kids
        https://ilgeniodellostreaming.se/genere/kids
    genere-> avventura
        https://ilgeniodellostreaming.se/genere/avventura
    Se il genere è formato da 2 parola lo spazio si trasforma in -
    genere-> televisione film
        https://ilgeniodellostreaming.se/genere/televisione-film

    Novità -> Serietv e Aggiornamenti nel canale:
        - le pagine sono di 25 titoli


    ##### note per i dev #########
    - La pagina "Aggiornamenti Anime" del sito è vuota (update 13-9-2019)
    - in url: film o serietv

"""

import re

from core import scrapertoolsV2, httptools, support
from core.support import log
from core.item import Item
from platformcode import config

__channel__ = 'ilgeniodellostreaming'
host = config.get_channel_url(__channel__)

list_servers = ['verystream', 'openload', 'streamango']
list_quality = ['default']

headers = [['Referer', host]]

@support.menu
def mainlist(item):
    support.log(item)

    film = ['/film/',
        ('Film Per Categoria',['', 'genres', 'genres']),
        ('Film Per Anno',['', 'genres', 'year']),
        ('Film Per Lettera',['/film-a-z/', 'genres', 'letter']),
        ('Popolari',['/trending/?get=movies', 'peliculas', 'populared']),
        ('Più Votati', ['/ratings/?get=movies', 'peliculas', 'populared'])
        ]

    tvshow = ['/serie/',
        ('Nuovi Episodi', ['/aggiornamenti-serie/', 'peliculas', 'update']),
        ('Popolari',['/trending/?get=tv', 'peliculas', 'populared']),
        ('Più Votati', ['/ratings/?get=tv', 'peliculas', 'populared'])

        ]

    anime = ['/anime/'
        ]

    Tvshow = [
        ('Show TV', ['/tv-show/', 'peliculas', '', 'tvshow'])
        ]

    search = ''

    return locals()


@support.scrape
def peliculas(item):
    log()

    if item.args == 'search':

        patronBlock = r'<div class="search-page">(?P<block>.*?)<footer class="main">'
        patron = r'<div class="thumbnail animation-2"><a href="(?P<url>[^"]+)">'\
                 '<img src="(?P<thumb>[^"]+)" alt="[^"]+" \/>[^>]+>(?P<type>[^<]+)'\
                 '<\/span>.*?<a href.*?>(?P<title>.+?)[ ]?(?:\[(?P<lang>Sub-ITA)\])?'\
                 '<\/a>[^>]+>(?:<span class="rating">IMDb\s*(?P<rating>[0-9.]+)<\/span>)?'\
                 '.+?(?:<span class="year">(?P<year>[0-9]+)<\/span>)?[^>]+>[^>]+><p>(?P<plot>.*?)<\/p>'

##        type_content_dict={'movie': ['film'], 'tvshow': ['tv']}
##        type_action_dict={'findvideos': ['film'], 'episodios': ['tv']}
        def itemHook(item):
            if 'film' not in item.url:
                item.contentType = 'tvshow'
                item.action = 'episodios'
            return item
    else:

        if item.contentType == 'movie':
            endBlock = '</article></div>'
        else:
            endBlock = '<footer class="main">'

        patronBlock = r'<header><h1>.+?</h1>(?P<block>.*?)'+endBlock

        if item.contentType == 'movie':
            if item.args == 'letter':
                patronBlock = r'<table class="table table-striped">(?P<block>.+?)</table>'
                patron = r'<img src="(?P<thumb>[^"]+)"[^>]+>[^>]+>[^>]+><td class="mlnh-2"><a href="(?P<url>[^"]+)">(?P<title>.+?)[ ]?(?:\[(?P<lang>Sub-ITA)\])?<[^>]+>[^>]+>[^>]+>(?P<year>\d{4})\s+<'
            elif item.args == 'populared':
                patron = r'<img src="(?P<thumb>[^"]+)" alt="[^"]+">[^>]+>[^>]+>[^>]+>[^>]+>\s+?(?P<rating>\d+.?\d+|\d+)<[^>]+>[^>]+>(?P<quality>[a-zA-Z\-]+)[^>]+>[^>]+>[^>]+>[^>]+><a href="(?P<url>[^"]+)">(?P<title>[^<]+)<[^>]+>[^>]+>[^>]+>(?P<year>\d+)<'
            else:

                patron = r'<div class="poster">\s*<a href="(?P<url>[^"]+)"><img src="(?P<thumb>[^"]+)" alt="[^"]+"><\/a>[^>]+>[^>]+>[^>]+>\s*(?P<rating>[0-9.]+)<\/div><span class="quality">(?:SUB-ITA|)?(?P<quality>|[^<]+)?<\/span>[^>]+>[^>]+>[^>]+>[^>]+>(?P<title>.+?)[ ]?(?:\[(?P<lang>Sub-ITA)\])?<\/a>[^>]+>[^>]+>(?P<year>[^<]+)<\/span>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<plot>[^<]+)<div'
        else:
            # TVSHOW
            action = 'episodios'
            if item.args == 'update':
                action = 'findvideos'
                patron = r'<div class="poster"><img src="(?P<thumb>[^"]+)"[^>]+>[^>]+><a href="(?P<url>[^"]+)">[^>]+>(?P<episode>[\d\-x]+)[^>]+>[^>]+>[^>]+>[^>]+>(?P<title>.+?)(?:\[(?P<lang>Sub-ITA|Sub-ita)\])?<[^>]+>[^>]+>[^>]+>[^>]+>(?P<quality>[HD]+)?(?:.+?)?/span><p class="serie"'
                pagination = 25
                def itemHook(item):
                    item.contentType = 'episode'
                    return item
            else:
                patron = r'<div class="poster">\s?<a href="(?P<url>[^"]+)"><img src="(?P<thumb>[^"]+)" alt="[^"]+"><\/a>[^>]+>[^>]+>[^>]+> (?P<rating>[0-9.]+)<[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<title>.+?)[ ]?(?:\[(?P<lang>Sub-ITA|Sub-ita)\])?<[^>]+>[^>]+>[^>]+>(?P<year>[^<]+)(?:<.*?<div class="texto">(?P<plot>[^<]+))?'

    patronNext = '<span class="current">[^<]+<[^>]+><a href="([^"]+)"'

    #support.regexDbg(item, patron, headers)
    #debug = True
    return locals()


@support.scrape
def episodios(item):
    log()

    patronBlock = r'<h1>.*?[ ]?(?:\[(?P<lang>.+?\]))?</h1>.+?<div class="se-a" '\
                  'style="display:block"><ul class="episodios">(?P<block>.*?)</ul>'\
                  '</div></div></div></div></div>'
    patron = r'<a href="(?P<url>[^"]+)"><img src="(?P<thumb>[^"]+)">.*?'\
             '<div class="numerando">(?P<episode>[^<]+).*?<div class="episodiotitle">'\
             '[^>]+>(?P<title>[^<]+)<\/a>'
#    debug = True
    return locals()

@support.scrape
def genres(item):
    log(item)

    action='peliculas'
    if item.args == 'genres':
        patronBlock = r'<div class="sidemenu"><h2>Genere</h2>(?P<block>.*?)/li></ul></div>'
    elif item.args == 'year':
        item.args = 'genres'
        patronBlock = r'<div class="sidemenu"><h2>Anno di uscita</h2>(?P<block>.*?)/li></ul></div>'
    elif item.args == 'letter':
        patronBlock = r'<div class="movies-letter">(?P<block>.*?)<div class="clearfix">'

    patron = r'<a(?:.+?)?href="(?P<url>.*?)"[ ]?>(?P<title>.*?)<\/a>'

##    debug = True
    return locals()

def search(item, text):
    log(text)
    itemlist = []
    text = text.replace(' ', '+')
    item.url = host + "/?s=" + text
    try:
        item.args = 'search'
        return peliculas(item)
    except:
        import sys
        for line in sys.exc_info():
            log("%s" % line)

    return []

def newest(categoria):
    log(categoria)
    itemlist = []
    item = Item()

    if categoria == 'peliculas':
        item.contentType = 'movie'
        item.url = host + '/film/'
    elif categoria == 'series':
        item.args = 'update'
        item.contentType = 'tvshow'
        item.url = host + '/aggiornamenti-serie/'
##    elif categoria == 'anime':
##        item.contentType = 'tvshow'
##        item.url = host + '/anime/'
    try:
        item.action = 'peliculas'
        itemlist = peliculas(item)

    except:
        import sys
        for line in sys.exc_info():
            log("{0}".format(line))
        return []

    return itemlist


def findvideos(item):
    log()
    itemlist =[]

    matches, data = support.match(item, '<iframe class="metaframe rptss" src="([^"]+)"[^>]+>',headers=headers)
    for url in matches:
        html = httptools.downloadpage(url, headers=headers).data
        data += str(scrapertoolsV2.find_multiple_matches(html, '<meta name="og:url" content="([^"]+)">'))

    itemlist = support.server(item, data)

    if item.args == 'update':

        data = httptools.downloadpage(item.url).data
        patron = r'<div class="item"><a href="'+host+'/serietv/([^"\/]+)\/"><i class="icon-bars">'
        series = scrapertoolsV2.find_single_match(data, patron)
        titles = support.typo(series.upper().replace('-', ' '), 'bold color kod')
        goseries = support.typo("Vai alla Serie:", ' bold color kod')
        itemlist.append(
            Item(channel=item.channel,
                    title=goseries + titles,
                    fulltitle=titles,
                    show=series,
                    contentType='tvshow',
                    contentSerieName=series,
                    url=host+"/serietv/"+series,
                    action='episodios',
                    contentTitle=titles,
                    plot = "Vai alla Serie " + titles + " con tutte le puntate",
                    ))
    return itemlist
