# -*- coding: utf-8 -*-
# Ringraziamo Icarus crew
# ------------------------------------------------------------
# XBMC Plugin
# Canale per http://bleachportal.it
# ------------------------------------------------------------

import re

from core import scrapertools, httptools
from core.item import Item
from platformcode import logger
from platformcode import config
from core import support

host = "http://www.bleachportal.it"


def mainlist(item):
    logger.info("[BleachPortal.py]==> mainlist")
    itemlist = [Item(channel=item.channel,
                     action="episodi",
                     title= support.typo('Bleach','bold'),
                     url=host + "/streaming/bleach/stream_bleach.htm",
                     thumbnail="https://www.thetvdb.com/banners/posters/74796-14.jpg",
                     banner="https://www.thetvdb.com/banners/graphical/74796-g6.jpg",
                     fanart="https://www.thetvdb.com/banners/fanart/original/74796-30.jpg",
                     extra="bleach"),
                Item(channel=item.channel,
                     action="episodi",
                     title=support.typo('D.Gray Man','bold'),
                     url=host + "/streaming/d.gray-man/stream_dgray-man.htm",
                     thumbnail="https://www.thetvdb.com/banners/posters/79635-1.jpg",
                     banner="https://www.thetvdb.com/banners/graphical/79635-g4.jpg",
                     fanart="https://www.thetvdb.com/banners/fanart/original/79635-6.jpg",
                     extra="dgrayman")]

    return itemlist


def episodi(item):
    logger.info("[BleachPortal.py]==> episodi")
    itemlist = []

    data = httptools.downloadpage(item.url).data
    patron = r'<td>?[<span\s|<width="\d+%"\s]+?class="[^"]+">\D+([\d\-]+)\s?<[^<]+<[^<]+<[^<]+<[^<]+<.*?\s+?.*?<span style="[^"]+">([^<]+).*?\s?.*?<a href="\.*(/?[^"]+)">'
    matches = re.compile(patron, re.DOTALL).findall(data)

    animetitle = "Bleach" if item.extra == "bleach" else "D.Gray Man"
    for scrapednumber, scrapedtitle, scrapedurl in matches:
        scrapedtitle = scrapedtitle.decode('latin1').encode('utf8')
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 title=support.typo("%s Episodio %s" % (animetitle, scrapednumber),'bold'),
                 url=item.url.replace("stream_bleach.htm",scrapedurl) if "stream_bleach.htm" in item.url else item.url.replace("stream_dgray-man.htm", scrapedurl),
                 plot=scrapedtitle,
                 extra=item.extra,
                 thumbnail=item.thumbnail,
                 fanart=item.fanart,
                 fulltitle="%s Ep: %s | %s" % (animetitle, scrapednumber, scrapedtitle)))

    if item.extra == "bleach":
        itemlist.append(
            Item(channel=item.channel,
                 action="oav",
                 title=support.typo("OAV e Movies",'bold color kod'),
                 url=item.url.replace("stream_bleach.htm", "stream_bleach_movie_oav.htm"),
                 extra=item.extra,
                 thumbnail=item.thumbnail,
                 fanart=item.fanart))

    return list(reversed(itemlist))


def oav(item):
    logger.info("[BleachPortal.py]==> oav")
    itemlist = []

    data = httptools.downloadpage(item.url).data
    patron = r'<td>?[<span\s|<width="\d+%"\s]+?class="[^"]+">-\s+(.*?)<[^<]+<[^<]+<[^<]+<[^<]+<.*?\s+?.*?<span style="[^"]+">([^<]+).*?\s?.*?<a href="\.*(/?[^"]+)">'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapednumber, scrapedtitle, scrapedurl in matches:
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 title=support.typo(scrapednumber, 'bold'),
                 url=item.url.replace("stream_bleach_movie_oav.htm", scrapedurl),
                 plot=scrapedtitle,
                 extra=item.extra,
                 thumbnail=item.thumbnail,
                 fulltitle=scrapednumber + " | " + scrapedtitle))

    return list(reversed(itemlist))


def findvideos(item):
    logger.info("[BleachPortal.py]==> findvideos")
    itemlist = []

    if "bleach//" in item.url:
        item.url = re.sub(r'\w+//', "", item.url)

    data = httptools.downloadpage(item.url).data

    if "bleach" in item.extra:
        video = scrapertools.find_single_match(data, 'file: "(.*?)",')
    else:
        video = scrapertools.find_single_match(data, 'file=(.*?)&').rsplit('/', 1)[-1]

    itemlist.append(
        Item(channel=item.channel,
             action="play",
             title="Diretto %s" % item.title,
             url=item.url.replace(item.url.split("/")[-1], "/" + video),
             thumbnail=item.thumbnail,
             fulltitle=item.fulltitle))
    return itemlist
