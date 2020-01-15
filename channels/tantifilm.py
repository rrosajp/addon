# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Tantifilm
# ------------------------------------------------------------

import re

from core import scrapertools, httptools, tmdb, support
from core.item import Item
from core.support import menu, log
from platformcode import logger
from specials import autorenumber
from platformcode import config, unify
from lib.unshortenit import unshorten_only


def findhost():
    permUrl = httptools.downloadpage('https://www.tantifilm.info/', follow_redirects=False).data
    host = 'https://' + scrapertools.find_single_match(permUrl, r'Ora siamo ([A-Za-z0-9./]+)')
    return host

host = config.get_channel_url(findhost)
headers = [['Referer', host]]
list_servers = ['verystream', 'openload', 'streamango', 'vidlox', 'youtube']
list_quality = ['default']


@support.menu
def mainlist(item):
    log()


    #top = [(support.typo('Novità Film/Serie/Anime/Altro', 'bold'),['/film/'])]
    top = [('Novità Film/Serie/Anime/Altro', ['/film/', 'peliculas', 'all'])]

    film = ['/watch-genre/film-aggiornati/',
        ('Al Cinema', ['/watch-genre/al-cinema/']),
        ('HD', ['/watch-genre/altadefinizione/']),
        ('Sub-ITA', ['/watch-genre/sub-ita/'])

        ]

    tvshow = ['/serie-tv/',
        ('HD', ['/watch-genre/serie-altadefinizione/']),
        ('Miniserie', ['/watch-genre/miniserie-1/']),
        ('Programmi TV', ['/watch-genre/programmi-tv/']),
        #('LIVE', ['/watch-genre/live/'])
        ]

    anime = ['/watch-genre/anime/'
        ]

    search = ''
    return locals()

@support.scrape
def peliculas(item):
    log()


    if item.args == 'search':
        patron = r'<a href="(?P<url>[^"]+)" title="Permalink to\s(?P<title>[^"]+) \((?P<year>[^<]+)\).*?".*?<img[^s]+src="(?P<thumb>[^"]+)".*?<div class="calitate">\s*<p>(?P<quality>[^<]+)<\/p>'
        # support.regexDbg(item, patron, headers)
    else:
        patronNext = r'<a class="nextpostslink" rel="next" href="([^"]+)">'
        patron = r'<div class="mediaWrap mediaWrapAlt">\s?<a href="(?P<url>[^"]+)"(?:[^>]+>|)>?\s?<img[^s]+src="([^"]+)"[^>]+>\s?<\/a>[^>]+>[^>]+>[^>]+>(?P<title>.+?)(?:[ ]<lang>[sSuUbB\-iItTaA]+)?(?:[ ]?\((?P<year>[\-\d+]+)\)).[^<]+[^>]+><\/a>.+?<p>\s*(?P<quality>[a-zA-Z-0-9\.]+)\s*<\/p>[^>]+>'
        patronBlock = r'<div id="main_col">(?P<block>.*?)<!\-\- main_col \-\->'

    if item.args != 'all' and item.args != 'search':
        action = 'findvideos' if item.extra == 'movie' else 'episodios'
        item.contentType = 'movie' if item.extra == 'movie' else 'tvshow'

    #debug = True
    return locals()

@support.scrape
def episodios(item):
    log()

    if not item.data:
        data_check = httptools.downloadpage(item.url, headers=headers).data
        data_check = re.sub('\n|\t', ' ', data_check)
        data_check = re.sub(r'>\s+<', '> <', data_check)
    else:
        data_check = item.data
    patron_check = r'<iframe src="([^"]+)" scrolling="no" frameborder="0" width="626" height="550" allowfullscreen="true" webkitallowfullscreen="true" mozallowfullscreen="true">'
    item.url = scrapertools.find_single_match(data_check, patron_check)

    patronBlock = r'Stagioni<\/a>.*?<ul class="nav navbar-nav">(?P<block>.*?)<\/ul>'
    patron = r'<a href="(?P<url>[^"]+)"\s*>\s*<i[^>]+><\/i>\s*(?P<episode>\d+)<\/a>'
    # debug = True

    def itemlistHook(itemlist):
        retItemlist = []
        for item in itemlist:
            item.contentType = 'episode'

            season = unify.remove_format(item.title)
            season_data = httptools.downloadpage(item.url).data
            season_data = re.sub('\n|\t', ' ', season_data)
            season_data = re.sub(r'>\s+<', '> <', season_data)
            block = scrapertools.find_single_match(season_data, 'Episodi.*?<ul class="nav navbar-nav">(.*?)</ul>')
            episodes = scrapertools.find_multiple_matches(block, '<a href="([^"]+)"\s*>\s*<i[^>]+><\/i>\s*(\d+)<\/a>')
            for url, episode in episodes:
                i = item.clone()
                i.action = 'findvideos'
                i.url = url
                i.title = str(season) + 'x' + str(episode)
                retItemlist.append(i)

        return retItemlist

    #debug = True
    return locals()

