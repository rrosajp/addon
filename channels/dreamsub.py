# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per 'dreamsub'
# ------------------------------------------------------------
# ------------------------------------------------------------
"""

    Problemi noti che non superano il test del canale:
       - Nessuno noto!

    Avvisi per i tester:
        1. Gli episodi sono divisi per pagine di 20
        2. In Novità->Anime, cliccare sulla home il bottone "Ultime inserite"
         Se avete più titoli in KOD, ridimensiona il browser in modo che si vedano i titoli
         a gruppi di 3 e ricontrollare, è un problema del sito.

        3.Passaggi per Aggiungere in videoteca e/o scaricare Serie:
            1. sul titolo -> menu contestuale -> Rinumerazione
            Solo dopo questo passaggio appariranno le voci, sul titolo -> menu contestuale ->:
                - Aggiungi in videoteca (senza rinumerazione non appare
                la voce)
                - Scarica Serie e Scarica Stagione ( Se download Abilitato! )

        4. ### PIù IMPORTANTE!!! ###
        #### NON E' DA CONSIDERARE ERRORE NEL TEST QUANTO RIPORTATO DI SEGUITO!!!! ####
            1. Il sito permette un filtro tra anime e film, tramite url.
                Se nell'url c'è /anime/, sul titolo e proseguendo fino alla pagina del video, saranno
                presenti le voci:
                    - 'Rinumerazione', prima, e dopo: 'Aggiungi in videoteca', 'Scarica Serie' etc...
                Tutto il resto è trattato come film e si avranno le voci solite:
                AD eccezione per quei "FILM" che hanno 2 o più titoli all'interno, in questo caso:
                    1. Non apparirà nessuna voce tra "Aggiungi in videoteca" e "Scarica Film" e nemmeno "rinumerazione"
                    2. Dopo essere entrato nella pagina del Titolo Principale, troverai una lista di titoli dove sarà possibile scaricare
                    il filmato (chiamato EPISODIO) stessa cosa accedendo alla pagina ultima del video
                    3. Questi TITOLI NON POSSONO ESSERE AGGIUNTI IN VIDEOTECA
                le voci "Scarica FILM" si avranno dopo.

                Es:
                https://www.dreamsub.stream/movie/5-centimetri-al-secondo -> film ma ha 3 titoli

    Il Canale NON è presente nelle novità(globale) -> Anime


"""
# Qui gli import
import re

from core import support
from platformcode import config
from core import scrapertoolsV2, httptools, servertools, tmdb
from core.item import Item

##### fine import
__channel__ = "dreamsub"
host = config.get_channel_url(__channel__)
headers = [['Referer', host]]

# server di esempio...
list_servers = ['directo', 'verystream', 'streamango', 'openload']
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
             ('Movie', ['/search/movie', 'peliculas', '', 'movie']),
             ('Film', ['/search/film', 'peliculas', '', 'movie']),
             ('Categorie', ['/filter?genere=','genres']),
##             ('Ultimi Episodi', ['', 'last'])
             ]

    return locals()

@support.scrape
def peliculas(item):
    support.log(item)
    #dbg # decommentare per attivare web_pdb

    anime = True
    if item.args == 'newest':
        patronBlock = r'<div class="showRoomGoLeft" sr="ultime"></div>(?P<block>.*?)<div class="showRoomGoRight" sr="ultime">'
    else:
        patronBlock = r'<input type="submit" value="Vai!" class="blueButton">(?P<block>.*?)<div class="footer">'

##    patron = r'<div class="showStreaming"> <b>(?P<title>[^<]+).+?Stato streaming: '\
##             '(?:[^<]+)<.*?Lingua:[ ](?P<lang1>ITA\/JAP|ITA|JAP)?(?:[ ])?'\
##             '(?P<lang2>SUB ITA)?<br>.+?href="(?P<url>[^"]+)".+?'\
##             'background: url\((?P<thumb>[^"]+)\).+?<div class="tvTitle">.+?'\
##             '<strong>Anno di inizio</strong>: (?P<year>\d+)<br>'

        patron = r'<div class="showStreaming"> <b>(?P<title>[^<]+).+?Stato streaming: (?:[^<]+)<.*?Lingua:[ ](?P<lang1>ITA\/JAP|ITA|JAP)?(?:[ ])?(?P<lang2>SUB ITA)?<br>.+?href="(?P<url>[^"]+)".+?background: url\((?P<thumb>[^"]+)\).+?<div class="tvTitle">.+?Episodi[^>]+>.\s?(?P<nep>\d+).+?<strong>Anno di inizio</strong>: (?P<year>\d+)<br>'
    patronNext = '<li class="currentPage">[^>]+><li[^<]+<a href="([^"]+)">'

    def itemHook(item):
        support.log("ITEMHOOK -> ", item)
        item = language(item)

        if 'anime' in item.url:
            item.contentType = 'tvshow'
            item.action = 'episodios'
            #item.args = 'anime'
        else:
            if item.nep == '1':
                item.contentType = 'movie'
                item.action = 'findvideos'
            else:
                item.contentType = 'episode'
                item.args = ''
                item.nep = item.nep
                item.action = 'findmovie'
        return item

    #debug = True
    return locals()

