# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per 'casacinema'
# ------------------------------------------------------------
"""

    Problemi noti che non superano il test del canale:
       - Nella ricerca globale non sono presenti le voci:
           - "Aggiungi in videoteca"
           - "Scarica film/serie"
        presenti però quando si entra nella pagina

    Avvisi:


    Novità:
        - Film, SerieTv

    Ulteriori info:

"""
import re
from core import support
from platformcode import config

# in caso di necessità
from core import scrapertoolsV2, httptools
from core.item import Item


##### fine import
__channel__ = "casacinema"
host = config.get_channel_url(__channel__)
headers = [['Referer', host]]

list_servers = ['verystream', 'openload', 'wstream', 'speedvideo']
list_quality = ['HD', 'SD']

@support.menu
def mainlist(item):
    support.log(item)
##    support.dbg()

    film = ['/category/film',
        ('Generi', ['', 'genres', 'genres']),
        ('Sub-ITA', ['/category/sub-ita/', 'peliculas', 'sub'])
        ]

    tvshow = ['/category/serie-tv',
        ('Novità', ['/aggiornamenti-serie-tv', 'peliculas', '']),
        ]

    search = ''

    return locals()

@support.scrape
def peliculas(item):
    support.log(item)
##    support.dbg() # decommentare per attivare web_pdb

    if item.contentType == 'movie':
        action = 'findvideos'
    elif item.contentType == 'tvshow':
        action = 'episodios'
        pagination = ''
    else:
        # è una ricerca
        action = 'select'
    blacklist = ['']

    patron = r'<li><a href="(?P<url>[^"]+)"[^=]+="(?P<thumb>[^"]+)"><div> <div[^>]+>(?P<title>.*?)[ ]?(?:\[(?P<quality1>HD)\])?[ ]?(?:\(|\[)?(?P<lang>Sub-ITA)?(?:\)|\])?[ ]?(?:\[(?P<quality>.+?)\])?[ ]?(?:\((?P<year>\d+)\))?<(?:[^>]+>.+?(?:title="Nuovi episodi">(?P<episode>\d+x\d+)[ ]?(?P<lang2>Sub-Ita)?|title="IMDb">(?P<rating>[^<]+)))?'
    patronBlock = r'<h1>.+?</h1>(?P<block>.*?)<aside>'
    patronNext = '<a href="([^"]+)" >Pagina'

    def itemHook(item):
        if item.quality1:
            item.quality = item.quality1
            item.title += support.typo(item.quality, '_ [] color kod')
        if item.lang2:
            item.contentLanguage = item.lang2
            item.title += support.typo(item.lang2, '_ [] color kod')
        if item.args == 'novita':
            item.title = item.title
        return item

##    debug = True  # True per testare le regex sul sito
    return locals()

@support.scrape
def episodios(item):
    support.log(item)
    #dbg
    if item.data1:
        data = item.data1
    action = 'findvideos'
    item.contentType = 'tvshow'
    blacklist = ['']
    patron = r'(?P<episode>\d+(?:&#215;|×)?\d+\-\d+|\d+(?:&#215;|×)\d+)[;]?(?:(?P<title>[^<]+)<(?P<url>.*?)|(\2[ ])(?:<(\3.*?)))(?:<br />|</p>)'
    patronBlock = r'<strong>(?P<block>(?:.+?Stagione*.+?(?P<lang>[Ii][Tt][Aa]|[Ss][Uu][Bb][\-]?[iI][tT][aA]))?(?:.+?|</strong>)(/?:</span>)?</p>.*?</p>)'

##    debug = True
    return locals()

# Questa def è utilizzata per generare il menu 'Generi' del canale
# per genere, per anno, per lettera, per qualità ecc ecc
@support.scrape
def genres(item):
    support.log(item)
    #dbg

    action = 'peliculas'
    blacklist = ['PRIME VISIONI', 'ULTIME SERIE TV', 'ULTIMI FILM']
    patron = r'<li><a href="(?P<url>[^"]+)">(?P<title>[^<>]+)</a></li>'
    patronBlock = r'<div class="container home-cats">(?P<block>.*?)<div class="clear">'

    #debug = True
    return locals()

def select(item):
    support.log('select --->', item)
##    debug = True
    #support.dbg()
    data = httptools.downloadpage(item.url, headers=headers).data
    data = re.sub('\n|\t', ' ', data)
    data = re.sub(r'>\s+<', '> <', data)
    if 'continua con il video' in data.lower():
##    block = scrapertoolsV2.find_single_match(data, r'<div class="col-md-8 bg-white rounded-left p-5"><div>(.*?)<div style="margin-left: 0.5%; color: #FFF;">')
##    if re.findall('rel="category tag">serie', data, re.IGNORECASE):
        support.log('select = ### è un film ###')
        return findvideos(Item(channel=item.channel,
                              title=item.title,
                              fulltitle=item.fulltitle,
                              url=item.url,
                              #args='serie',
                              contentType='movie',
                              data1 = data
                              ))
    else:
        support.log('select = ### è una serie ###')
        return episodios(Item(channel=item.channel,
                              title=item.title,
                              fulltitle=item.fulltitle,
                              url=item.url,
                              #args='serie',
                              contentType='tvshow',
                              data1 = data
                              ))

############## Fondo Pagina

def search(item, text):
    support.log('search ->', item)
    itemlist = []
    text = text.replace(' ', '+')
    item.url = host + '/?s=' + text
    item.args = 'search'
    try:
        item.contentType = 'episode' # non fa uscire le voci nel context menu
        return peliculas(item)
    # Se captura la excepcion, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            support.log('search log:', line)
        return []

def newest(categoria):
    support.log('newest ->', categoria)
    itemlist = []
    item = Item()

    try:
        if categoria == 'series':
            item.contentType = 'tvshow'
            item.url = host+'/aggiornamenti-serie-tv'
            item.args = 'novita'
        else:
            item.contentType = 'movie'
            item.url = host+'/category/film'

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
    itemlist = []
    if item.contentType != 'movie':
        return support.server(item, item.url)
    else:
        block = r'<div class="col-md-10">(.+?)<div class="swappable" id="links">'
        patron = r'SRC="([^"]+)"'
        links = re.findall(patron, block, re.IGNORECASE)
        if "#" in links:
            links = link.replace('#', 'speedvideo.net')
            return support.server(item, links)
        else:
            return support.server(item)
