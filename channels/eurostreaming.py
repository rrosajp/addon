# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Eurostreaming
# by Greko
# ------------------------------------------------------------
"""
    Problemi noti:
    Alcune sezioni di anime-cartoni non vanno, alcune hanno solo la lista degli episodi, ma non hanno link,
    altre cambiano la struttura
"""
import re
from core import scrapertoolsV2, httptools, support
from core.item import Item
from platformcode import logger, config

__channel__ = "eurostreaming"
host = config.get_channel_url(__channel__)
headers = [['Referer', host]]

list_servers = ['verystream', 'wstream', 'speedvideo', 'flashx', 'nowvideo', 'streamango', 'deltabit', 'openload']
list_quality = ['default']

IDIOMAS = {'Italiano': 'ITA', 'Sub-ITA':'vosi'}
list_language = IDIOMAS.values()

@support.menu
def mainlist(item):
    support.log()
    tvshow = [
        ('Archivio ', ['/category/serie-tv-archive/', 'peliculas', '', 'tvshow']),
        ('Aggiornamenti ', ['/aggiornamento-episodi/', 'peliculas', True, 'tvshow'])
        ]
    anime = ['/category/anime-cartoni-animati/']
    return locals()


@support.scrape
def peliculas(item):
    support.log()
    action = 'episodios'
    if item.args == True:
        patron = r'<span class="serieTitle" style="font-size:20px">(?P<title>.*?).[^–]<a href="(?P<url>[^"]+)"'\
                 '\s+target="_blank">(?P<episode>\d+x\d+) (?P<title2>.*?)</a>'
        # permette di vedere episodio e titolo + titolo2 in novità
        def itemHook(item):
            item.show = item.episode + item.title
            return item
    else:
        patron = r'<div class="post-thumb">.*?\s<img src="(?P<thumb>[^"]+)".*?>'\
                 '<a href="(?P<url>[^"]+)".*?>(?P<title>.*?(?:\((?P<year>\d{4})\)|(\4\d{4}))?)<\/a><\/h2>'

        patronNext='a class="next page-numbers" href="?([^>"]+)">Avanti &raquo;</a>'
    return locals()

@support.scrape
def episodios(item):
    support.log("episodios: %s" % item)
    action = 'findvideos'
    item.contentType = 'episode'
    # Carica la pagina
    data = httptools.downloadpage(item.url, headers=headers).data.replace("'", '"')
    #======== 
    if 'clicca qui per aprire' in data.lower():
        item.url = scrapertoolsV2.find_single_match(data, '"go_to":"([^"]+)"')
        item.url = item.url.replace("\\","")
        # Carica la pagina
        data = httptools.downloadpage(item.url, headers=headers).data.replace("'", '"')
    elif 'clicca qui</span>' in data.lower():
        item.url = scrapertoolsV2.find_single_match(data, '<h2 style="text-align: center;"><a href="([^"]+)">')
        # Carica la pagina        
        data = httptools.downloadpage(item.url, headers=headers).data.replace("'", '"')
    #=========
    data = re.sub('\n|\t', ' ', data)
    patronBlock = r'(?P<block>STAGIONE\s\d+ (?:\()?(?P<lang>ITA|SUB ITA)(?:\))?<\/div>.*?)</div></div>'
    patron = r'(?:\s|\Wn)?(?:|<strong>)?(?P<episode>\d+&#\d+;\d+)(?:|</strong>) (?P<title>.*?)(?:|–)?<a\s(?P<url>.*?)<\/a><br\s\/>'

    return locals()

# ===========  def findvideos  =============

def findvideos(item):
    support.log('findvideos', item)
    return support.server(item, item.url)

# ===========  def ricerca  =============
def search(item, texto):
    support.log()
    item.url = "%s/?s=%s" % (host, texto)
    item.contentType = 'tvshow'
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

# ===========  def novità in ricerca globale  =============
def newest(categoria):
    support.log()  
    itemlist = []
    item = Item()
    item.contentType = 'tvshow'
    item.args = True
    try:        
        item.url = "%s/aggiornamento-episodi/" % host
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
