# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Guardaserie.click
# ------------------------------------------------------------

"""
    Problemi noti che non superano il test del canale:
        NESSUNO (update 13-9-2019)

    Avvisi per il test:
        La voce "Serie TV" mostra per ogni pagina 24 titoli


    Problemi noti:
    - nella pagina categorie appaiono i risultati di tmdb in alcune voci

"""

from core import scrapertoolsV2, httptools, support
from core.item import Item
from platformcode import logger, config
from core.support import log

__channel__ = 'guardaserieclick'
host = config.get_channel_url(__channel__)
headers = [['Referer', host]]

list_servers = ['speedvideo', 'openload']
list_quality = ['default']

@support.menu
def mainlist(item):
    tvshow = ['/lista-serie-tv',
        ('Ultimi Aggiornamenti', ['/lista-serie-tv', 'peliculas', 'new']),
        ('Categorie', ['categorie', 'categorie']),
        ('Serie inedite Sub-ITA', ['/lista-serie-tv', 'peliculas', 'ined']),
        ('Da non perdere', ['/lista-serie-tv', 'peliculas', ['tv', 'da non perdere']]),
        ('Classiche', ["/lista-serie-tv", 'peliculas', ['tv', 'classiche']]),
        ('Anime', ["/category/animazione/", 'tvserie', 'tvshow','anime'])
    ]

    return locals()


@support.scrape
def peliculas(item):
##    import web_pdb; web_pdb.set_trace()
    log('serietv ->\n', item)

    if item.args == 'ined':
        #data = httptools.downloadpage(item.url).data
        log("Sono qui orco")
        pagination = 24
        action = 'episodios'

        patron_block = r'<span\s+class="label label-default label-title-typology">'\
                       '(?P<lang>[^<]+)</span>'
    else:
        pagination = 24
        action = 'episodios'
        patronBlock = r'<div\s+class="container container-title-serie-new container-scheda" '\
                      'meta-slug="new">(?P<block>.*?)<div\s+class='\
                      '"btn btn-lg btn-default btn-load-other-series">'

    patron = r'<a href="(?P<url>[^"]+)".*?>\s<img\s.*?src="(?P<thumb>[^"]+)"\s/>'\
             '[^>]+>[^>]+>\s[^>]+>\s(?P<year>\d{4})?\s.+?class="strongText">(?P<title>.+?)<'


    debug = True
    return locals()

@support.scrape
def tvserie(item):

    action = 'episodios'
##    listGroups = ['url', 'thumb', 'title']
    patron = r'<a\shref="(?P<url>[^"]+)".*?>\s<img\s.*?src="(?P<thumb>[^"]+)" />'\
             '[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<title>[^<]+)</p></div>'
    patron_block = r'<div\sclass="col-xs-\d+ col-sm-\d+-\d+">(?P<block>.*?)'\
                   '<div\sclass="container-fluid whitebg" style="">'
    patronNext = r'<link\s.*?rel="next"\shref="([^"]+)"'

    return locals()

@support.scrape
def episodios(item):
    log('episodios ->\n')
    item.contentType = 'episode'

    action = 'findvideos'
##    listGroups = ['episode', 'lang', 'title2', 'plot', 'title', 'url']
    patron = r'class="number-episodes-on-img"> (?P<episode>\d+.\d+)'\
             '(?:|[ ]\((?P<lang>.*?)\))<[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>'\
             '(?P<title2>.*?)<[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>'\
             '(?P<plot>.*?)<[^>]+></div></div>.<span\s.+?meta-serie="(?P<title>.*?)"'\
             'meta-stag=(?P<url>.*?)</span>'

    return locals()


def findvideos(item):
    log()
    return support.server(item, item.url)

@support.scrape
def categorie(item):
    action = 'tvserie'
    #listGroups = ['url', 'title']
    patron = r'<li>\s<a\shref="(?P<url>[^"]+)"[^>]+>(?P<title>[^<]+)</a></li>'
    patron_block = r'<ul\sclass="dropdown-menu category">(?P<block>.*?)</ul>'

    return locals()

# ================================================================================================================

def newest(categoria):
    log()
    itemlist = []
    item = Item()
    item.contentType= 'episode'
    item.args = 'update'
    try:
        if categoria == "series":
            item.url = "%s/lista-serie-tv" % host
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

### ================================================================================================================
### ----------------------------------------------------------------------------------------------------------------

def search(item, texto):
    log(texto)
    item.url = host + "/?s=" + texto
    item.args = 'cerca'
    try:
        return tvserie(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
