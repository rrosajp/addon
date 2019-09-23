# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per fastsubita
# Thanks Icarus crew & Alfa addon & 4l3x87
# ------------------------------------------------------------
"""

    Problemi noti che non superano il test del canale:
       - indicare i problemi

    Avvisi:
        - Eventuali avvisi per i tester

    Ulteriori info:
        - SOLO SUB-ITA

    ---------------------------------------------------
    Per i DEV:
        - nella ricerca, anche globale, esce la voce "successivo"
        ma apre la maschera per l'inserimento testo


"""
from core import support, httptools, scrapertoolsV2, tmdb
from core.item import Item
from core.support import log
from platformcode import config #, logger

__channel__ = 'fastsubita'
host = config.get_channel_url(__channel__)
headers = [['Referer', host]]
##IDIOMAS = {'Italiano': 'IT'}
##list_language = IDIOMAS.values()
list_servers = ['verystream', 'openload', 'speedvideo', 'wstream', 'flashx', 'vidoza', 'vidtome']
list_quality = ['default']

PERPAGE = 15

@support.menu
def mainlist(item):
    tvshow = ['',
        ('Archivio A-Z ', ['', 'list_az'])
    ]

    return locals()


@support.scrape
def peliculas(item):
    support.log(item)
    #dbg # decommentare per attivare web_pdb
    deflang = 'Sub-ITA'

    action = 'findvideos'
    blacklist = ['']
    patron = r'<div class="featured-thumb"> <a href="(?P<url>[^"]+)" title="(?:(?P<title>.+?)[ ]?(?P<episode>\d+&#215;\d+).+?&#8220;(?P<title2>.+?)&#8221;).+?">(?P<lang>Sub-ITA)?'
    patronBlock = r'<main id="main" class="site-main" role="main">(?P<block>.*?)<nav class="navigation pagination" role="navigation">'
    patronNext = '<a class="next page-numbers" href="(.*?)">Successivi'

    def itemHook(item):
        if item.args == 'newest':
            item.show = item.title# + support.typo('Sub-ITA', '_ [] color kod')
        return item

##    debug = True  # True per testare le regex sul sito
    return locals()


@support.scrape
def episodios(item):
    support.log(item)
    #dbg
    item.args = 'episodios'
    deflang = 'Sub-ITA'
    action = 'findvideos'
    blacklist = ['']
    patron = r'<div class="featured-thumb"> <a href="(?P<url>[^"]+)" title="(?:(?P<title>.+?)[ ]?(?P<episode>\d+&#215;\d+).+?&#8220;(?P<title2>.+?)&#8221;).+?">(?P<lang>Sub-ITA)?'
    patronBlock = r'<main id="main" class="site-main" role="main">(?P<block>.*?)</main>'
    patronNext = '<a class="next page-numbers" href="(.*?)">Successivi'

##    debug = True
    return locals()


def list_az(item):
    log()
    itemlist = []

    alphabet = dict()

    for i, (scrapedurl, scrapedtitle) in enumerate(serietv()):
        letter = scrapedtitle[0].upper()
        if letter not in alphabet:
            alphabet[letter] = []
        alphabet[letter].append(str(scrapedurl) + '||' + str(scrapedtitle))

    for letter in sorted(alphabet):
        itemlist.append(
            Item(channel=item.channel,
                 action="lista_serie",
                 url='\n\n'.join(alphabet[letter]),
                 title=letter,
                 fulltitle=letter))

    return itemlist


def cleantitle(scrapedtitle):
    scrapedtitle = scrapertoolsV2.decodeHtmlentities(scrapedtitle.strip())
    scrapedtitle = scrapedtitle.replace('’', '\'').replace('&#215;', 'x').replace('×', 'x').replace('"', "'")

    return scrapedtitle.strip()


def serietv():
    log()

    itemlist = []
    matches = support.match(Item(), r'<option class="level-0" value="([^"]+)">([^<]+)</option>',
                            r'<select\s*?name="cat"\s*?id="cat"\s*?class="postform"\s*?>(.*?)</select>', headers,
                            url="%s/" % host)[0]
    index = 0

    for cat, title in matches:
        title = cleantitle(title)
        url = '%s?cat=%s' % (host, cat)
##        if int(level) > 0:
##            itemlist[index - 1][0] += '{|}' + url
##            continue

        itemlist.append([url, title])

        index += 1
    return itemlist


def lista_serie(item):
    log()
    itemlist = []

    p = 1
    if '{}' in item.url:
        item.url, p = item.url.split('{}')
        p = int(p)

    if '||' in item.url:
        series = item.url.split('\n\n')
        matches = []
        for i, serie in enumerate(series):
            matches.append(serie.decode('utf-8').split('||'))
        series = matches
        support.log("SERIE ALF :", series)
    else:
        series = serietv()
        support.log("SERIE ALF 2 :", series)

    for i, (scrapedurl, scrapedtitle) in enumerate(series):
        if (p - 1) * PERPAGE > i: continue
        if i >= p * PERPAGE: break

        scrapedplot = ""
        scrapedthumbnail = ""

        itemlist.append(
            Item(channel=item.channel,
                 action="episodios",
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 plot=scrapedplot,
                 show=scrapedtitle,
                 extra=item.extra,
                 contentType='tvshow',
                 originalUrl=scrapedurl,
                 folder=True))

    support.checkHost(item, itemlist)
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    if len(series) >= p * PERPAGE:
        next_page = item.url + '{}' + str(p + 1)
        support.nextPage(itemlist, item, next_page=next_page)

    return itemlist


############## Fondo Pagina
# da adattare al canale
def search(item, text):
    support.log('search', item)
    itemlist = []
    text = text.replace(' ', '+')
    item.url = host + '?s=' + text
    # bisogna inserire item.contentType per la ricerca globale
    # se il canale è solo film, si può omettere, altrimenti bisgona aggiungerlo e discriminare.
    
    try:
        item.contentType = 'tvshow'
        return peliculas(item)
    # Se captura la excepcion, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            log('search log:', line)
        return []


# da adattare al canale
# inserire newest solo se il sito ha la pagina con le ultime novità/aggiunte
# altrimenti NON inserirlo
def newest(categoria):
    support.log('newest ->', categoria)
    itemlist = []
    item = Item()
    try:
        item.contentType = 'tvshow'
        item.args = 'newest'
        item.url = host
        item.action = 'peliculas'
        itemlist = peliculas(item)

        if itemlist[-1].action == 'peliculas':
            itemlist.pop()
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.log('newest log: ', {0}.format(line))
        return []

    return itemlist


def findvideos(item):
    support.log('findvideos ->', item)
    patronBlock = '<div class="entry-content">(?P<block>.*)<footer class="entry-footer">'
    patron = r'<a href="([^"]+)">'
    matches, data = support.match(item, patron, patronBlock, headers)

    if item.args != 'episodios':
        item.infoLabels['mediatype'] = 'episode'
    for scrapedurl in matches:
        if 'is.gd' in scrapedurl:
            resp = httptools.downloadpage(scrapedurl, follow_redirects=False)
            data += resp.headers.get("location", "") + '\n'

    return support.server(item, data)
