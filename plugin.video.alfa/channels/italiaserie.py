# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per italiaserie
# ------------------------------------------------------------
import re

import autoplay
import filtertools
import support
from core import httptools, scrapertools
from core import tmdb
from core.item import Item
from platformcode import logger

host = "https://italiaserie.org"

list_servers = ['speedvideo']

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()


def mainlist(item):
    support.log()
    itemlist = []

    support.menu(itemlist, 'Ultime Uscite', 'peliculas', host + "/category/serie-tv/", "episode")
    # page not working
    # support.menu(itemlist, 'Ultimi Episodi', 'peliculas', host + "/ultimi-episodi/", "episode", 'latest')
    support.menu(itemlist, 'Ultimi Episodi', 'peliculas', host, "episode", 'latest')
    support.menu(itemlist, 'Categorie', 'menu', host, "episode", args="Serie-Tv per Genere")
    support.menu(itemlist, 'Cerca...', 'search', host, 'episode', args='serie')

    autoplay.init(item.channel, list_servers, [])
    autoplay.show_option(item.channel, itemlist)

    return itemlist


def newest(categoria):
    logger.info("[italiaserie.py]==> newest" + categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "series":
            item.url = host + "/ultimi-episodi/"
            item.action = "peliculas"
            item.args = "latest"
            item.contentType = "episode"
            itemlist = peliculas(item)

            if itemlist[-1].action == "peliculas":
                itemlist.pop()

    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def peliculas(item):
    support.log()
    patron = r'<div class="post-thumb">\s*<a href="([^"]+)" title="([^"]+)">\s*<img src="([^"]+)"[^>]+>'
    list_groups = ["url", "title", "thumb"]

    if item.args == "latest":
        patron += r'.*?aj-eps">(.*?)</span>'
        data = httptools.downloadpage(item.url).data

        # remove when /ultimi-episodi page will work again
        block = scrapertools.find_single_match(data, r'<ul class="recent-posts">(.*?)<\/ul>')

        matches = re.compile(patron, re.S).findall(block)
        itemlist = []

        for scrapedurl, scrapedtitle, scrapedthumbnail, scrapedep in matches:
            s, ep = scrapertools.find_single_match(scrapedep, r'(\d+)x(\d+)\s')
            itemlist.append(
                Item(channel=item.channel,
                     action="seasons",
                     contentType=item.contentType,
                     title="[B]" + scrapedtitle + "[/B] " + scrapedep,
                     fulltitle=scrapedtitle,
                     show=scrapedtitle,
                     url=scrapedurl,
                     extra=item.extra,
                     args={"season": s, "episode": ep}
                     ))

        tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
        return itemlist
    else:
        patron_next = r'<a class="next page-numbers" href="(.*?)">'
        return support.scrape(item, patron, list_groups, patronNext=patron_next, action="seasons")


def search(item, texto):
    support.log("s=", texto)
    item.url = host + "/?s=" + texto
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def menu(item):
    support.log()
    patron = r'<li class="cat-item.*?href="([^"]+)".*?>(.*?)</a>'
    return support.scrape(item, patron, ["url", "title"], action="peliculas")


def seasons(item):
    support.log()

    patron = r'<div class="su-spoiler.*?</i>(.*?)</div>\s+<div class="su-spoiler-content"(.*?)="clearfix">'
    itemlist = support.scrape(item, patron, ["title", "url"], action="episodios")

    if item.args:
        s = item.args["season"]
        s = (int(s) - 1)
        lastitem = itemlist[s]
        lastitem.args = {"episode": item.args["episode"]}

        return episodios(lastitem)

    return itemlist[:-1]


def episodios(item):
    support.log()
    season = item.fulltitle

    patron = r'<div class="su-link-ep">\s+<a.*?href="([^"]+)".*?strong>(.*?)</'
    if item.args:
        ep = int(item.args["episode"])
        patron = r'<div class="su-link-ep">\s+<a.*?href="([^"]+)".*?strong>\s(Episodio ' + str(ep) + r') .*?</'

    itemlist = support.scrape(item, patron, ["url", "title"], data=item.url)

    if item.args:
        itemlist = itemlist[:-1]

    for it in itemlist:
        if it.action == "findvideos":
            season_n = season.lower().replace("stagione", "").strip()
            ep_n = scrapertools.find_single_match(it.title, r'Episodio\s+(\d+)')
            it.title = season_n + "x" + str(ep_n).zfill(2) + re.sub(r"Episodio\s+" + ep_n, "", it.title)

    return itemlist


def findvideos(item):
    support.log()

    itemlist = support.server(item, data=item.url)
    itemlist = filtertools.get_links(itemlist, item, list_language)

    autoplay.start(itemlist, item)

    return itemlist
