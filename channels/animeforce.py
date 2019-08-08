# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per animeforce.org
# ------------------------------------------------------------
import re
import urllib
import urlparse

from core import httptools, scrapertoolsV2, servertools, tmdb
from core.item import Item
from platformcode import config, logger
from servers.decrypters import adfly
from core.support import log
from core import support

__channel__ = "animeforce"
host = config.get_channel_url(__channel__)

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['directo', 'openload']
list_quality = ['default']

checklinks = config.get_setting('checklinks', __channel__)
checklinks_number = config.get_setting('checklinks_number', __channel__)

headers = [['Referer', host]]


@support.menu
def mainlist(item):
    anime = ['/lista-anime/',
             ('In Corso',['/lista-anime-in-corso/']),
             ('Ultimi Episodi',['','peliculas','update']),
             ('Ultime Serie',['/category/anime/articoli-principali/','peliculas','last'])
            ]
    return locals()

    
def newest(categoria):
    log(categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "anime":
            item.url = host
            item.args = 'update'
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

@support.scrape
def search(item, texto):
    search = texto
    item.contentType = 'tvshow'
    patron = '<strong><a href="(?P<url>[^"]+)">(?P<title>.*?) [Ss][Uu][Bb]'
    action = 'episodios'    
    return locals()


@support.scrape
def peliculas(item):
    anime = True
    if item.args == 'update':
        patron = r'src="(?P<thumb>[^"]+)" class="attachment-grid-post[^"]+" alt="[^"]*" title="(?P<title>[^"]+").*?<h2><a href="(?P<url>[^"]+)"'
        def itemHook(item):
            delete = scrapertoolsV2.find_single_match(item.fulltitle, r'( Episodio.*)')
            number = scrapertoolsV2.find_single_match(item.title, r'Episodio (\d+)')
            item.title = support.typo(number + ' - ','bold') + item.title.replace(delete,'')
            item.fulltitle = item.show = item.fulltitle.replace(delete,'')    
            item.url = item.url.replace('-episodio-'+ number,'')
            item.number = number
            return item
        action = 'findvideos'

    elif item.args == 'last':
        patron = r'src="(?P<thumb>[^"]+)" class="attachment-grid-post[^"]+" alt="[^"]*" title="(?P<title>.*?)(?: Sub| sub| SUB|").*?<h2><a href="(?P<url>[^"]+)"'
        action = 'episodios'

    else:
        pagination = ''
        patron = '<strong><a href="(?P<url>[^"]+)">(?P<title>.*?) [Ss][Uu][Bb]'
        action = 'episodios'

    return locals()


@support.scrape
def episodios(item):
    anime = True
    patron = r'<td style[^>]+>\s*.*?(?:<span[^>]+)?<strong>(?P<title>[^<]+)<\/strong>.*?<td style[^>]+>\s*<a href="(?P<url>[^"]+)"[^>]+>'
    def itemHook(item):
        item.url = item.url.replace(host, '')
        return item
    action = 'findvideos'
    return locals()


def findvideos(item):
    log(item)

    itemlist = []
    
    if item.number:       
        item.url = support.match(item, r'<a href="([^"]+)"[^>]*>', patronBlock=r'Episodio %s(.*?)</tr>' % item.number)[0][0]   
    
    if 'http' not in item.url:
        if '//' in item.url[:2]:
            item.url = 'http:' + item.url
        elif host not in item.url:        
            item.url = host + item.url
    
    if 'adf.ly' in item.url:
        item.url = adfly.get_long_url(item.url)
    elif 'bit.ly' in item.url:
        item.url = httptools.downloadpage(item.url, only_headers=True, follow_redirects=False).headers.get("location")

    matches = support.match(item, r'button"><a href="([^"]+)"')[0]

    for video in matches:
        itemlist.append(
            Item(channel=item.channel,
                action="play",
                title='diretto',
                url=video,
                server='directo'))

    support.server(item, itemlist=itemlist)

    return itemlist