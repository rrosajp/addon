# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per 'dreamsub'
# ------------------------------------------------------------
# ------------------------------------------------------------
"""

    Problemi noti che non superano il test del canale:
       - indicare i problemi

    Avvisi:
       - Gli episodi sono divisi per pagine di 20
       - In Novità->Anime, cliccare sulla home il bottone "Ultime inserite"
         Se avete più titoli in KOD, ridimensiona il browser in modo che si vedano i titoli
         a gruppi di 3 e ricontrollare, è un problema del sito.


    Ulteriori info:
       -


    -------------------------------------------------------
    NOTA per i DEV:
        - Dai risultati dei Menu vengono tolti quei titoli
          che non hanno la corrispettiva parola nel link, secondo lo schema seguente:
            Menu        Parole nel link
            ---------------------------
            OAV         oav
            OVA         ova
            Speciali    movie
            Movie       movie
            Serie       Tutti gli altri casi
        Es:
        https://www.dreamsub.stream/oav/another-the-other - è un OAV
"""
# Qui gli import
import re
import copy

from core import support
from platformcode import config
##from specials.autorenumber import renumber
from specials import autorenumber
# in caso di necessità

from core import scrapertoolsV2, httptools, servertools, tmdb
from core.item import Item
#from lib import unshortenit

##### fine import
__channel__ = "dreamsub"
host = config.get_channel_url(__channel__)
headers = [['Referer', host]]

# server di esempio...
list_servers = ['verystream', 'streamango', 'openload', 'directo']
# quality di esempio
list_quality = ['default']

#### Inizio delle def principali ###

@support.menu
def mainlist(item):
    support.log(item)


    anime = ['/anime',
##             ('Novità', ['']),
##             ('OAV', ['/search/oav', 'peliculas', 'oav']),
##             ('OVA', ['/search/ova', 'peliculas', 'ova']),
             ('Movie', ['/search/movie', 'peliculas', 'special']),
             ('Film', ['/search/film', 'peliculas', 'special']),
             ('Categorie', ['/filter?genere=','genres']),
##             ('Ultimi Episodi', ['', 'last'])
             ]
    """
        Eventuali Menu per voci non contemplate!
    """

    return locals()

@support.scrape
def peliculas(item):
    support.log(item)
    #dbg # decommentare per attivare web_pdb

    anime = True
    action = 'episodios'
    item.contentType = 'tvshow'
    if item.args == 'newest':
         patronBlock = r'<div class="showRoomGoLeft" sr="ultime"></div>(?P<block>.*?)<div class="showRoomGoRight" sr="ultime">'
    else:
        patronBlock = r'<input type="submit" value="Vai!" class="blueButton">(?P<block>.*?)<div class="footer">'

    patron = r'<div class="showStreaming"> <b>(?P<title>[^<]+).+?Stato streaming: '\
             '(?:[^<]+)<.*?Lingua:[ ](?P<lang1>ITA\/JAP|ITA|JAP)?(?:[ ])?'\
             '(?P<lang2>SUB ITA)?<br>.+?href="(?P<url>[^"]+)".+?'\
             'background: url\((?P<thumb>[^"]+)\).+?<div class="tvTitle">.+?'\
             '<strong>Anno di inizio</strong>: (?P<year>\d+)<br>'

    patronNext = '<li class="currentPage">[^>]+><li[^<]+<a href="([^"]+)">'

    def itemHook(item):
        support.log("ITEMHOOK -> ", item)
        lang = []
        if item.lang1 == 'ITA/JAP' or item.lang1 == 'ITA':
            lang.append('ITA')

        if item.lang1 == 'JAP' and item.lang2 == 'SUB ITA' or item.lang2 == 'SUB ITA':
            lang.append('Sub-ITA')
        support.log("ITEMHOOK LANG-> ", lang)
        item.contentLanguage = lang

        if len(lang) == 2:
            item.title += ' [COLOR 0xFF65B3DA][' + lang[0] + '][/COLOR]'+' [COLOR 0xFF65B3DA][' + lang[1] + '][/COLOR]'
        elif len(lang) == 1 and lang[0] != 'ITA':
            item.title += ' [COLOR 0xFF65B3DA][' + lang[0] + '][/COLOR]'

        # se si riesce a differenziare in qualche modo tramite il link
##            if item.args == 'oav':
##                if not '/oav/' in url:
##                    continue
##            elif item.args == 'ova':
##                if not '/ova/' in url:
##                    continue
##            elif item.args == 'special':
        if item.args == 'search' or item.args == 'special':
##            if '/movie/' in item.url:
##                item.args = 'special'
##        if item.args == 'special':
            item.action = 'findvideos'
            item.contentType = 'movie'
            if not '/movie/' in item.url:
                pass
        return item

    #debug = True
    return locals()

@support.scrape
def episodios(item):
    support.log(item)
    #dbg
    anime = True