def category(item):
    log()

    blacklist = ['Serie TV Altadefinizione', 'HD AltaDefinizione', 'Al Cinema', 'Serie TV', 'Miniserie', 'Programmi Tv', 'Live', 'Trailers', 'Serie TV Aggiornate', 'Aggiornamenti', 'Featured']
    itemlist = support.scrape(item, '<li><a href="([^"]+)"><span></span>([^<]+)</a></li>', ['url', 'title'], headers, blacklist, patron_block='<ul class="table-list">(.*?)</ul>', action='peliculas')
    return support.thumb(itemlist)

def anime(item):
    log()
    itemlist = []

    seasons = support.match(item, patron=r'<div class="sp-body[^"]+">(.*?)<\/div>').matches
    for season in seasons:
        episodes = scrapertools.find_multiple_matches(season, r'<a.*?href="([^"]+)"[^>]+>([^<]+)<\/a>(.*?)<(:?br|\/p)')
        for url, title, urls, none in episodes:
            urls = scrapertools.find_multiple_matches(urls, '<a.*?href="([^"]+)"[^>]+>')

            for url2 in urls:
                url += url2 + '\n'

            #log('EP URL',url)

            itemlist.append(
                Item(channel=item.channel,
                     action="findvideos",
                     contentType=item.contentType,
                     title=support.typo(title + ' - ' + item.fulltitle,'bold'),
                     url=url,
                     fulltitle=title + ' - ' + item.show,
                     show=item.show,
                     thumbnail=item.thumbnail,
                     args=item.args))

    autorenumber.renumber(itemlist, item,'bold')
    support.videolibrary(itemlist, item, 'color kod bold')

    return itemlist

def search(item, texto):
    log(texto)


    item.url = host + "/?s=" + texto
    try:
        item.args = 'search'
        return peliculas(item)

    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


##def search_peliculas(item):
##    log()
##    itemlist = []
##
##    action = 'findvideos' if item.extra == 'movie' else 'episodios'
##
##    data = httptools.downloadpage(item.url, headers=headers, ignore_response_code=True).data.replace('\t','').replace('\n','')
##    log(data)
##    patron = r'<a href="([^"]+)" title="Permalink to\s([^"]+) \(([^<]+)\).*?".*?<img[^s]+src="([^"]+)".*?<div class="calitate">\s*<p>([^<]+)<\/p>'
##    matches = re.compile(patron, re.MULTILINE).findall(data)
##
##    for url, title, year, thumb, quality in matches:
##        infoLabels = {}
##        infoLabels['year'] = year
##        title = scrapertools.decodeHtmlentities(title)
##        quality = scrapertools.decodeHtmlentities(quality)
##        longtitle = title + support.typo(quality,'_ [] color kod')
##        itemlist.append(
##            Item(channel=item.channel,
##                 action=action,
##                 contentType=item.contentType,
##                 fulltitle=title,
##                 show=title,
##                 title=longtitle,
##                 url=url,
##                 thumbnail=thumb,
##                 infoLabels=infoLabels,
##                 args=item.args))
##
##    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
##
##    return itemlist


def newest(categoria):
    log()
    itemlist = []
    item = Item()
    item.url = host +'/aggiornamenti/'

    matches = support.match(item, patron=r'mediaWrapAlt recomended_videos"[^>]+>\s*<a href="([^"]+)" title="([^"]+)" rel="bookmark">\s*<img[^s]+src="([^"]+)"[^>]+>').matches

    for url, title, thumb in matches:
        title = scrapertools.decodeHtmlentities(title).replace("Permalink to ", "").replace("streaming", "")
        title = re.sub(r'\s\(\d+\)','',title)
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 contentType="movie",
                 fulltitle=title,
                 show=title,
                 title=support.typo(title, 'bold'),
                 url=url,
                 thumbnail=thumb,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist

