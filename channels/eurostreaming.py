# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Eurostreaming
# by Greko
# ------------------------------------------------------------
"""
    Problemi noti da non considerare come errori nel test:
        - Alcune sezioni di anime-cartoni non vanno:
            - alcune hanno solo la lista degli episodi, ma non hanno link!

    Novità(globale):
       - serie, anime
"""
import re
from core import scrapertoolsV2, httptools, support
from core.item import Item
from platformcode import config

#impostati dinamicamente da findhost()
host = ""
headers = ""

def findhost():
    global host, headers
    permUrl = httptools.downloadpage('https://eurostreaming.link/', follow_redirects=False).headers
    host = 'https://www.'+permUrl['location'].replace('https://www.google.it/search?q=site:', '')
    headers = [['Referer', host]]

findhost()

list_servers = ['verystream', 'wstream', 'speedvideo', 'flashx', 'nowvideo', 'streamango', 'deltabit', 'openload']
list_quality = ['default']

@support.menu
def mainlist(item):
    support.log()

    tvshow = [''
        ]

    anime = ['/category/anime-cartoni-animati/'
        ]

    mix = [
        (support.typo('Aggiornamenti Serie-Anime', 'bullet bold'), ['/aggiornamento-episodi/', 'peliculas', 'newest']),
        (support.typo('Archivio Serie-Anime', 'bullet bold'), ['/category/serie-tv-archive/', 'peliculas'])
        ]
    search = ''

    return locals()


@support.scrape
def peliculas(item):
    support.log()

    action = 'episodios'
    if item.args == 'newest':
        #patron = r'<span class="serieTitle" style="font-size:20px">(?P<title>.*?).[^–][\s]?<a href="(?P<url>[^"]+)"\s+target="_blank">(?P<episode>\d+x\d+-\d+|\d+x\d+) (?P<title2>.*?)[ ]?(?:|\((?P<lang>SUB ITA)\))?</a>'
        patron = r'<span class="serieTitle" style="font-size:20px">(?P<title>.*?).[^â][\s]?<a href="(?P<url>[^"]+)"\s+target="_blank">(?:<episode>\d+x\d+-\d+|\d+x\d+) .*?[ ]?\(?(?P<lang>SUB ITA)?\)?</a>'
        pagination = ''
    else:
        patron = r'<div class="post-thumb">.*?\s<img src="(?P<thumb>[^"]+)".*?><a href="(?P<url>[^"]+)"[^>]+>(?P<title>.+?)\s?(?: Serie Tv)?\s?\(?(?P<year>\d{4})?\)?<\/a><\/h2>'
        patronNext='a class="next page-numbers" href="?([^>"]+)">Avanti &raquo;</a>'
    
    #debug = True
    return locals()

@support.scrape
def episodios(item):
    support.log("episodios: %s" % item)

    action = 'findvideos'
    item.contentType = 'tvshow'
    # Carica la pagina
    data1 = pagina(item.url)
    data1 = re.sub('\n|\t', ' ', data1)
    data = re.sub(r'>\s+<', '> <', data1)
    patronBlock = r'(?P<block>STAGIONE\s\d+ (.+?)?(?:\()?(?P<lang>ITA|SUB ITA)(?:\))?.*?)</div></div>'
    #patron = r'(?:\s|\Wn)?(?:<strong>|)?(?P<episode>\d+&#\d+;\d+-\d+|\d+&#\d+;\d+)(?:</strong>|)?(?P<title>.+?)(?:–|-.+?-|â.+?â|â|.)?<a (?P<url>.*?)<br />'
    patron = r'(?:\s|\Wn)?(?:<strong>|)?(?P<episode>\d+&#\d+;\d+-\d+|\d+&#\d+;\d+)(?:</strong>|)?(?P<title>.+?)(?:â|-.+?-|Ã¢ÂÂ.+?Ã¢ÂÂ|Ã¢ÂÂ|.)?(?:<a (?P<url>.*?))?<br />'

    def itemHook(item):
        if not item.url:
            item.title += ' [B][COLOR red]### NO LINK ###[/COLOR][/B]'
        return item

    #support.regexDbg(item, patronBlock, headers, data)
    #debug = True
    return locals()

def pagina(url):
    support.log(url)

    data = httptools.downloadpage(url, headers=headers).data.replace("'", '"')
    #support.log("DATA ----###----> ", data)
    if 'clicca qui per aprire' in data.lower():
        url = scrapertoolsV2.find_single_match(data, '"go_to":"([^"]+)"')
        url = url.replace("\\","")
        # Carica la pagina
        data = httptools.downloadpage(url, headers=headers).data.replace("'", '"')

    elif 'clicca qui</span>' in data.lower():
        item.url = scrapertoolsV2.find_single_match(data, '<h2 style="text-align: center;"><a href="([^"]+)">')
        # Carica la pagina
        data = httptools.downloadpage(url, headers=headers).data.replace("'", '"')

    return data

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
            support.log(line)
        return []

# ===========  def novità in ricerca globale  =============

def newest(categoria):
    support.log()
    itemlist = []
    item = Item()
    item.contentType = 'tvshow'
    item.args = 'newest'
    try:
        item.url = "%s/aggiornamento-episodi/" % host
        item.action = "peliculas"
        itemlist = peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.log("{0}".format(line))
        return []

    return itemlist

# ===========  def findvideos  =============
def findvideos(item):
    support.log('findvideos', item)
    return support.server(item, item.url)
