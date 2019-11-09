# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per 'cinemaLibero'
# ------------------------------------------------------------
"""
    Questi sono commenti per i beta-tester.

    25 titoli per le novità di qualsiasi sezione.

    NON CONTROLLARE LE SEZIONE SPORT - ANIME, HANNO PROBLEMI!!!
    è stata eliminata dall'elenco ma i titoli possono apparire nella ricerca o tra le novità
    Non è errore se dà problemi!!! NON CONSIDERATELA!

    Novità. Indicare in quale/i sezione/i è presente il canale:
       - FILM - SERIE

"""

import re

from core import httptools, support, scrapertoolsV2
from core.item import Item
from platformcode import config

list_servers = ['akstream', 'wstream', 'backin']
list_quality = ['default']

__channel__ = "cinemalibero"
host = config.get_channel_url(__channel__)
headers = [['Referer', host]]

@support.menu
def mainlist(item):
    support.log()

    film = ['/category/film/',
            ('Generi', ['', 'genres'])
        ]

    tvshow = ['/category/serie-tv/'
        ]

##    Anime = [(support.typo('Anime', 'bullet bold'),['/category/anime-giapponesi/', 'peliculas', 'anime', 'tvshow'])
##        ]

##    Sport = [(support.typo('Sport', 'bullet bold'), ['/category/sport/', 'peliculas', 'sport', 'tvshow'])
##        ]
    news = [('Novità Serie-Anime', ['/aggiornamenti-serie-tv/', 'peliculas', 'update', 'tvshow'])]

    search = ''

    return locals()


@support.scrape
def peliculas(item):
    support.log()
    #debug = True

    patronBlock = r'<div class="container">.*?class="col-md-12[^"]*?">(?P<block>.*?)<div class=(?:"container"|"bg-dark ")>'
    if item.contentType == 'movie':
        patron = r'<div class="col-lg-3">[^>]+>[^>]+>\s<a href="(?P<url>[^"]+)".+?url\((?P<thumb>[^\)]+)\)">[^>]+>[^>]+>[^>]+>\s?(?P<rating>[\d\.]+)?[^>]+>[^>]+>(?P<title>.+?)\(?(?P<year>\d+)?\)?<[^>]+>[^>]+>(?P<quality>[^<]+)?<'
    elif item.args == 'anime':
        patron = r'<div class="col-lg-3">[^>]+>[^>]+>\s<a href="(?P<url>[^"]+)".+?url\((?P<thumb>[^\)]+)\)">[^>]+>[^>]+>[^>]+>\s?(?P<rating>[\d\.]+)?[^>]+>[^>]+>(?P<title>.+?)\(?(?P<year>\d+)?\)?<[^>]+>[^>]+>(?:.+?[^fFiInNeE]+?\(?(?P<lang>[sSuUbBiItTaA]+)\)?.+?)<'
    elif item.args == 'update':
        pagination = 25
        patron = r'<div class="card-body p-0">\s<a href="(?P<url>[^"]+)".+?url\((?P<thumb>.+?)\)">\s<div class="titolo">(?P<title>.+?)(?: &#8211; Serie TV)?(?:\([sSuUbBiItTaA\-]+\))?[ ]?(?P<year>\d{4})?</div>[ ]<div class="genere">(?:[\w]+?\.?\s?[\s|S]?[\dx\-S]+?\s\(?(?P<lang>[iItTaA]+|[sSuUbBiItTaA\-]+)\)?\s?(?P<quality>[HD]+)?|.+?\(?(?P<lang2>[sSuUbBiItTaA\-]+)?\)?</div>)'
    else:
        #search
        patron = r'<div class="col-lg-3">[^>]+>[^>]+>\s<a href="(?P<url>[^"]+)".+?url\((?P<thumb>[^\)]+)\)">[^>]+>[^>]+>[^>]+>(?:[^>]+>)?\s?(?P<rating>[\d\.]+)?[^>]+>(?P<title>.+?)(?:[ ]\((?P<year>\d{4})\))?<[^>]+>[^>]+>(.?[\d\-x]+\s\(?(?P<lang>[sSuUbBiItTaA\-]+)?\)?\s?(?P<quality>[\w]+)?[|]?\s?(?:[fFiInNeE]+)?\s?\(?(?P<lang2>[sSuUbBiItTaA\-]+)?\)?)?'

    def itemHook(item):
        if item.lang2:
            if len(item.lang2)<3:
                item.lang2 = 'ITA'
            item.contentLanguage = item.lang2
            item.title += support.typo(item.lang2, '_ [] color kod')

        data = httptools.downloadpage(item.url, headers=headers).data
        block = scrapertoolsV2.find_single_match(data, r'Streaming\s?[\w]+?:(.*?)<\/div>')
        if re.findall('rel="category tag">serie', data, re.IGNORECASE):
            support.log('select = ### è una serie ###')
            item.action = 'episodios'
            item.contentType = 'tvshow'
