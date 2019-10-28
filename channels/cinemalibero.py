# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per 'cinemaLibero'
# ------------------------------------------------------------
"""
    Questi sono commenti per i beta-tester.

    Su questo canale in:
    - Cerca ( nel canale ) e Ricerca Globale
    - SerieTV e novità del canale
    - Novità -> SerieTV
    non saranno presenti le voci:
    - 'Aggiungi alla Videoteca',
    - 'Scarica Serie'
    - NON SONO PRESENTI IN NOVITà GLOBALE E del CANALE RIGUARDANTI LO SPORT!!!!
    dunque, la loro assenza, nel Test, NON dovrà essere segnalata come ERRORE.

    NON CONTROLLARE LA SEZIONE SPORT, HA PROBLEMI!!!
    è stata eliminata dall'elenco ma i titoli possono apparire nella ricerca o tra le novità
    Non è errore se dà problemi!!! NON CONSIDERATELA!

    Novità. Indicare in quale/i sezione/i è presente il canale:
       - FILM

    Avvisi:
        - Eventuali avvisi per i tester

    Ulteriori info:

"""

import re

from core import httptools, support, scrapertoolsV2
from core.item import Item
from platformcode import config

list_servers = ['akstream', 'wstream', 'backin', 'verystream', 'openload', 'streamango']
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

    Anime = [(support.typo('Anime', 'bullet bold'),['/category/anime-giapponesi/', 'peliculas', 'anime', 'tvshow'])
        ]

##    Sport = [(support.typo('Sport', 'bullet bold'), ['/category/sport/', 'peliculas', '', 'tvshow'])
##        ]
##    news = [('Novità Serie-Anime', ['/aggiornamenti-serie-tv/', 'peliculas', 'update', 'tvshow'])]
    search = ''

    return locals()


@support.scrape
#def video(item):
def peliculas(item):
    support.log()
    #debug = True

    patronBlock = r'<div class="container">.*?class="col-md-12[^"]*?">(?P<block>.*?)<div class=(?:"container"|"bg-dark ")>'
    if item.contentType == 'movie':
        patron = r'<div class="col-lg-3">[^>]+>[^>]+>\s<a href="(?P<url>[^"]+)".+?url\((?P<thumb>[^\)]+)\)">[^>]+>[^>]+>[^>]+>\s?(?P<rating>[\d\.]+)?[^>]+>[^>]+>(?P<title>.+?)\(?(?P<year>\d+)?\)?<[^>]+>[^>]+>(?P<quality>[^<]+)?<'
    elif item.args == 'anime':
        patron = r'<div class="col-lg-3">[^>]+>[^>]+>\s<a href="(?P<url>[^"]+)".+?url\((?P<thumb>[^\)]+)\)">[^>]+>[^>]+>[^>]+>\s?(?P<rating>[\d\.]+)?[^>]+>[^>]+>(?P<title>.+?)\(?(?P<year>\d+)?\)?<[^>]+>[^>]+>(?:.+?[^fFiInNeE]+?\(?(?P<lang>[sSuUbBiItTaA]+)\)?.+?)<'
    elif item.args == 'update':
        action = 'select'
        patron = r'<div class="card-body p-0">\s<a href="(?P<url>[^"]+)".+?url\((?P<thumb>.+?)\)">\s<div class="titolo">(?P<title>.+?)(?: &#8211; Serie TV)?(?:\([sSuUbBiItTaA\-]+\))?[ ]?(?P<year>\d{4})?</div>[ ]<div class="genere">(?:[\w]+?\.?\s?[\s|S]?[\dx\-S]+?\s\(?(?P<lang>[iItTaA]+|[sSuUbBiItTaA\-]+)\)?\s?(?P<quality>[HD]+)?|.+?\(?(?P<lang2>[sSuUbBiItTaA\-]+)?\)?</div>)'
    else:
        patron = r'<div class="col-lg-3">[^>]+>[^>]+>\s<a href="(?P<url>[^"]+)".+?url\((?P<thumb>[^\)]+)\)">[^>]+>[^>]+>[^>]+>(?:[^>]+>)?\s?(?P<rating>[\d\.]+)?[^>]+>(?P<title>[^<]+)<[^>]+>[^>]+>(.?[\d\-x]+\s\(?(?P<lang>[sSuUbBiItTaA\-]+)?\)?\s?(?P<quality>[\w]+)?[|]?\s?(?:[fFiInNeE]+)?\s?\(?(?P<lang2>[sSuUbBiItTaA\-]+)?\)?)?'

    def itemHook(item):
        if item.lang2:
            if len(item.lang2)<3:
                item.lang2 = 'ITA'
            item.contentLanguage = item.lang2
            item.title += support.typo(item.lang2, '_ [] color kod')

        if item.contentType == 'movie':
            item.action = 'findvideos'
        elif item.args == 'anime' or item.args == 'update' or item.args == 'search':
            item.action = 'select'
        elif item.contentType == 'tvshow':
            item.extra = 'serie'
            item.action = 'episodios'
        else:
            item.action = 'select'

        return item

    patronNext = r'<a class="next page-numbers".*?href="([^"]+)">'

    return locals()

