# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per cinemalibero
# ------------------------------------------------------------
"""

    Il canale non permette di filtrare film, serie e altro nella ricerca.
    Quindi vengono disabilitate le voci:
            - "Aggiungi in videoteca"
            - "Scarica film/serie"
        per le solo ricerce: nel canale e globale.

    Problemi noti che non superano il test del canale:
       -
       
    Avvisi:
       -

    Ulteriori info:


"""

import re

# per l'uso dei decoratori, per i log, e funzioni per siti particolari
from core import support
# se non si fa uso di findhost()
from platformcode import config

# in caso di necessità
from core import scrapertoolsV2, httptools#, servertools
from core.item import Item # per newest
#from lib import unshortenit

__channel__ = "cinemalibero"
host = config.get_channel_url(__channel__)
headers = [['Referer', host]]
##headers = [
##    ['Host', host.split("//")[-1].split("/")[0]],
##    ['User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0'],
##    ['Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'],
##    ['Accept-Language', 'en-US,en;q=0.5'],
##    ['Accept-Encoding', 'gzip, deflate'],
##    ['Referer', host],
##    ['DNT', '1'],
##    ['Connection', 'keep-alive'],
##    ['Upgrade-Insecure-Requests', '1'],
##    ['Cache-Control', 'max-age=0']
##    ]

list_servers = ['akstream', 'wstream', 'openload', 'streamango']
list_quality = ['default']

@support.menu
def mainlist(item):
    support.log(item)

    film = ['/category/film/',
        ('Generi', ['', 'genres', 'genres']),
        ]

    tvshow = ['/category/serie-tv/',
##        ('Novità', ['/aggiornamenti-serie-tv/', 'peliculas', 'update']),
        ]

    anime = ['/category/anime-giapponesi/',
             ]

    search = ''

    return locals()

@support.scrape
def peliculas(item):
    support.log(item)
    #support.dbg() # decommentare per attivare web_pdb
    debug = True
    blacklist = ['']

    if item.args == 'search':
        patron = r'href="(?P<url>[^"]+)".+?url\((?P<thumb>[^\)]+)\)">.+?class="titolo">(?P<title>[^<]+)<'
        patronBlock = r'style="color: #2C3549 !important;" class="fon my-3"><small>.+?</small></h1>(?P<block>.*?)<div class="bg-dark ">'
        action = 'select'
    else:
        if item.contentType == 'tvshow':
            # da sistemare per matchare le ultime serie inserite
            if item.args == 'update':
                patron = r'<div class="card-body p-0"> <a href="(?P<url>[^"]+)".+?url\((?P<thumb>[^)]+)\)">[^>]+>(?P<title>.+?)(?:[ ]\((?P<lang>SubITA)\))?(?:[ ](?P<year>\d{4}))?</div> <div class="genere">(?:|Ep.)(?:|.+?)?</div>'
                action = 'select'
            else:
##                #patron = r'href="(?P<url>[^"]+)".+?url\((?P<thumb>.+?)\)">[^>]+>[^>]+>[^>]+>(?:[ ](?P<rating>\d+.\d+))?[^>]+>[^>]+>(?P<title>.+?)<[^>]+>[^>]+>(?:.+?) (?:\()?(?P<lang>ITA|iTA|Sub)(?:\))?'
##                #patron = r'<div class="card-body p-0"> <a href="(?P<url>[^"]+)".+?url\((?P<thumb>.+?)\)">[^>]+>[^>]+>[^>]+>(?:[ ](?P<rating>\d+.\d+))?[^>]+>[^>]+>(?P<title>.+?)(?: \(.+?\))?(?: \(\d+\)| \d+)?<[^>]+>(?:<div class="genere">.+?(?:\()?(?P<lang>ITA|iTA|Sub)(?:\))?)?'
                patron = r'<div class="card-body p-0"> <a href="(?P<url>[^"]+)".+?url\((?P<thumb>.+?)\)">[^>]+>[^>]+>[^>]+>(?:[ ](?P<rating>\d+.\d+))?[^>]+>[^>]+>(?P<title>.+?)(?: \(.+?\))?(?: \(\d+\)| \d+)?</div><div class="genere">(?:.?(?P<episode>\d+x\d+-\d+|\d+-\d+|\d+x\d+|\d+)[ ]?(?:\()?(?:(?P<lang>ITA|iTA|Sub ITA|Sub iTA|Sub))?[ ]?(?:(?P<quality>HD))?.+?)</div>'
                action = 'episodios'
            if 'anime' in item.url:
                patron = r'<div class="card-body p-0"> <a href="(?P<url>[^"]+)".+?url\((?P<thumb>.+?)\)">[^>]+>[^>]+>[^>]+>(?:[ ](?P<rating>\d+.\d+))?[^>]+>[^>]+>(?P<title>.+?)(?: \(.+?\))?(?: \(\d+\)| \d+)?<[^>]+>(?:<div class="genere">.+?(?:\()?(?P<lang>ITA|iTA|Sub)(?:\))?)?'
                action = 'select'
        elif item.contentType == 'movie':
            action = 'findvideos'
            patron = r'href="(?P<url>[^"]+)".+?url\((?P<thumb>.+?)\)">[^>]+>[^>]+>[^>]+>(?:[ ](?P<rating>\d+.\d+))?[^>]+>[^>]+>(?P<title>.+?)(?:\[(?P<lang>Sub-iTA|Sub-ITA|Sub)\])?[ ]\((?P<year>\d+)\)</div>(?:<div class="genere">(?P<quality>[^<]+)<)?'

        patronBlock = r'<h1(?: style="color: #2C3549 !important; text-transform: uppercase;"| style="text-transform: uppercase; color: #2C3549 !important;"| style="color: #2C3549 !important; text-transform: uppercase;" style="text-shadow: 1px 1px 1px #FF8C00; color:#FF8C00;"| style="text-shadow: 1px 1px 1px #0f0f0f;" class="darkorange"| style="color:#2C3549 !important;")>.+?</h1>(?P<block>.*?)<div class=(?:"container"|"bg-dark ")>'

    patronNext = '<a class="next page-numbers".*?href="([^"]+)">'

    return locals()


