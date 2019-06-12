# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale netlovers
# ------------------------------------------------------------

import re
import urllib
from channelselector import get_thumb
from core import httptools, scrapertools, support, tmdb
from core.item import Item
from platformcode import logger, config

host = "https://www.netflixlovers.it"

TIMEOUT_TOTAL = 60


def mainlist(item):
    logger.info(" mainlist")
    itemlist = [Item(channel=item.channel,
                     title="Novità",
                     action="get_info",
                     url="%s/novita-su-netflix" % host,
                     thumbnail=item.thumbnail),
               Item(channel=item.channel,
                     title="Prossimamente",
                     action="ratings",
                     url="%s/prossimamente-su-netflix" % host,
                     thumbnail=item.thumbnail),
                Item(channel=item.channel,
                     title="Meglio del Mese",
                     action="ratings",
                     url="%s/classifiche/questo-mese" % host,
                     thumbnail=item.thumbnail),
                Item(channel=item.channel,
                     title="Migliori Film",
                     action="ratings",
                     url="%s/classifiche/film" % host,
                     thumbnail=item.thumbnail),
                Item(channel=item.channel,
                     title="Migliori Serie",
                     action="ratings",
                     url="%s/classifiche/migliori-serie-tv-su-netflix" % host,
                     thumbnail=item.thumbnail),
                Item(channel=item.channel,
                     title="Migliori Documentari",
                     action="ratings",
                     url="%s/classifiche/documentari" % host,
                     thumbnail=item.thumbnail)]

    return itemlist


def get_info(item):
    logger.info("filmontv tvoggi")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data
    patron = r'<div class=moviecard>[a-z \n<>\/="_\-:0-9;A-Z.?!\'\&]*img src="([a-zA-Z:\/\.0-9\-_]*)[a-z \n<>\/="_\-:0-9;A-Z.?!\'\&]*alt="([A-Za-z ,:0-9\.À-ÖØ-öø-ÿ\-\']*)[a-z \n<>\/="_\-:0-9;A-Z.?!\'\&,#]*<p>([A-Za-z ,0-9\.À-ÖØ-öø-ÿ\-\']*)'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedthumbnail, scrapedtitle, scrapedinfo in matches:
    # for scrapedthumbnail, scrapedtitle, scrapedtv in matches:
        scrapedurl = ""
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()
        infoLabels = {}
        infoLabels["plot"] = scrapedinfo
        itemlist.append(
            Item(channel=item.channel,
                 action="do_search",
                 extra=urllib.quote_plus(scrapedtitle) + '{}' + 'movie',
                 title="[B]" + scrapedtitle + "[/B]",
                 fulltitle="[B]" + scrapedtitle + "[/B]",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 contentTitle=scrapedtitle,
                 contentType='movie',
                 infoLabels=infoLabels,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


def ratings(item):
    logger.info("filmontv tvoggi")
    itemlist = []

    # Carica la pagina 
    data = httptools.downloadpage(item.url).data
    patron = r'<div class=thumb>[a-z \n<>\/="_\-:0-9;A-Z.?!\'\&]*img src="([a-zA-Z:\/\.0-9\-_]*)[a-z \n<>\/="_\-:0-9;A-Z.?!\'\&]*alt="([A-Za-z ,0-9:\.À-ÖØ-öø-ÿ\-\']*)[a-z \n<>\/="_\-:0-9;A-Z.?!\'\&,#]*<p>([A-Za-z ,0-9\.À-ÖØ-öø-ÿ\-\']*)'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedthumbnail, scrapedtitle, scrapedinfo in matches:
    # for scrapedthumbnail, scrapedtitle, scrapedtv in matches:
        scrapedurl = ""
        scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).strip()
        infoLabels = {}
        infoLabels["plot"] = scrapedinfo
        itemlist.append(
            Item(channel=item.channel,
                 action="do_search",
                 extra=urllib.quote_plus(scrapedtitle) + '{}' + 'movie',
                 title="[B]" + scrapedtitle + "[/B]",
                 fulltitle="[B]" + scrapedtitle + "[/B]",
                 url=scrapedurl,
                 thumbnail=scrapedthumbnail,
                 contentTitle=scrapedtitle,
                 contentType='movie',
                 infoLabels=infoLabels,
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist



def do_search(item):
    from specials import search
    return search.do_search(item)