@support.scrape
def episodios(item): # Questa def. deve sempre essere nominata episodios
    support.log()

    if item.extra == 'serie':
        support.log("Serie :", item)
        patron = r'(?P<episode>\d+(?:&#215;|×)?\d+\-\d+|\d+(?:&#215;|×)\d+)[;]?[ ]?(?:(?P<title>[^<]+)(?P<url>.*?)|(\2[ ])(?:<(\3.*?)))(?:</a><br />|</a></p>)'
        patronBlock = r'<p><strong>(?P<block>(?:.+?[Ss]tagione.+?(?P<lang>iTA|ITA|Sub-ITA|Sub-iTA))?(?:|.+?|</strong>)(/?:</span>)?</p>.*?</p>)'
        item.contentType = 'tvshow'
        item.contentSerieName = item.fulltitle
    elif item.args == 'anime':
        support.log("Anime :", item)
        blacklist = ['Clipwatching', 'Verystream', 'Easybytez', 'Flix555']
        #patron = r'(?:href="[ ]?(?P<url>[^"]+)"[^>]+>(?P<title>[^<]+))<|(?P<episode>\d+(?:&#215;|×)?\d+\-\d+|\d+(?:&#215;|×)\d+)[;]?(?:(\4[^<]+)(\2.*?)|(\2[ ])(?:<(\3.*?)))(?:</a><br />|</a></p>)'
        #patron = r'<a target=.+?href="(?P<url>[^"]+)"[^>]+>(?P<title>(Epis|).+?(?P<episode>\d+)?)(?:\((?P<lang>Sub ITA)\))?</a>(?:<br />)?'
        patron = r'<a target=(?P<url>.+?(?:rel="noopener noreferrer">(?P<title>[^<]+)))</a>.+?(?:</a></p>|</a><br />)'
        patronBlock = r'Streaming.+?:(?P<block>.*?)</div>'
        #patronBlock = r'(?:<p>)?(?P<block>.*?)(?:</a><br /> |</p><div)'
        item.contentType = 'tvshow'
        item.contentSerieName = item.fulltitle
    else:
        support.log('extra = else --- select = ### è un film ###')
        return findvideos(Item(channel=item.channel,
                               title=item.title,
                               fulltitle=item.fulltitle,
                               url=item.url,
                               show=item.fulltitle,
                               contentType='movie'))
    debug = True
    return locals()

@support.scrape
def genres(item):
    support.log()

    action='peliculas'
    patron_block=r'<div id="bordobar" class="dropdown-menu(?P<block>.*?)</li>'
    patron=r'<a class="dropdown-item" href="(?P<url>[^"]+)" title="(?P<title>[A-z]+)"'

    return locals()


def select(item):
    support.log()

    data = httptools.downloadpage(item.url, headers=headers).data
    block = scrapertoolsV2.find_single_match(data, r'Streaming\s?[\w]+?:(.*?)<\/div>')
    if re.findall('rel="category tag">serie', data, re.IGNORECASE):
        support.log('select = ### è una serie ###')
        return episodios(Item(channel=item.channel,
                              title=item.title,
                              fulltitle=item.fulltitle,
                              contentSerieName = fulltitle,
                              url=item.url,
                              extra='serie',
                              contentType='episode'))
    elif re.findall('rel="category tag">anime', data, re.IGNORECASE):
        if re.findall('episodio', block, re.IGNORECASE) or re.findall('episodi streaming', block, re.IGNORECASE) or \
           re.findall('numero stagioni', data, re.IGNORECASE):
            support.log('select = ### è un anime ###')
            return episodios(Item(channel=item.channel,
                                title=item.title,
                                fulltitle=item.fulltitle,
                                contentSerieName = item.fulltitle,
                                url=item.url,
                                args='anime',
                                contentType='episode'))
        else:
            support.log('select anime ELSE = ### è un film ###')
            return findvideos(Item(channel=item.channel,
                                    title=item.title,
                                    fulltitle=item.fulltitle,
                                    url=item.url,
                                    contentType='movie'))
    else:
        support.log('select ELSE = ### è un film ###')
        return findvideos(Item(channel=item.channel,
                              title=item.title,
                              fulltitle=item.fulltitle,
                              url=item.url,
                              contentType='movie'))

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
##            item.action = 'peliculas'
##            itemlist = peliculas(item)
##        elif categoria == 'series':
##            item.contentType = 'tvshow'
##            item.args = 'update'
##            item.url = host+'/aggiornamenti-serie-tv/'
        item.action = 'peliculas'
        itemlist = peliculas(item)

        if itemlist[-1].action == 'peliculas':
            itemlist.pop()
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.log('newest log: ', {0}.format(line))
        return []

    return itemlist

def findvideos(item):
    support.log('findvideos ->', item)
    if item.contentType == 'movie':
        return support.server(item)
    else:
        return support.server(item, data= item.url)