##    item.contentType = 'episode'
    action = 'findvideos'
    blacklist = ['']

    patronBlock = r'<div class="seasonEp">(?P<block>.*?)<div class="footer">'
    patron = r'<li><a href="(?P<url>[^"]+)"[^<]+<b>(?:.+?)[ ](?P<episode>\d+)<\/b>[^>]+>(?P<title>[^<]+)<\/i>[ ]\((?P<lang1>ITA)?\s?.+?\s?(?P<lang2>Sub ITA)?.+?\)<\/a>'
    pagination = ''

    #UnicodeDecodeError: 'ascii' codec can't decode byte 0xc3 in position 18: ordinal not in range(128)
    def itemHook(item):
        support.log("ITEMHOOK EPISODE LANG1 -> ", item)
        lang = []
        if item.lang1 == 'ITA':
            lang.append('ITA')

        if item.lang2 == 'Sub ITA':
            lang.append('Sub-ITA')
        support.log("ITEMHOOK EPISODE LANG2-> ", lang)
        item.contentLanguage = lang
        support.log("ITEMHOOK EPISODE LANG3 -> ", item, lang)
        if len(lang) ==2:
            item.title += ' [COLOR 0xFF65B3DA][' + lang[0] + '][/COLOR]'+' [COLOR 0xFF65B3DA][' + lang[1] + '][/COLOR]'
            item.show += ' [COLOR 0xFF65B3DA][' + lang[0] + '][/COLOR]'+' [COLOR 0xFF65B3DA][' + lang[1] + '][/COLOR]'
        elif len(lang) == 1 and lang[0] != 'ITA':
            item.title += ' [COLOR 0xFF65B3DA][' + lang[0] + '][/COLOR]'
            item.show += ' [COLOR 0xFF65B3DA][' + lang[0] + '][/COLOR]'
        return item

    #debug = True
    return locals()

@support.scrape
def genres(item):
    support.log(item)
    #dbg
    item.contentType = ''
    action = 'peliculas'
    blacklist = ['tutti']
    patron = r'<option value="(?P<title>[^"]+)">'
    patronBlock = r'<select name="genere" id="genere" class="selectInput">(?P<block>.*?)</select>'

    def itemHook(item):
        item.contentTitle = item.contentTitle.replace(' ', '+')
        item.url = host+'/filter?genere='+item.contentTitle
        return item
    #debug = True
    return locals()

def search(item, text):
    support.log('search', item)
    itemlist = []
    text = text.replace(' ', '+')
    item.url = host + '/search/' + text
    item.contentType = item.contentType
    item.args = 'search'
    try:
        return peliculas(item)
    # Se captura la excepcion, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            support.log('search log:', line)
        return []

def newest(categoria):
    support.log('newest ->', categoria)
    itemlist = []
    item = Item()
    item.contentType = 'tvshow'
    item.args = 'newest'
    try:
        item.url = host
        item.action = 'peliculas'
        itemlist = peliculas(item)

        if itemlist[-1].action == 'peliculas':
            itemlist.pop()
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            log('newest log: ', {0}.format(line))
        return []

    return itemlist

# da adattare... ( support.server ha vari parametri )
#support.server(item, data='', itemlist=[], headers='', AutoPlay=True, CheckLinks=True)
def findvideos(item):
    support.log()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r'\n|\t', ' ', data)
    data = re.sub(r'>\s\s*<', '><', data)
    patronBlock = r'LINK STREAMING(?P<block>.*?)LINK DOWNLOAD'
    patron = r'href="(.+?)"'
    block = scrapertoolsV2.find_single_match(data, patronBlock)
    urls = scrapertoolsV2.find_multiple_matches(block, patron)

    for url in urls:

        lang = ''
        if 'sub_ita' in url.lower():
            lang = 'Sub-ITA'
        else:
            lang = 'ITA'

        if 'keepem.online' in data:
            urls = scrapertoolsV2.find_multiple_matches(data, r'(https://keepem\.online/f/[^"]+)"')
            for url in urls:
                url = httptools.downloadpage(url).url
                itemlist += servertools.find_video_items(data=url)

        elif 'keepsetsu' in url.lower() or 'woof' in url.lower():
            if 'keepsetsu' in url.lower():
                support.log("keepsetsu url -> ", url )
                data = httptools.downloadpage(url).url
                support.log("LINK-DATA :", data)

            data = httptools.downloadpage(data).data
            support.log("LINK-DATA2 :", data)
            video_urls = scrapertoolsV2.find_single_match(data, r'<meta name="description" content="([^"]+)"')

        else:

            data = httptools.downloadpage(url).data
            host_video = scrapertoolsV2.find_single_match(data, r'var thisPageUrl = "(http[s]\:\/\/[^\/]+).+?"')
            link = scrapertoolsV2.find_single_match(data, r'<video src="([^"]+)"')
            video_urls = host_video+link

        title =  support.typo(item.fulltitle,'_ bold') + support.typo(lang,'_ [] color kod')
        itemlist.append(
            support.Item(channel=item.channel,
                         action="play",
                         contentType=item.contentType,
                         title=title,
                         fulltitle=title,
                         show=title,
                         url=video_urls,
                         infoLabels=item.infoLabels,
                         thumbnail=item.thumbnail,
                         contentSerieName= item.contentSerieName,
                         contentTitle=title,
                         contentLanguage = 'ITA' if lang == [] else lang,
                         args=item.args,
                         server='directo',
                         ))
    return itemlist
