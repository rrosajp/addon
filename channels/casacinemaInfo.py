# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per 'casacinemaInfo'
# ------------------------------------------------------------
"""

    Problemi noti che non superano il test del canale:
       - indicare i problemi

    Avvisi:
        - Sub-ita è nel titolo, lascia il puntatore sulla locandina
        per visualizzare il titolo completo!

    Ulteriori info:


"""
# CANCELLARE Ciò CHE NON SERVE per il canale, lascia il codice commentato
# ma fare PULIZIA quando si è finito di testarlo

# Qui gli import
#import re

# per l'uso dei decoratori, per i log, e funzioni per siti particolari
from core import support

# in caso di necessità
from core import scrapertoolsV2, httptools #, servertools, tmdb
from core.item import Item
#from lib import unshortenit

##### fine import

host = ""
headers = ""

def findhost():
    global host, headers
    data = httptools.downloadpage('https://casacinema.nuovo.link').data
    host = scrapertoolsV2.find_single_match(data, r'<div class="elementor-widget-container"><div class="elementor-button-wrapper"> <a href="([^"]+)"')
    headers = [['Referer', host]]
    if host.endswith('/'):
        host = host[:-1]
findhost()

# server di esempio...
list_servers = ['supervideo', 'streamcherry','rapidvideo', 'streamango', 'openload']
# quality di esempio
list_quality = ['default', 'HD', '3D', '4K', 'DVD', 'SD']

@support.menu
def mainlist(item):
    support.log(item)

    # Ordine delle voci
    # Voce FILM, puoi solo impostare l'url
    film = ['',
        #'url', # url per la voce FILM, se possibile la pagina principale con le ultime novità
        #Voce Menu,['url','action','args',contentType]
        ('Al Cinema', ['/category/in-sala/', 'peliculas', '']),
        ('Novità', ['/category/nuove-uscite/', 'peliculas', '']),
        ('Generi', ['', 'genres', 'genres']),
        ('Sub-ITA', ['/category/sub-ita/', 'peliculas', ''])
        ]

    return locals()


@support.scrape
def peliculas(item):
    support.log(item)
    #dbg # decommentare per attivare web_pdb

##    action = 'episodios'
    blacklist = ['']
    if item.args != 'search':
        patron = r'<div class="col-mt-5 postsh">[^<>]+<div class="poster-media-card">[^<>]+<a href="(?P<url>[^"]+)" title="(?P<title>.+?)[ ]?(?:\[(?P<lang>Sub-ITA)\])?".*?<img(?:.+?)?src="(?P<thumb>[^"]+)"'
        patronBlock = r'<div class="showpost4 posthome">(?P<block>.*?)</section>'
    else:
        patron = r'<li class="col-md-12 itemlist">.*?<a href="(?P<url>[^"]+)" title="(?P<title>[^"]+)".*?<img src="(?P<thumb>[^"]+)".*?Film dell"anno: (?P<year>\d{4})(?:[\d\-]+)?</p> <p class="text-list">(?P<plot>[^<>]+)</p>'
        patronBlock = r'<ul class="search-results-content infinite">(?P<block>.*?)</section>'
    patronNext = '<a href="([^"]+)"><i class="glyphicon glyphicon-chevron-right"'

    #debug = True  # True per testare le regex sul sito
    return locals()


@support.scrape
def genres(item):
    support.log(item)
    #dbg

    action = 'peliculas'
    blacklist = ['']
    patron = r'href="(?P<url>[^"]+)">(?P<title>[^<]+)<'
    patronBlock = r'</span>Generi</h3>(?P<block>.*?)<div class="clear"></div>'

    debug = False
    return locals()


def search(item, text):
    support.log('search', item)
    itemlist = []
    text = text.replace(' ', '+')
    item.args = 'search'
    item.url = host+'/?s=%s' % (text)
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
        if categoria == 'peliculas':
            item.url = host
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
    return support.hdpass_get_servers(item)
