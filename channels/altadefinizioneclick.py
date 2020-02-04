# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per altadefinizioneclick
# ----------------------------------------------------------
"""

    Eccezioni che non superano il test del canale:
       - indicare le eccezioni

    Novità. Indicare in quale/i sezione/i è presente il canale:
       - film
    
    Avvisi:
        - Eventuali avvisi per i tester

    Ulteriori info:


"""
from core import support
from core.item import Item
from platformcode import config

# def findhost():
#     data = support.httptools.downloadpage('https://altadefinizione-nuovo.link/').data
#     host = support.scrapertools.find_single_match(data, '<div class="elementor-button-wrapper"> <a href="([^"]+)"')
#     return host

host = config.get_channel_url()
headers = [['Referer', host]]
list_servers = ['mixdrop', 'vidcloud', 'vidoza', 'supervideo', 'hdload', 'mystream']
list_quality = ['1080p', '720p', '360p']

@support.menu
def mainlist(item):
    support.log()
    film = ['',
        ('Novità', ['/nuove-uscite/', 'peliculas', 'news']),
        ('Al Cinema', ['/al-cinema/', 'peliculas', 'cinema']),
        ('Generi', ['', 'genres', 'genres']),
        ('Anni', ['', 'genres', 'years']),
        ('Qualità', ['', 'genres', 'quality']),
        ('Mi sento Fortunato',[ '', 'genres', 'lucky']),
        ('Sub-ITA', ['/sub-ita/', 'peliculas', 'sub'])
    ]
    return locals()

@support.scrape
def peliculas(item):
    support.log()

    patron = r'<div class="wrapperImage">[ ]?(?:<span class="hd">(?P<quality>[^<>]+))?.+?'\
             'href="(?P<url>[^"]+)".+?src="(?P<thumb>[^"]+)".+?<h2 class="titleFilm">[^>]+>'\
             '(?P<title>.+?)[ ]?(?:|\[(?P<lang>[^\]]+)\])?(?:\((?P<year>\d{4})\))?</a>.*?'\
             '(?:IMDB\:</strong>[ ](?P<rating>.+?)<|</h2> )'
    patronBlock = r'<h1 class="titleSection titleLastIns">.+?</h1>(?P<block>.*?)<div class="row ismobile">'

    if item.args == 'genres':
        patron = r'<div class="wrapperImage">[ ]?(?:<span class="hd">'\
                 '(?P<quality>[^<>]+))?.+?href="(?P<url>[^"]+)".+?src="(?P<thumb>[^"]+)"'\
                 '.+?<h2 class="titleFilm(?:Mobile)?">[^>]+>(?P<title>.+?)[ ]?'\
                 '(?:|\[(?P<lang>[^\]]+)\])?(?:\((?P<year>\d{4})\))?</a>.*?'\
                 '(IMDB\:[ ](?P<rating>.+?))<'
    elif item.args == 'search':
        patronBlock = r'<section id="lastUpdate">(?P<block>.*?)<div class="row ismobile">'
        patron = r'<a href="(?P<url>[^"]+)">\s*<div class="wrapperImage">(?:<span class="hd">(?P<quality>[^<]+)'\
                 '<\/span>)?<img[^s]+src="(?P<thumb>[^"]+)"[^>]+>[^>]+>[^>]+>(?P<title>[^<]+)<[^<]+>'\
                 '(?:.*?IMDB:\s(\2[^<]+)<\/div>)?'
    elif not item.args:
        patronBlock = r'ULTIMI INSERITI(?P<block>.*?)<div class="sliderLastUpdate ismobile ">'

    # nella pagina "CERCA", la voce "SUCCESSIVO" apre la maschera di inserimento dati
    patronNext = r'<a class="next page-numbers" href="([^"]+)">'

    #debug = True
    return locals()

@support.scrape
def genres(item):
    support.log('genres', item)
    #debug = True

    action = 'peliculas'
    patron = r'<li><a href="(?P<url>[^"]+)">(?P<title>[^<]+)<'

    if item.args == 'genres':
        patronBlock = r'<ul class="listSubCat" id="Film">(?P<block>.*)<ul class="listSubCat" id="Anno">'
    elif item.args == 'years':
        patronBlock = r'<ul class="listSubCat" id="Anno">(?P<block>.*)<ul class="listSubCat" id="Qualita">'
    elif item.args == 'quality':
        patronBlock = r'<ul class="listSubCat" id="Qualita">(?P<block>.*)</li> </ul> </div> </div> </div> <a'
    elif item.args == 'lucky': # sono i titoli random nella pagina
        patronBlock = r'<h3 class="titleSidebox dado">FILM RANDOM</h3>(?P<block>.*)</section>'
        patron = r'<li><a href="(?P<url>[^"]+)">(?P<title>[^<[]+)(?:\[(?P<lang>.+?)\])?<'
        action = 'findvideos'

    item.args = 'genres'

    return locals()

def search(item, texto):
    support.log("search ", texto)

    item.args = 'search'
    item.url = host + "/?s=" + texto
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

def newest(categoria):
    support.log(categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "peliculas":
            item.args = 'news'
            item.url = host + "/nuove-uscite/"
            item.action = "peliculas"
            itemlist = peliculas(item)

            if itemlist[-1].action == "peliculas":
                itemlist.pop()

    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist

def findvideos(item):
    support.log('findvideos', item)
    return support.hdpass_get_servers(item)