def findvideos(item):
    log()
    listurl = set()
    # itemlist = []
    support.log("ITEMLIST: ", item)
##    if item.args == 'anime':
##        data = item.url
##    else:
##        data = httptools.downloadpage(item.url, headers=headers).data
    data = support.match(item.url, headers=headers).data

    data = re.sub('\n|\t', ' ', data)
    data = re.sub(r'>\s+<', '> <', data)
    check = support.match(data, patron=r'<div class="category-film">\s+<h3>\s+(.*?)\s+</h3>\s+</div>').match
    if 'sub' in check.lower():
        item.contentLanguage = 'Sub-ITA'
    support.log("CHECK : ", check)
    if 'anime' in check.lower():
        item.contentType = 'tvshow'
        item.data = data
        support.log('select = ### è una anime ###')
        return episodios(item)
    elif 'serie' in check.lower():
        item.contentType = 'tvshow'
        item.data = data
        return episodios(item)

    if 'protectlink' in data:
        urls = scrapertools.find_multiple_matches(data, r'<iframe src="[^=]+=(.*?)"')
        support.log("SONO QUI: ", urls)
        for url in urls:
            url = url.decode('base64')
            # tiro via l'ultimo carattere perchè non c'entra
            url, c = unshorten_only(url)
            if 'nodmca' in url:
                page = httptools.downloadpage(url, headers=headers).data
                url = '\t' + scrapertools.find_single_match(page, '<meta name="og:url" content="([^=]+)">')
            if url:
                listurl.add(url)
    data += '\n'.join(listurl)
    return support.server(item, data)#, headers=headers)
    # return itemlist

##def findvideos(item):
##    log()
##
##    # Carica la pagina
##    data = item.url if item.contentType == "episode" else httptools.downloadpage(item.url, headers=headers).data
##
##    if 'protectlink' in data:
##        urls = scrapertools.find_multiple_matches(data, r'<iframe src="[^=]+=(.*?)"')
##        for url in urls:
##            url = url.decode('base64')
##            data += '\t' + url
##            url, c = unshorten_only(url)
##            data += '\t' + url
##
##    itemlist = servertools.find_video_items(data=data)
##
##    for videoitem in itemlist:
##        videoitem.title = item.title + videoitem.title
##        videoitem.fulltitle = item.fulltitle
##        videoitem.thumbnail = item.thumbnail
##        videoitem.show = item.show
##        videoitem.plot = item.plot
##        videoitem.channel = item.channel
##        videoitem.contentType = item.contentType
####        videoitem.language = IDIOMAS['Italiano']
##
####    # Requerido para Filtrar enlaces
####
####    if __comprueba_enlaces__:
####        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)
####
####    # Requerido para FilterTools
####
####    itemlist = filtertools.get_links(itemlist, item, list_language)
####
####    # Requerido para AutoPlay
####
####    autoplay.start(itemlist, item)
##
##    if item.contentType != 'episode':
##        if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
##            itemlist.append(
##                Item(channel=item.channel, title='[COLOR yellow][B]Aggiungi alla videoteca[/B][/COLOR]', url=item.url,
##                     action="add_pelicula_to_library", extra="findvideos", contentTitle=item.contentTitle))
##
##    # Estrae i contenuti
##    patron = r'\{"file":"([^"]+)","type":"[^"]+","label":"([^"]+)"\}'
##    matches = re.compile(patron, re.DOTALL).findall(data)
##    for scrapedurl, scrapedtitle in matches:
##        title = item.title + " " + scrapedtitle + " quality"
##        itemlist.append(
##            Item(channel=item.channel,
##                 action="play",
##                 title=title,
##                 url=scrapedurl.replace(r'\/', '/').replace('%3B', ';'),
##                 thumbnail=item.thumbnail,
##                 fulltitle=item.title,
##                 show=item.title,
##                 server='',
##                 contentType=item.contentType,
##                 folder=False))
##
##    return itemlist
