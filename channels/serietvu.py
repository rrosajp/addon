# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per serietvu.py
# ----------------------------------------------------------

"""
    La pagina novità contiene al max 25 titoli
"""
import re

from core import support, httptools, scrapertoolsV2
from core.item import Item
from core.support import log
from platformcode import config

__channel__ = 'serietvu'
host = config.get_channel_url(__channel__)
headers = [['Referer', host]]

list_servers = ['speedvideo']
list_quality = ['default']


@support.menu
def mainlist(item):
    log()
    
    tvshow = ['/category/serie-tv',
              ('Aggiornamenti Serie', ['/ultimi-episodi/', 'peliculas', 'update']),
              ('Generi', ['', 'genres', 'genres'])
    ]

    return locals()


@support.scrape
def peliculas(item):
    log()

    patronBlock = r'<div class="wrap">\s+<h.>.*?</h.>(?P<block>.*?)<footer>'

        
    if item.args != 'update':
        action = 'episodios'     
        patron = r'<div class="item">\s*<a href="(?P<url>[^"]+)" data-original="(?P<thumb>[^"]+)" class="lazy inner">[^>]+>[^>]+>[^>]+>[^>]+>(?P<title>[^<]+)<'    
    else:
        action = 'findvideos'
        patron = r'<div class="item">\s+?<a href="(?P<url>[^"]+)"\s+?data-original="(?P<thumb>[^"]+)"[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<title>.+?)<[^>]+>\((?P<episode>[\dx\-]+)\s+?(?P<lang>Sub-Ita|[iITtAa]+)\)<'
        pagination = 25

    patronNext = r'<li><a href="([^"]+)"\s+?>Pagina successiva'

    #support.regexDbg(item, patron, headers)
    #debug = True
    return locals()

@support.scrape
def episodios(item):
    log()

    patronBlock = r'</select><div style="clear:both"></div></h2>(?P<block>.*?)<div id="trailer" class="tab">'
    patron = r'(?:<div class="list (?:active)?" data-id="(?P<season>\d+)">[^>]+>)?\s+<a data-id="(?P<episode>\d+)(?:[ ](?P<lang>[SuUbBiItTaA\-]+))?"(?P<url>[^>]+)>[^>]+>[^>]+>(?P<title>.+?)(?:\sSub-ITA)?<'
    
    #support.regexDbg(item, patronBlock, headers)
    #debug = True
    return locals()    


@support.scrape
def genres(item):
    log()

    blacklist = ["Home Page", "Calendario Aggiornamenti"]
    action = 'peliculas'
    patronBlock = r'<h2>Sfoglia</h2>\s*<ul>(?P<block>.*?)</ul>\s*</section>'
    patron = r'<li><a href="(?P<url>[^"]+)">(?P<title>[^<]+)</a></li>'
    #debug = True

    return locals()


def search(item, text):
    log(text)
    item.url = host + "/?s=" + text
    try:
        item.contentType = 'tvshow'
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            log("%s" % line)
        return []

def newest(categoria):
    log(categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "series":
            item.url = host + "/ultimi-episodi"
            item.action = "peliculas"
            item.contentType = 'tvshow'
            item.args = 'update'
            itemlist = peliculas(item)

    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            log("{0}".format(line))
        return []

    return itemlist


def findvideos(item):
    log()
    if item.args != 'update':
        return support.server(item, data=item.url)        
    else:
        itemlist = []
        item.infoLabels['mediatype'] = 'episode'

        data = httptools.downloadpage(item.url, headers=headers).data
        data = re.sub('\n|\t', ' ', data)
        data = re.sub(r'>\s+<', '> <', data)
##        support.log("DATA - HTML:\n", data)
        url_video = scrapertoolsV2.find_single_match(data, r'<div class="item"> <a data-id="[^"]+" data-href="([^"]+)" data-original="[^"]+"[^>]+> <div> <div class="title">Episodio \d+', -1)
        url_serie = scrapertoolsV2.find_single_match(data, r'<link rel="canonical" href="([^"]+)"\s?/>')
        goseries = support.typo("Vai alla Serie:", ' bold')
        series = support.typo(item.contentSerieName, ' bold color kod')

        itemlist = support.server(item, data=url_video)
        
        itemlist.append(
            Item(channel=item.channel,
                    title=goseries + series,
                    fulltitle=item.fulltitle,
                    show=item.show,
                    contentType='tvshow',
                    contentSerieName=item.contentSerieName,
                    url=url_serie,
                    action='episodios',
                    contentTitle=item.contentSerieName,
                    plot = goseries + series + "con tutte le puntate",
                    ))
    
    #support.regexDbg(item, patronBlock, headers)
    return itemlist        
