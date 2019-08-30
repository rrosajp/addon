# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per animeworld
# ----------------------------------------------------------
import re
import time
import urllib
import urlparse

from core import httptools, scrapertoolsV2, servertools, tmdb, support, jsontools
from core.support import log
from core.item import Item
from platformcode import logger, config
from specials import autoplay, autorenumber

__channel__ = "animeworld"
host = config.get_channel_url(__channel__)
headers = [['Referer', host]]

IDIOMAS = {'Italiano': 'Italiano'}
list_language = IDIOMAS.values()
list_servers = ['animeworld', 'verystream', 'streamango', 'openload', 'directo']
list_quality = ['default', '480p', '720p', '1080p']


@support.menu
def mainlist(item):
    anime=['/filter',
           ('ITA',['/filter?language%5B%5D=1&sort=2', 'build_menu', 'language[]=1']),
           ('SUB-ITA',['/filter?language%5B%5D=1&sort=2', 'build_menu', 'language[]=0']),
           ('In Corso', ['/ongoing', 'peliculas']),
           ('Ultimi Episodi', ['/updated', 'peliculas', 'updated']),
           ('Nuove Aggiunte',['/newest', 'peliculas' ]),
           ('Generi',['','genres', '</i> Generi</a>'])]
    return locals()

# Crea menu  ===================================================

@support.scrape
def genres(item):
    patronBlock = r'</i> Generi</a>(?P<block>.*?)</ul>'
    patronMenu = r'<a href="(?P<url>[^"]+)"\stitle="(?P<title>[^"]+)">'
    action = 'peliculas'
    return locals()

def build_menu(item):
    log()
    itemlist = []
    support.menuItem(itemlist, __channel__, 'Tutti bold', 'peliculas', item.url, 'tvshow' , args=item.args)
    matches = support.match(item,r'<button class="btn btn-sm btn-default dropdown-toggle" data-toggle="dropdown"> (.*?) <span.[^>]+>(.*?)</ul>',r'<form class="filters.*?>(.*?)</form>')[0]
    for title, html in matches:
        if title not in 'Lingua Ordine':
            support.menuItem(itemlist, __channel__, title + ' submenu bold', 'build_sub_menu', html, 'tvshow', args=item.args)
    return itemlist

def build_sub_menu(item):
    log()
    itemlist = []
    matches = support.re.compile(r'<input.*?name="([^"]+)" value="([^"]+)"\s*>[^>]+>([^<]+)<\/label>', re.DOTALL).findall(item.url)
    for name, value, title in matches:
        support.menuItem(itemlist, __channel__, support.typo(title, 'bold'), 'peliculas', host + '/filter?&' + name + '=' + value + '&' + item.args + '&sort=2', 'tvshow', args='sub')
    return itemlist

# Novità ======================================================

def newest(categoria):
    log()
    itemlist = []
    item = Item()
    try:
        if categoria == "anime":
            item.url = host + '/updated'
            item.args = "updated"
            return peliculas(item)
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


# Cerca ===========================================================

def search(item, texto):
    log(texto)
    item.url = host + '/search?keyword=' + texto
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

# Scrapers ========================================================

@support.scrape
def peliculas(item):
    anime=True
    if item.args == 'updated':
        patron=r'<div class="inner">\s*<a href="(?P<url>[^"]+)" class[^>]+>\s*<img src="(?P<thumb>[^"]+)" alt?="(?P<title>[^\("]+)(?:\((?P<lang>[^\)]+)\))?"[^>]+>[^>]+>\s*(?:<div class="[^"]+">(?P<type>[^<]+)</div>)?[^>]+>[^>]+>\s*<div class="ep">[^\d]+(?P<episode>\d+)[^<]*</div>'
        action='findvideos'
    else:
        patron= r'<div class="inner">\s*<a href="(?P<url>[^"]+)" class[^>]+>\s*<img src="(?P<thumb>[^"]+)" alt?="(?P<title>[^\("]+)(?:\((?P<lang>[^\)]+)\))?"[^>]+>[^>]+>[^>]+>[^>]+>\s*(?:<div class="[^"]+">(?P<type>[^<]+)</div>)?'
        action='episodios'
    
    patronNext=r'href="([^"]+)" rel="next"'
    type_content_dict={'movie':['movie']}
    type_action_dict={'findvideos':['movie']}    
    return locals()


@support.scrape
def episodios(item):
    anime=True
    patronBlock= r'server  active(?P<block>.*?)server  hidden ' 
    patron = r'<li><a [^=]+="[^"]+"[^=]+="[^"]+"[^=]+="[^"]+"[^=]+="[^"]+"[^=]+="[^"]+" href="(?P<url>[^"]+)"[^>]+>(?P<episode>[^<]+)<'
    def itemHook(item):
        log('FULLTITLE= ',item)
        item.title += support.typo(item.fulltitle,'-- bold')
        return item
    action='findvideos'
    return locals()


def findvideos(item):
    log(item)
    itemlist = []    
    matches, data = support.match(item, r'class="tab.*?data-name="([0-9]+)">', headers=headers)
    videoData = ''
    
    for serverid in matches:
        number = scrapertoolsV2.find_single_match(item.title,r'(\d+) -')
        block = scrapertoolsV2.find_multiple_matches(data,'data-id="' + serverid + '">(.*?)<div class="server')
        ID = scrapertoolsV2.find_single_match(str(block),r'<a data-id="([^"]+)" data-base="' + (number if number else '1') + '"')
        log('ID= ',ID)
        if id:
            dataJson = httptools.downloadpage('%s/ajax/episode/info?id=%s&server=%s&ts=%s' % (host, ID, serverid, int(time.time())), headers=[['x-requested-with', 'XMLHttpRequest']]).data
            json = jsontools.load(dataJson)
            videoData +='\n'+json['grabber']

            if serverid == '28':
                itemlist.append(
                    Item(
                        channel=item.channel,
                        action="play",
                        title='diretto',
                        quality='',
                        url=json['grabber'],
                        server='directo',
                        fulltitle=item.fulltitle,
                        show=item.show,
                        contentType=item.contentType,
                        folder=False))

    return support.server(item, videoData, itemlist)

