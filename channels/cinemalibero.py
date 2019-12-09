# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per 'cinemaLibero'
# ------------------------------------------------------------
"""

    25 titoli per le novità

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

list_servers = ['akstream', 'wstream', 'backin', 'clipwatching', 'cloudvideo', 'verystream', 'onlystream', 'mixdrop']
list_quality = ['default']

__channel__ = "cinemalibero"
host = config.get_channel_url(__channel__)
headers = [['Referer', host]]

@support.menu
def mainlist(item):

    film = ['/category/film/',
            ('Novità', ['', 'peliculas', 'update']),
            ('Generi', ['', 'genres'])
        ]

    tvshow = ['/category/serie-tv/'
        ]

##    Anime = [(support.typo('Anime', 'bullet bold'),['/category/anime-giapponesi/', 'peliculas', 'anime', 'tvshow'])
##        ]

##    Sport = [(support.typo('Sport', 'bullet bold'), ['/category/sport/', 'peliculas', 'sport', 'tvshow'])
##        ]
    news = [('Ultimi episodi Serie/Anime', ['/aggiornamenti-serie-tv/', 'peliculas', 'update', 'tvshow'])]

    search = ''

    return locals()


@support.scrape
def peliculas(item):

    data = httptools.downloadpage(item.url, headers=headers).data
    data = re.sub('\n|\t', ' ', data)
    data = re.sub(r'>\s+<', '> <', data)
    GENERI = scrapertoolsV2.find_multiple_matches(data, r'<a class="dropdown-item" href="[^"]+" title="([A-z]+)"')

    patronBlock = r'<div class="container">.*?class="col-md-12[^"]*?">(?P<block>.*?)<div class=(?:"container"|"bg-dark ")>'
    if item.args == 'newest':
        patron = r'<div class="col-lg-3">[^>]+>[^>]+>\s<a href="(?P<url>[^"]+)".+?url\((?P<thumb>[^\)]+)\)">[^>]+>(?P<title>[^<]+)<[^>]+>[^>]+>(?:[^>]+>)?\s?(?P<rating>[\d\.]+)?[^>]+>.+?(?:[ ]\((?P<year>\d{4})\))?<[^>]+>[^>]+>(.?[\d\-x]+\s\(?(?P<lang>[sSuUbBiItTaA\-]+)?\)?\s?(?P<quality>[\w]+)?[|]?\s?(?:[fFiInNeE]+)?\s?\(?(?P<lang2>[sSuUbBiItTaA\-]+)?\)?)?'
        pagination = 25
    elif item.contentType == 'movie':
        patron = r'<a href="(?P<url>[^"]+)" title="(?P<title>.+?)(?:[ ]\[(?P<lang>[sSuUbB\-iItTaA]+)\])?(?:[ ]\((?P<year>\d{4})\))?"\salt="[^"]+"\sclass="[^"]+"(?: style="background-image: url\((?P<thumb>.+?)\)">)?<div class="voto">[^>]+>[^>]+>.(?P<rating>[\d\.a-zA-Z\/]+)?[^>]+>[^>]+>[^>]+>(?:<div class="genere">(?P<quality>[^<]+)</div>)?'
        if item.args == 'update':
            patronBlock = r'<section id="slider">(?P<block>.*?)</section>'
            patron = r'<a href="(?P<url>(?:https:\/\/.+?\/(?P<title>[^\/]+[a-zA-Z0-9\-]+)(?P<year>\d{4})))/".+?url\((?P<thumb>[^\)]+)\)">'
    elif item.contentType == 'tvshow':
        action = 'episodios'
        patron = r'<a href="(?P<url>[^"]+)".+?url\((?P<thumb>[^\)]+)\)">[^>]+>[^>]+>[^>]+>(?:[^>]+>)?\s?(?P<rating>[\d\.]+)?[^>]+>(?P<title>.+?)(?:[ ]\((?P<year>\d{4})\))?<[^>]+>[^>]+>(.?[\d\-x]+\s\(?(?P<lang>[sSuUbBiItTaA\-]+)?\)?\s?(?P<quality>[\w]+)?[|]?\s?(?:[fFiInNeE]+)?\s?\(?(?P<lang2>[sSuUbBiItTaA\-]+)?\)?)?'
        if item.args == 'anime':
            anime = True
            patron = r'<div class="col-lg-3">[^>]+>[^>]+>\s<a href="(?P<url>[^"]+)".+?url\((?P<thumb>[^\)]+)\)">[^>]+>[^>]+>[^>]+>\s?(?P<rating>[\d\.]+)?[^>]+>[^>]+>(?P<title>.+?)\(?(?P<year>\d+)?\)?<[^>]+>[^>]+>(?:.+?[^fFiInNeE]+?\(?(?P<lang>[sSuUbBiItTaA]+)\)?.+?)<'
        elif item.args == 'update':
            patron = r'<a href="(?P<url>[^"]+)".+?url\((?P<thumb>.+?)\)">\s<div class="titolo">(?P<title>.+?)(?: &#8211; Serie TV)?(?:\([sSuUbBiItTaA\-]+\))?[ ]?(?P<year>\d{4})?</div>[ ]<div class="genere">(?:[\w]+?\.?\s?[\s|S]?[\dx\-S]+?\s\(?(?P<lang>[iItTaA]+|[sSuUbBiItTaA\-]+)\)?\s?(?P<quality>[HD]+)?|.+?\(?(?P<lang2>[sSuUbBiItTaA\-]+)?\)?</div>)'
            pagination = 25
    else:
        #search
        patron = r'<div class="col-lg-3">[^>]+>[^>]+>\s<a href="(?P<url>[^"]+)".+?url\((?P<thumb>[^\)]+)\)">[^>]+>[^>]+>[^>]+>(?:[^>]+>)?\s?(?P<rating>[\d\.]+)?[^>]+>(?P<title>.+?)(?:[ ]\((?P<year>\d{4})\))?<[^>]+>[^>]+>(.?[\d\-x]+\s\(?(?P<lang>[sSuUbBiItTaA\-]+)?\)?\s?(?P<quality>[\w]+)?[|]?\s?(?:[fFiInNeE]+)?\s?\(?(?P<lang2>[sSuUbBiItTaA\-]+)?\)?)?'

    def itemHook(item):
        if item.lang2:
            if len(item.lang2)<3:
                item.lang2 = 'ITA'
            item.contentLanguage = item.lang2
            item.title += support.typo(item.lang2, '_ [] color kod')

        dataBlock = httptools.downloadpage(item.url, headers=headers).data
        genere = scrapertoolsV2.find_single_match(dataBlock, r'rel="category tag">([a-zA-Z0-9]+).+?<')

        if genere.lower() in str(GENERI).lower():
            item.contentType = 'movie'
            action = 'findvideos'
            if item.args == 'update':
                item.title = item.title.replace('-',' ')
        elif genere.lower() == 'serie':
            item.action = 'episodios'
            item.contentType = 'tvshow'
        elif genere.lower() == 'anime':
            blockAnime = scrapertoolsV2.find_single_match(dataBlock, r'<div id="container" class="container">(.+?)<div style="margin-left')
            if 'stagione'  in blockAnime.lower() or 'episodio' in blockAnime.lower() or 'saga' in blockAnime.lower():
                anime = True
                item.action = 'episodios'
                item.contentType = 'tvshow'
            else:
                item.contentType = 'movie'
                item.action = 'findvideos'
                item.url = scrapertoolsV2.find_single_match(blockAnime, r'<span class="txt_dow">(?:.+?)?Streaming:(?:.+?)?</span>(.*?)<div style="margin-left:')
        else:
            # Tutto il resto!!
            pass

        return item

    patronNext = r'<a class="next page-numbers".*?href="([^"]+)">'
    debug = True
    return locals()

@support.scrape
def episodios(item):

    if item.args == 'anime':
        support.log("Anime :", item)
        blacklist = ['Clipwatching', 'Verystream', 'Easybytez', 'Flix555', 'Cloudvideo']
        patron = r'(Stagione (?P<season>\d+))?.+?<a target=(?P<url>[^>]+>(?P<title>.+?(?P<episode>\d+)))(?:[:]?.+?)(?:</a></p>|</a><br />)'
        patronBlock = r'Stagione (?P<season>\d+)</span><br />(?P<block>.*?)(?:<div style="margin-left:|<span class="txt_dow">)'
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

    action='peliculas'
    patron_block=r'<div id="bordobar" class="dropdown-menu(?P<block>.*?)</li>'
    patron=r'<a class="dropdown-item" href="(?P<url>[^"]+)" title="(?P<title>[A-z]+)"'

    return locals()


def search(item, texto):
    support.log(item.url,texto)
    text = texto.replace(' ', '+')
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
    item.args = 'newest'
    try:
        if categoria == 'peliculas':
            item.url = host+'/category/film/'
            item.contentType = 'movie'
        elif categoria == 'series' or categoria == 'anime':
            item.args = 'update'
            item.url = host+'/aggiornamenti-serie-tv/'
            item.contentType = 'tvshow'
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
    if item.contentType == 'movie' and item.args != 'anime':
        return support.server(item)
    else:
        return support.server(item, data= item.url)
