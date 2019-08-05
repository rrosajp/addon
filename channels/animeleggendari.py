# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per animeleggendari
# ------------------------------------------------------------

import re

from core import servertools, httptools, scrapertoolsV2, tmdb, support
from core.item import Item
from core.support import log, menu
from lib.js2py.host import jsfunctions
from platformcode import logger, config
from specials import autoplay, autorenumber

__channel__ = "animeleggendari"
host = config.get_channel_url(__channel__)

headers = [['User-Agent', 'Mozilla/50.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0'],
           ['Referer', host]]

list_servers = ['verystream','openload','rapidvideo','streamango']
list_quality = ['default']

checklinks = config.get_setting('checklinks', 'animeleggendari')
checklinks_number = config.get_setting('checklinks_number', 'animeleggendari')

                                       
@support.menu
def mainlist(item):

    anime = ''
    animeSub = [
        ('Leggendari', ['/category/anime-leggendari/', 'peliculas']),
        ('ITA', ['/category/anime-ita/', 'peliculas']),
        ('SUB-ITA', ['/category/anime-sub-ita/', 'peliculas']),
        ('Conclusi', ['/category/serie-anime-concluse/', 'peliculas']),
        ('in Corso', ['/category/anime-in-corso/', 'peliculas']),
        ('Genere', ['', 'genres'])
    ]

    return locals()


def search(item, texto):
    log(texto)
    
    item.url = host + "/?s=" + texto
    try:
        return peliculas(item)

    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []

@support.scrape
def last_ep(item):
    log('ANIME PER TUTTI')

    action = 'findvideos'
    patron = r'<a href="(?P<url>[^"]+)">(?P<title>[^<]+)<'
    patron_block = r'<ul class="mh-tab-content-posts">(.*?)<\/ul>'

def newest(categoria):
    log('ANIME PER TUTTI')
    log(categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "anime":
            item.url = host
            item.action = "last_ep"
            itemlist = last_ep(item)

            if itemlist[-1].action == "last_ep":
                itemlist.pop()
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist

@support.scrape
def genres(item):
    log()

    action = 'peliculas'
    blacklist = ['Contattaci','Privacy Policy', 'DMCA']
    patron = r'<a href="(?P<url>[^"]+)">(?P<title>[^<]+)<'
    patron_block = r'Generi.*?<ul.*?>(.*?)<\/ul>'
    return locals()

def peliculas(item):
    log()
    itemlist = []

    blacklist = ['top 10 anime da vedere']
    matches, data = support.match(item, r'<a class="[^"]+" href="([^"]+)" title="([^"]+)"><img[^s]+src="([^"]+)"[^>]+')

    for url, title, thumb in matches:
        title = scrapertoolsV2.decodeHtmlentities(title.strip()).replace("streaming", "")
        lang = scrapertoolsV2.find_single_match(title, r"((?:SUB ITA|ITA))")
        videoType = ''
        if 'movie' in title.lower():
            videoType = ' - (MOVIE)'
        if 'ova' in title.lower():
            videoType = ' - (OAV)'

        cleantitle = title.replace(lang, "").replace('(Streaming & Download)', '').replace('( Streaming & Download )', '').replace('OAV', '').replace('OVA', '').replace('MOVIE', '').strip()

        if not videoType :
            contentType="tvshow"
            action="episodios"
        else:
            contentType="movie"
            action="findvideos"

        if not title.lower() in blacklist:
            itemlist.append(
                Item(channel=item.channel,
                    action=action,
                    contentType=contentType,
                    title=support.typo(cleantitle + videoType, 'bold') + support.typo(lang,'_ [] color kod'),
                    fulltitle=cleantitle,
                    show=cleantitle,
                    url=url,
                    thumbnail=thumb))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    autorenumber.renumber(itemlist)
    support.nextPage(itemlist, item, data, r'<a class="next page-numbers" href="([^"]+)">')

    return itemlist

def episodios(item):
    log()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    block = scrapertoolsV2.find_single_match(data, r'(?:<p style="text-align: left;">|<div class="pagination clearfix">\s*)(.*?)</span></a></div>')

    itemlist.append(
        Item(channel=item.channel,
             action='findvideos',
             contentType='episode',
             title=support.typo('Episodio 1 bold'),
             fulltitle=item.title,
             url=item.url,
             thumbnail=item.thumbnail))

    if block:
        matches = re.compile(r'<a href="([^"]+)".*?><span class="pagelink">(\d+)</span></a>', re.DOTALL).findall(data)
        for url, number in matches:
            itemlist.append(
                Item(channel=item.channel,
                     action='findvideos',
                     contentType='episode',
                     title=support.typo('Episodio ' + number,'bold'),
                     fulltitle=item.title,
                     url=url,
                     thumbnail=item.thumbnail))

    autorenumber.renumber(itemlist, item)
    support.videolibrary
    return itemlist

def findvideos(item):
    log()
    data = ''
    matches = support.match(item, 'str="([^"]+)"')[0]
    if matches:
        for match in matches:
            data += str(jsfunctions.unescape(re.sub('@|g','%', match)))
            data += str(match)
            log('DATA',data)
            if 'animepertutti' in data:
                log('ANIMEPERTUTTI!')

    else:
        data = ''

    itemlist = support.server(item,data)

    if checklinks:
        itemlist = servertools.check_list_links(itemlist, checklinks_number)

    # itemlist = filtertools.get_links(itemlist, item, list_language)
    autoplay.start(itemlist, item)

    return itemlist
