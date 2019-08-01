# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per ToonItalia
# ------------------------------------------------------------

import re

from core import httptools, support
from platformcode import config, logger

__channel__ = "toonitalia"
host = config.get_channel_url(__channel__)

headers = [['Referer', host]]

list_servers = ['wstream', 'openload', 'streamango']
list_quality = ['HD', 'default']


@support.menu
def mainlist(item):

    top = [('Novità',['', 'peliculas', 'new', 'tvshow']),
           ('Aggiornamenti', ['', 'peliculas', 'last', 'tvshow']),
           ('Popolari', ['', 'peliculas', 'most_view', 'tvshow'])]   
    tvshow = '/lista-serie-tv/'
    anime =['/lista-anime-2/',
               ('Sub-Ita',['/lista-anime-sub-ita/']),
               ('Film Animati',['/lista-film-animazione/','peliculas', 'movie'])]    
    search = ''

    return locals()


@support.scrape
def peliculas(item):
    pagination = ''
    anime = True
    blacklist = '-Film Animazione disponibili in attesa di recensione (Link Wstream)-">-Film Animazione disponibili in attesa di recensione (Link Wstream)-'
    if item.args == 'movie': contentType = 'movie'
    if item.args == 'search':
        patron = r'<h2 class="entry-title"><a href="(?P<url>[^"]+)" rel="bookmark">(?P<title>[^<]+)</a>'
    elif item.args == 'last':
        patronBlock = 'Aggiornamenti</h2>(.*?)</ul>'
        patron = '<a href="(?P<url>[^"]+)">(?P<title>[^<]+)</a>'
    elif item.args == 'most_view':
        patronBlock = 'I piu visti</h2>(.*?)</ul>'
        patron = '<a href="(?P<url>[^"]+)" title="(?P<title>[^"]+)"'
    elif item.args == 'new':
        patronBlock = '<main[^>]+>(.*?)</main>'
        patron = '<a href="(?P<url>[^"]+)" rel="bookmark">(?P<title>[^<]+)</a>[^>]+>[^>]+>[^>]+><img.*?src="(?P<thumb>[^"]+)".*?<p>(?P<plot>[^<]+)</p>'
        patronNext = '<a class="next page-numbers" href="([^"]+)">'
    else:
        patronBlock = '"lcp_catlist"[^>]+>(.*?)</ul>'
        patron = r'<li ><a href="(?P<url>[^"]+)" title="[^>]+">(?P<title>[^<|\(]+)?(?:\([^\d]*(?P<year>\d+)\))?[^<]*</a>'
        
    action = 'findvideos' if item.contentType == 'movie' else 'check'

    return locals()

def check(item):
    data = httptools.downloadpage(item.url, headers=headers).data
    item.action = 'episodios'
    if 'https://vcrypt.net' in data: item.patron = '(?:<br /> |<p>)(?P<title>[^<]+)<a href="(?P<url>[^"]+)"'
    else: item.patron = '<br /> <a href="(?P<url>[^"]+)" target="_blank" rel="noopener[^>]+>(?P<title>[^<]+)</a>'
    itemlist = episodios(item)
    return itemlist


@support.scrape
def episodios(item):    
    anime = True
    patron = item.patron

    def itemHook(item):
        support.log(patron)
        item.title = item.fulltitle.replace('_',' ').replace('–','-')
        item.title = support.typo(re.sub(item.show + ' - ','',item.title, flags=re.I).strip(' - '), 'bold')        
        return item

    return locals()

def findvideos(item):
    return support.server(item, item.url if item.contentType != 'movie' else httptools.downloadpage(item.url, headers=headers).data )