##        elif re.findall('rel="category tag">sport', data, re.IGNORECASE):
##            support.log('select = ### è un documentario sportivo ###')
##            item.action = 'findvideos'
##            item.contentType = 'movie'
##        elif re.findall('rel="category tag">Wrestling WWE', data, re.IGNORECASE):
##            support.log('select = ### è una serie ###')
##            item.action = 'episodios'
##            item.contentType = 'tvshow'
        elif re.findall('rel="category tag">anime', data, re.IGNORECASE):
            if re.findall('episodio', block, re.IGNORECASE) or re.findall('episodi streaming', block, re.IGNORECASE) or \
               re.findall('numero stagioni', data, re.IGNORECASE):
                support.log('select = ### è un anime ###')
                item.action = 'episodios'
                item.contentType = 'tvshow'
                args='anime'
            else:
                support.log('select anime ELSE = ### è un film ###')
                contentType='movie'
                item.action = 'findvideos'
        else:
            support.log('select ELSE = ### è un film ###')
            item.action = 'findvideos'
            item.contentType='movie'

        return item

    patronNext = r'<a class="next page-numbers".*?href="([^"]+)">'

    return locals()

@support.scrape
def episodios(item):
    support.log()

    if item.args == 'anime':
        support.log("Anime :", item)
        blacklist = ['Clipwatching', 'Verystream', 'Easybytez', 'Flix555']
        patron = r'<a target=(?P<url>[^>]+>(?P<title>[^<]+))(?:</a></p>|</a><br />)'
        patronBlock = r'Streaming.+?:(?P<block>.*?)</div>'
        item.contentType = 'tvshow'
        item.contentSerieName = item.fulltitle
    else:# item.extra == 'serie':
        support.log("Serie :", item)
        patron = r'(?P<episode>\d+(?:&#215;|×)?\d+\-\d+|\d+(?:&#215;|×)\d+)[;]?[ ]?(?:(?P<title>[^<]+)(?P<url>.*?)|(\2[ ])(?:<(\3.*?)))(?:</a><br />|</a></p>)'
        patronBlock = r'<p><strong>(?P<block>(?:.+?[Ss]tagione.+?(?P<lang>iTA|ITA|Sub-ITA|Sub-iTA))?(?:|.+?|</strong>)(/?:</span>)?</p>.*?</p>)'
        item.contentType = 'tvshow'
        item.contentSerieName = item.fulltitle

    #debug = True
    return locals()

@support.scrape
def genres(item):
    support.log()

    action='peliculas'
    patron_block=r'<div id="bordobar" class="dropdown-menu(?P<block>.*?)</li>'
    patron=r'<a class="dropdown-item" href="(?P<url>[^"]+)" title="(?P<title>[A-z]+)"'

    return locals()


def search(item, texto):
    support.log(item.url,texto)
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
    support.log('newest ->', categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = host+'/category/film/'
            item.contentType = 'movie'
        elif categoria == 'series' or categoria == 'anime':
            item.args = 'update'
            item.url = host+'/aggiornamenti-serie-tv/'
        item.action = 'peliculas'
        itemlist = peliculas(item)

##        if itemlist[-1].action == 'peliculas':
##            itemlist.pop()
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.log('newest log: ', (line))
        return []

    return itemlist

def findvideos(item):
    support.log('findvideos ->', item)
    if item.contentType == 'movie':
        return support.server(item)
    else:
        return support.server(item, data= item.url)
