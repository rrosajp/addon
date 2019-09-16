# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per serietvonline
# ----------------------------------------------------------
"""

    Problemi noti che non superano il test del canale:
        - il solo film .45, nella lista titoli, ha come titolo nel canale '.'
        - la ricerca dei titoli potrebbe non essere uguale ( da sistemare le regex )
          indicate i titoli, con cui avete avuto problemi, e se sono film o serie.

    Avvisi:
        - Nelle pagine di liste avrete un elenco di 24 titoli per pagina,
          invece della singola del sito
        - Il Canale è incluso nella sola ricerca globale.

    Le pagine di liste sono lente a caricarsi in quanto scaricano anche le info...

"""

from core import support
from platformcode import logger, config

__channel__ = "serietvonline"
host = config.get_channel_url(__channel__)
headers = [['Referer', host]]

list_servers = ['akvideo', 'wstream', 'backin', 'vidtome', 'nowvideo']
list_quality = ['default']


@support.menu
def mainlist(item):
    support.log()

    film = ['/lista-film/',
            ('Ultimi Aggiunti', ['/ultimi-film-aggiunti/', 'peliculas', 'latest'])
        ]

    tvshow = ['',
            ('HD', ['/lista-serie-tv-in-altadefinizione/', 'peliculas', 'hd'])
        ]

    anime = ['/lista-cartoni-animati-e-anime/']

    documentari = [('Documentari', ['/lista-documentari/' , 'peliculas' , 'doc', 'tvshow'])]

    search = ''

    return locals()

@support.scrape
def peliculas(item):
    support.log()

    blacklist = ['DMCA', 'Contatti', 'Attenzione NON FARTI OSCURARE', 'Lista Ccartoni Animati e Anime']

    if item.action == 'search':

        patronBlock = r'>Lista Serie Tv</a></li></ul></div><div id="box_movies">'\
                      '(?P<block>.*?)<div id="paginador">'
        patron = r'<div class="movie"><div class="imagen"> <img src="(?P<thumb>[^"]+)" '\
                 'alt="(?:(?P<title>.+?)[ ]?(?:\d+)?)?" /> <a href="(?P<url>[^"]+)">'\
                 '.+?<h2>(?:.+?(?P<year>\d+)?)</h2>(?: <span class="year">'\
                 '(\d+)(?:–|â|-\d+)?</span>)?</div>'

        def itemHook(item):
            support.log("ITEMHOOK PRIMA: ", item)
            if 'film' in item.url:
                item.action = 'findvideos'
                item.contentType = 'movie'
                item.infoLabels['mediatype'] = 'movie'
            else:
                item.action = 'episodios'
                item.contentType = 'tvshow'
                item.infoLabels['mediatype'] = 'tvshow'
            support.log("ITEMHOOK DOPO: ", item)

            return item

    elif item.extra == 'tvshow' or item.contentType == 'tvshow':
        # SEZIONE Serie TV- Anime!
        action = 'episodios'

        if 'anime' in item.url:
            patronBlock = r'<h1>Lista Cartoni Animati e Anime</h1>(?P<block>.*?)<div class="footer_c">'
            patron = r'<a href="(?P<url>[^"]+)" title="(?P<title>[^"]+)">.+?</a>'

        else:
            if item.args == 'hd':
                patronBlock = r'<h1>Lista Serie Tv in AltaDefinizione</h1>(?P<block>.*?)'\
                              '<div class="footer_c">'
                patron = r'<a href="(?P<url>[^"]+)" title="(?P<title>[^"]+)">.+?</a>'

            elif item.args == 'doc':
                patronBlock = r'<h1>Lista Documentari</h1>(?P<block>.*?)<div class="footer_c">'
                patron = r'<a href="(?P<url>[^"]+)" title="(?P<title>[^"]+)">.+?</a>'

            else:
                patronBlock = r'<div id="box_movies">(?P<block>.*?)<div id="paginador">'
                patron = r'<div class="movie">[^>]+>.+?src="(?P<thumb>[^"]+)" alt="[^"]+"'\
                         '.+?href="(?P<url>[^"]+)">[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[ ]'\
                         '(?P<rating>\d+.\d+|\d+)<[^>]+>[^>]+><h2>(?P<title>[^"]+)</h2>[ ]?'\
                         '(?:<span class="year">(?P<year>\d+|\-\d+))?<'
    else:
        # SEZIONE FILM
        action = 'findvideos'
        pagination = 24

        if not item.args:
            patron = r'href="(?P<url>[^"]+)"[^>]+>(?P<title>.*?)[ ]?(?P<year>\d+)?'\
                     '(?: Streaming | MD iSTANCE )?<'
            patronBlock = r'Lista dei film disponibili in streaming e anche in download\.'\
                          '</p>(?P<block>.*?)<div class="footer_c">'

        elif item.args == 'latest':
            patronBlock = r'<h1>Ultimi film aggiunti</h1>(?P<block>.*?)<div class="footer_c">'
            patron = r'<tr><td><a href="(?P<url>[^"]+)"(?:|.+?)?>(?:&nbsp;&nbsp;)?[ ]?'\
                     '(?P<title>.*?)[ ]?(?:HD)?[ ]?(?P<year>\d+)?'\
                     '(?: | HD | Streaming | MD(?: iSTANCE)? )?</a>'

    patronNext = r'<div class="siguiente"><a href="([^"]+)" >'

##    debug = True
    return locals()

@support.scrape
def episodios(item):
    support.log()

    action = 'findvideos'
    patronBlock = r'<table>(?P<block>.*?)<\/table>'

    patron = r'<tr><td>(?:[^<]+)[ ](?:Parte)?(?P<episode>\d+x\d+|\d+)(?:|[ ]?'\
             '(?P<title2>.+?)?)<(?P<url>.*?)</td><tr>'

##    debug = True
    return locals()

def findvideos(item):
    support.log()
    if item.contentType == 'movie':
        return support.server(item, headers=headers)
    else:
        return support.server(item, item.url)


def search(item, texto):
    support.log("CERCA :" ,texto, item)
    item.url = "%s/?s=%s" % (host, texto)

    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