@support.scrape
def episodios(item):
    support.log(item)
    #support.dbg()

    action = 'findvideos'
    patronBlock = r'<div class="seasonEp">(?P<block>.*?)<div class="footer">'
    patron = r'<li><a href="(?P<url>[^"]+)"[^<]+<b>(?:.+?)[ ](?P<episode>\d+)<\/b>[^>]+>(?P<title>[^<]+)<\/i>[ ]\(?(?P<lang1>ITA|Sub ITA)?\s?.?\s?(?P<lang2>Sub ITA)?.+?\)?<\/a>'

    def itemHook(item):
        item = language(item)
        return item

    pagination = ''

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


@support.scrape
def findmovie(item):
    support.log(item)

    patronBlock = r'<div class="seasonEp">(?P<block>.*?)<div class="footer">'
    item.contentType = 'episode'
    item.nep = 2
    patron = r'<li><a href="(?P<url>[^"]+)"[^>]+>.(?P<title2>.+?)-.+?-[ ]<b>(?P<title>.+?)</b>\s+\(?(?P<lang1>ITA)?\s?(?P<lang2>Sub ITA)?.+?\)?'

    def itemHook(item):
        item = language(item)
        return item

    #debug = True
    return locals()


def language(item):
    lang = []

    if item.lang1:
        if item.lang1.lower() == 'ita/jap' or item.lang1.lower() == 'ita':
            lang.append('ITA')

        if item.lang1.lower() == 'jap' and item.lang1.lower() == 'sub ita':
            lang.append('Sub-ITA')

    if item.lang2:
        if item.lang2.lower() == 'sub ita':
            lang.append('Sub-ITA')

    item.contentLanguage = lang

    if len(lang) ==2:
        item.title += support.typo(lang[0], '_ [] color kod') + support.typo(lang[1], '_ [] color kod')
        #item.show += support.typo(lang[0], '_ [] color kod') + support.typo(lang[1], '_ [] color kod')
    elif len(lang) == 1:
        item.title += support.typo(lang[0], '_ [] color kod')
        #item.show += support.typo(lang[0], '_ [] color kod')

    return item


def search(item, text):
    support.log('search', item)
    itemlist = []

    text = text.replace(' ', '+')
    item.url = host + '/search/' + text
    item.args = 'search'
    try:
        return peliculas(item)
    # Se captura la excepcion, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            support.log('search log:', line)
        return []


# da adattare... ( support.server ha vari parametri )
#support.server(item, data='', itemlist=[], headers='', AutoPlay=True, CheckLinks=True)
def findvideos(item):
    support.log("ITEM ---->", item)
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r'\n|\t', ' ', data)
    data = re.sub(r'>\s\s*<', '><', data)
    patronBlock = r'LINK STREAMING(?P<block>.*?)LINK DOWNLOAD'
    patron = r'href="(.+?)"'
    block = scrapertoolsV2.find_single_match(data, patronBlock)
    urls = scrapertoolsV2.find_multiple_matches(block, patron)
    #support.regexDbg(item, patron, headers, data=data)

    for url in urls:
        titles = item.infoLabels['title']
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
            #host_video = scrapertoolsV2.find_single_match(data, r'var thisPageUrl = "(http[s]\:\/\/[^\/]+).+?"')
            host_video = scrapertoolsV2.find_single_match(data, r'(?:let|var) thisPageUrl = "(http[s]\:\/\/[^\/]+).+?"')
            link = scrapertoolsV2.find_single_match(data, r'<video src="([^"]+)"')
            video_urls = host_video+link

        title_show =  support.typo(titles,'_ bold') + support.typo(lang,'_ [] color kod')

        itemlist.append(
            support.Item(channel=item.channel,
                         action="play",
                         contentType=item.contentType,
                         title=title_show,
                         fulltitle=item.fulltitle,
                         show=item.fulltitle,
                         url=link if 'http' in link else video_urls,
                         infoLabels = item.infoLabels,
                         thumbnail=item.thumbnail,
                         contentSerieName= item.fulltitle,
                         contentTitle=title_show,
                         contentLanguage = 'ITA' if lang == [] else lang,
                         args=item.args,
                         server='directo',
                         ))

    if item.contentType != 'episode' and int(item.nep) < 2 :
        # Link Aggiungi alla Libreria
        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findservers':
           support.videolibrary(itemlist, item)
    # link per scaricare
    if config.get_setting('downloadenabled'):
        support.download(itemlist, item)
    return itemlist