@support.scrape
def episodios(item):
    support.log(item)

    #dbg
##    if item.args == '':
##        patron = r'<a target=.+?href="(?P<url>[^"]+)"[^>]+>(?P<title>Epis.+?(\d+)?)(?:\((?P<lang>Sub ITA)\))?</a><br />'
##        patronBlock = r'(?:class="txt_dow">Streaming:(?P<block>.*?)at-below-post)'
    if item.data1 and 'stagione' not in item.data1.lower():
        # è un movie
        item.contentType = 'tvshow'
        #patron = r'(?:href="[ ]?(?P<url>[^"]+)"[^>]+>(?P<title>[^<]+)<|(?P<episode>\d+(?:&#215;|×)?\d+\-\d+|\d+(?:&#215;|×)\d+)[;]?(?:(\4[^<]+)(\2.*?)|(\2[ ])(?:<(\3.*?)))(?:</a><br />|</a></p>))'
        patron = r'<a target=.+?href="(?P<url>[^"]+)"[^>]+>(?P<title>Epis.+?(?P<episode>\d+)?)(?:\((?P<lang>Sub ITA)\))?</a>(?:<br />)?'
        patronBlock = r'(?:class="txt_dow">Streaming:(?P<block>.*?)at-below-post)'
    else:
        patron = r'(?P<episode>\d+(?:&#215;|×)?\d+\-\d+|\d+(?:&#215;|×)\d+)[;]?[ ]?(?:(?P<title>[^<]+)(?P<url>.*?)|(\2[ ])(?:<(\3.*?)))(?:</a><br />|</a></p>)'
##        patron = r'<a target=.+?href="(?P<url>[^"]+)"[^>]+>(?P<title>Epis.+?(\d+)?)(?:\((?P<lang>Sub ITA)\))?</a><br />'
        patronBlock = r'<p><strong>(?P<block>(?:.+?[Ss]tagione.+?(?P<lang>iTA|ITA|Sub-ITA|Sub-iTA))?(?:|.+?|</strong>)(/?:</span>)?</p>.*?</p>)'
        item.contentType = 'tvshow'

    action = 'findvideos'
    blacklist = ['']

##    pagination = ''

##    debug = True
    return locals()


@support.scrape
def genres(item):
    support.log(item)
    #dbg

    action = 'peliculas'
    blacklist = ['']
    patron = r'<a class="dropdown-item" href="(?P<url>[^"]+)" title="(?P<title>[A-z]+)"'

    return locals()


def select(item):
    support.log('select --->', item)
    #support.dbg()
    data = httptools.downloadpage(item.url, headers=headers).data
    block = scrapertoolsV2.find_single_match(data, r'<div class="col-md-8 bg-white rounded-left p-5"><div>(.*?)<div style="margin-left: 0.5%; color: #FFF;">')
    if re.findall('rel="category tag">serie', data, re.IGNORECASE):
        support.log('select = ### è una serie ###')
        return episodios(Item(channel=item.channel,
                              title=item.title,
                              fulltitle=item.fulltitle,
                              url=item.url,
                              args='serie',
                              contentType='tvshow',
                              data1 = data
                              ))
    elif re.findall('rel="category tag">anime', data, re.IGNORECASE):
        if re.findall('episodio', block, re.IGNORECASE) or re.findall('stagione', data, re.IGNORECASE):
            support.log('select = ### è un anime ###')
            return episodios(Item(channel=item.channel,
                                title=item.title,
                                fulltitle=item.fulltitle,
                                url=item.url,
                                args='anime',
                                contentType='tvshow',
                                data1 = data
                                  ))
        else:
            support.log('select = ### è un film ###')
            return findvideos(Item(channel=item.channel,
                                    title=item.title,
                                    fulltitle=item.fulltitle,
                                    url=item.url,
                                    args = '',
                                    contentType='movie',
                                    #data = data
                                   ))
    else:
        support.log('select = ### è un film ###')
        return findvideos(Item(channel=item.channel,
                              title=item.title,
                              fulltitle=item.fulltitle,
                              url=item.url,
                              contentType='movie',
                              #data = data
                               ))

def search(item, texto):
    support.log("[cinemalibero.py] " + item.url + " search " + texto)
    item.url = host + "/?s=" + texto
    try:
        item.args = 'search'
        item.contentType = 'episode' # non fa uscire le voci nel context menu
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
            item.args = 'update'
            item.url = host+'/aggiornamenti-serie-tv/'
            item.contentType = 'tvshow'
            item.action = 'peliculas'
            itemlist = peliculas(item)

            if itemlist[-1].action == 'peliculas':
                itemlist.pop()
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            log('newest log: ', {0}.format(line))
        return []

    return itemlist


def findvideos(item):
    support.log(item)
    if item.contentType == 'movie':
        return support.server(item)
    else:
        return support.server(item, data= item.url)
