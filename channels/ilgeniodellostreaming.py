# -*- coding: utf-8 -*-
# ------------------------------------------------------------
#
# Canale per ilgeniodellostreaming
# ------------------------------------------------------------

"""

    Problemi noti che non superano il test del canale:
        NESSUNO (update 13-9-2019)

    Avvisi per il test:
    i link per le categorie non sono TUTTI visibili nella pagina del sito:
    vanno costruiti con i nomi dei generi che vedete nel CANALE.
    Es:
        https://ilgeniodellostreaming.se/genere/+ genere nel canale
    genere-> kids
        https://ilgeniodellostreaming.se/genere/kids
    genere-> avventura
        https://ilgeniodellostreaming.se/genere/avventura
    Se il genere è formato da 2 parola lo spazio si trasforma in -
    genere-> televisione film
        https://ilgeniodellostreaming.se/genere/televisione-film

    Non va abilitato per:
        Novità -> Anime
    La pagina "Aggiornamenti Anime" del sito è vuota (update 13-9-2019)

"""

import re

from platformcode import  logger
from core import scrapertoolsV2, httptools, tmdb, support
from core.support import log, menu, aplay
from core.item import Item
from platformcode import config

__channel__ = 'ilgeniodellostreaming'
host = config.get_channel_url(__channel__)

list_servers = ['verystream', 'openload', 'streamango']
list_quality = ['default']

headers = [['Referer', host]]

@support.menu
def mainlist(item):
    support.log(item)

    film = ['/film/',
        ('Film Per Categoria',['', 'category', 'genres']),
        ('Film Per Anno',['', 'category', 'year']),
        ('Film Per Lettera',['/film-a-z/', 'category', 'letter']),
        ('Popolari',['/trending/?get=movies', 'peliculas', 'populared']),
        ('Più Votati', ['/ratings/?get=movies', 'peliculas', 'populared'])
            ]

    tvshow = ['/serie/',
        ('Nuovi Episodi', ['/aggiornamenti-serie/', 'newep', 'tvshow']),
        ('TV Show', ['/tv-show/', 'peliculas', 'showtv', 'tvshow'])
        ]

    anime = ['/anime/']

    search = ''

    return locals()


@support.scrape
def category(item):
    log(item)

    action='peliculas'
    if item.args == 'genres':
        patronBlock = r'<div class="sidemenu"><h2>Genere</h2>(?P<block>.*?)/li></ul></div>'
    elif item.args == 'year':
        patronBlock = r'<div class="sidemenu"><h2>Anno di uscita</h2>(?P<block>.*?)/li></ul></div>'
    elif item.args == 'letter':
        patronBlock = r'<div class="movies-letter">(?P<block>.*?)<div class="clearfix">'
    patron = r'<a(?:.+?)?href="(?P<url>.*?)"[ ]?>(?P<title>.*?)<\/a>'

##    debug = True
    return locals()

def search(item, texto):
    log(texto)
    item.url = host + "/?s=" + texto
    try:
        return peliculas(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)

    return []

@support.scrape
def peliculas(item):
    log(item)
##    import web_pdb; web_pdb.set_trace()

    if item.action == 'search':
        patronBlock = r'<div class="search-page">(?P<block>.*?)<footer class="main">'
        patron = r'<div class="thumbnail animation-2"><a href="(?P<url>[^"]+)">'\
                 '<img src="(?P<thumb>[^"]+)" alt="[^"]+" \/>[^>]+>(?P<type>[^<]+)'\
                 '<\/span>.*?<a href.*?>(?P<title>.+?)[ ]?(?:\[(?P<lang>Sub-ITA)\])?'\
                 '<\/a>[^>]+>(?:<span class="rating">IMDb\s*(?P<rating>[0-9.]+)<\/span>)?'\
                 '.+?(?:<span class="year">(?P<year>[0-9]+)<\/span>)?[^>]+>[^>]+><p>(?P<plot>.*?)<\/p>'
        type_content_dict={'movie': ['film'], 'tvshow': ['tv']}
        type_action_dict={'findvideos': ['film'], 'episodios': ['tv']}

