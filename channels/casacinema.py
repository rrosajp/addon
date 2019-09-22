# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per 'idcanale nel json'
# ------------------------------------------------------------
# Rev: 0.2
# Update 18-09-2019
# fix:
# 1. aggiunto pagination e sistemate alcune voci

# Questo vuole solo essere uno scheletro per velocizzare la scrittura di un canale.
# I commenti sono più un promemoria... che una vera e propria spiegazione!
# Niente di più.
# Ulteriori informazioni sono reperibili nel wiki:
# https://github.com/kodiondemand/addon/wiki/decoratori
"""

    Problemi noti che non superano il test del canale:
       - indicare i problemi

    Avvisi:
        - NON è presente nella ricerca globale
        - TUTTE le pagine delle serie contengono al max 20 titoli

    Ulteriori info:

"""
# Qui gli import
# per l'uso dei decoratori, per i log, e funzioni per siti particolari
from core import support
from platformcode import config

# in caso di necessità
#from core import scrapertoolsV2#, httptools, servertools, tmdb
from core.item import Item # per newest
#from lib import unshortenit

##### fine import
__channel__ = "casacinema"
host = config.get_channel_url(__channel__)
headers = [['Referer', host]]

list_servers = ['verystream', 'openload', 'wstream', 'speedvideo']
list_quality = ['HD', 'SD']

@support.menu
def mainlist(item):
    support.log(item)

    film = ['/category/film',
        ('Generi', ['', 'genres', 'genres']),
        ('Sub-ITA', ['/category/sub-ita/', 'peliculas', 'sub'])
        ]

    # Voce SERIE, puoi solo impostare l'url
    tvshow = ['/aggiornamenti-serie-tv',
        ('Ultime', ['/category/serie-tv', 'peliculas', '']),
        ]
    return locals()

@support.scrape
def peliculas(item):
    support.log(item)
    #dbg # decommentare per attivare web_pdb

    if item.contentType == 'movie':
        action = 'findvideos'
    else:
        action = 'episodios'
        pagination = ''
    blacklist = ['']

    patron = r'<li><a href="(?P<url>[^"]+)"[^=]+="(?P<thumb>[^"]+)"><div> <div[^>]+>(?P<title>.*?)[ ]?(?:\[(?P<quality1>HD)\])?[ ]?(?:\(|\[)?(?P<lang>Sub-ITA)?(?:\)|\])?[ ]?(?:\[(?P<quality>.+?)\])?[ ]?(?:\((?P<year>\d+)\))?<(?:[^>]+>.+?(?:title="Nuovi episodi">(?P<episode>\d+x\d+)[ ]?(?P<lang2>Sub-Ita)?|title="IMDb">(?P<rating>[^<]+)))?'
    if item.args != 'search':
        patronBlock = r'<h1>.+?</h1>(?P<block>.*?)<aside>'
    else:
        patronBlock = r'<h1>Risultati per.+?</h1> <ul class="posts">(?P<block>.*?)<aside>'
    patronNext = '<a href="([^"]+)" >Pagina'

    def itemHook(item):
        if item.quality1:
            item.title = item.title + support.typo(item.quality1, '_ [] color kod')
        if item.lang2:
            item.contentLanguage = item.lang2
            item.title = item.title + support.typo(item.lang2, '_ [] color kod')

        return item

    #debug = True  # True per testare le regex sul sito
    return locals()

@support.scrape
def episodios(item):
    support.log(item)
    #dbg

    action = 'findvideos'
    blacklist = ['']
    patron = r'(?P<episode>\d+(?:&#215;|×)?\d+\-\d+|\d+(?:&#215;|×)\d+)[;]?(?:(?P<title>[^<]+)<(?P<url>.*?)|(\2[ ])(?:<(\3.*?)))(?:</a><br />|</a></p>)'
    patronBlock = r'<strong>(?P<block>(?:.+?Stagione*.+?(?P<lang>ITA|Sub-ITA))?(?:.+?|</strong>)(/?:</span>)?</p>.*?</p>)'

##    debug = True
    return locals()

# Questa def è utilizzata per generare i menu del canale
# per genere, per anno, per lettera, per qualità ecc ecc
@support.scrape
def genres(item):
    support.log(item)
    #dbg

    action = 'peliculas'
    blacklist = ['PRIME VISIONI', 'ULTIME SERIE TV']
    patron = r'<li><a href="(?P<url>[^"]+)">(?P<title>[^<>]+)</a></li>'
    patronBlock = r'<div class="container home-cats">(?P<block>.*?)<div class="clear">'

    #debug = True
    return locals()

############## Fondo Pagina

def search(item, text):
    support.log('search ->', item)
    itemlist = []
    text = text.replace(' ', '+')
    item.url = host + '/?s=' + text
    # bisogna inserire item.contentType per la ricerca globale
    # se il canale è solo film, si può omettere, altrimenti bisgona aggiungerlo e discriminare.
    item.contentType = item.contentType
    try:
        return peliculas(item)
    # Se captura la excepcion, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            log('search log:', line)
        return []

def newest(categoria):
    support.log('newest ->', categoria)
    itemlist = []
    item = Item()

    try:
        if categoria == 'series':
            item.contentType = 'tvshow'
            item.url = host+'/aggiornamenti-serie-tv'
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
            log('newest log: ', {0}.format(line))
        return []

    return itemlist


def findvideos(item):
    support.log('findvideos ->', item)
    if item.contentType != 'movie':
        return support.server(item, item.url)
    else:
        return support.server(item)