##    elif item.args == 'newest':
##        patronBlock = r'<div class="content"><header><h1>Aggiornamenti Serie</h1>'\
##                      '</header>(?P<block>.*?)</li></ul></div></div></div>'
##        patron = r'src="(?P<thumb>[^"]+)".*?href="(?P<url>[^"]+)">[^>]+>(?P<episode>[^<]+)'\
##                 '<.*?"c">(?P<title>.+?)[ ]?(?:\[(?P<lang>Sub-ITA)\])?<.+?<span class='\
##                 '"quality">(\5SUB-ITA|.+?)</span>'

    elif item.args == 'letter':
        patron = r'<td class="mlnh-2"><a href="(?P<url>[^"]+)">(?P<title>.+?)'\
                 '[ ]?(?:\[(?P<lang>Sub-ITA)\])?<[^>]+>[^>]+>[^>]+>(?P<year>\d{4})\s+<'
    elif item.args == 'populared':
        patron = r'<div class="poster"><a href="(?P<url>[^"]+)"><img src='\
                 '"(?P<thumb>[^"]+)" alt="[^"]+"><\/a>[^>]+>[^>]+>[^>]+> '\
                 '(?P<rating>[0-9.]+)<[^>]+>[^>]+>'\
                 '(?P<quality>[3]?[D]?[H]?[V]?[D]?[/]?[R]?[I]?[P]?)(?:SUB-ITA)?<'\
                 '[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<title>.+?)(?:[ ]\[(?P<lang>Sub-ITA)\])?<'\
                 '[^>]+>[^>]+>[^>]+>(?P<year>\d{4})?<'

    elif item.args == 'showtv':
        action = 'episodios'
        patron = r'<div class="poster"><a href="(?P<url>[^"]+)"><img src="(?P<thumb>[^"]+)" '\
                 'alt="[^"]+"><\/a>[^>]+>[^>]+>[^>]+> (?P<rating>[0-9.]+)<[^>]+>[^>]+>[^>]+>'\
                 '[^>]+>[^>]+>(?P<title>.+?)<[^>]+>[^>]+>[^>]+>(?P<year>\d{4})?<[^>]+>[^>]+>'\
                 '[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<plot>.+?)<'

    elif item.contentType == 'movie' and item.args != 'genres':
        patronBlock = r'<header><h1>Film</h1>(?P<block>.*?)<div class="pagination">'
        patron = r'<div class="poster">\s*<a href="(?P<url>[^"]+)"><img src="(?P<thumb>[^"]+)" '\
                 'alt="[^"]+"><\/a>[^>]+>[^>]+>[^>]+>\s*(?P<rating>[0-9.]+)<\/div>'\
                 '<span class="quality">(?:SUB-ITA|)?(?P<quality>|[^<]+)?'\
                 '<\/span>[^>]+>[^>]+>[^>]+>[^>]+>(?P<title>.+?)[ ]?(?:\[(?P<lang>Sub-ITA)\])?'\
                 '<\/a>[^>]+>'\
                 '[^>]+>(?P<year>[^<]+)<\/span>[^>]+>[^>]+>'\
                 '[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<plot>[^<]+)<div'

    elif item.contentType == 'tvshow' or item.args == 'genres':
        action = 'episodios'
        patron = r'<div class="poster">\s*<a href="(?P<url>[^"]+)"><img '\
                 'src="(?P<thumb>[^"]+)" alt="[^"]+"><\/a>[^>]+>[^>]+>[^>]+> '\
                 '(?P<rating>[0-9.]+)<[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>'\
                 '(?P<title>.+?)[ ]?(?:\[(?P<lang>Sub-ITA|Sub-ita)\])?<[^>]+>[^>]+>'\
                 '[^>]+>(?P<year>[^<]+)<.*?<div class="texto">(?P<plot>[^<]+)'

##    else:
##        patron = r'<div class="thumbnail animation-2"><a href="(?P<url>[^"]+)">'\
##                 '<img src="(?P<thumb>[^"]+)" alt="[^"]+" \/>'\
##                 '[^>]+>(?P<type>[^<]+)<\/span>.*?<a href.*?>(?P<title>[^<]+)'\
##                 '<\/a>(?P<lang>[^>])+>[^>]+>(?:<span class="rating">IMDb\s*'\
##                 '(?P<rating>[0-9.]+)<\/span>)?.*?(?:<span class="year">(?P<year>[0-9]+)'\
##                 '<\/span>)?[^>]+>[^>]+><p>(?P<plot>.*?)<\/p>'
####        type_content_dict={'movie': ['film'], 'tvshow': ['tv']}
####        type_action_dict={'findvideos': ['film'], 'episodios': ['tv']}

    patronNext = '<span class="current">[^<]+<[^>]+><a href="([^"]+)"'

    debug = True
    return locals()


@support.scrape
def newep(item):

    patron = r'<div class="poster"><img src="(?P<thumb>[^"]+)" alt="(?:.+?)[ ]?'\
             '(?:\[(?P<lang>Sub-ITA|Sub-ita)\])?">[^>]+><a href="(?P<url>[^"]+)">'\
             '[^>]+>(?P<episode>[^<]+)<[^>]+>[^>]+>[^>]+><span class="c">'\
             '(?P<title>.+?)[ ]?(?:\[Sub-ITA\]|)<'
    pagination = 10
##    debug = True
    return locals()


@support.scrape
def episodios(item):
    log()

    patronBlock = r'<h1>.*?[ ]?(?:\[(?P<lang>.+?\]))?</h1>.+?<div class="se-a" '\
                  'style="display:block"><ul class="episodios">(?P<block>.*?)</ul>'\
                  '</div></div></div></div></div>'
    patron = r'<a href="(?P<url>[^"]+)"><img src="(?P<thumb>[^"]+)">.*?'\
             '<div class="numerando">(?P<episode>[^<]+).*?<div class="episodiotitle">'\
             '[^>]+>(?P<title>[^<]+)<\/a>'
#    debug = True
    return locals()


def newest(categoria):
    log(categoria)
    itemlist = []
    item = Item()

    action = peliculas

    if categoria == 'peliculas':
        item.contentType = 'movie'
        item.url = host + '/film/'
    elif categoria == 'series':
        action = newep
        #item.args = 'newest'
        item.contentType = 'tvshow'
        item.url = host + '/aggiornamenti-serie/'
##    elif categoria == 'anime':
##        item.contentType = 'tvshow'
##        item.url = host + '/anime/'
    try:
        item.action = action
        itemlist = action(item)

        if itemlist[-1].action == action:
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def findvideos(item):
    log()
    itemlist =[]
    matches, data = support.match(item, '<iframe class="metaframe rptss" src="([^"]+)"[^>]+>',headers=headers)
    for url in matches:
        html = httptools.downloadpage(url, headers=headers).data
        data += str(scrapertoolsV2.find_multiple_matches(html, '<meta name="og:url" content="([^"]+)">'))
    itemlist = support.server(item, data)
    return itemlist

