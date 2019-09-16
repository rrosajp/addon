# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per italiaserie
# ------------------------------------------------------------
"""

"""
import re

from core import httptools, scrapertools, support
from core.item import Item
from platformcode import config

__channel__ = 'italiaserie'
host = config.get_channel_url(__channel__)

list_servers = ['speedvideo']
list_quality = []


@support.menu
def mainlist(item):
    support.log()

    tvshow = ['/category/serie-tv/',
        ('Aggiornamenti', ['/ultimi-episodi/', 'peliculas', 'latest']),
        ('Generi', ['', 'category', 'Serie-Tv per Genere'])
        ]

    return locals()


@support.scrape
def peliculas(item):
    support.log()

    action = 'episodios'
    patron = r'<div class="post-thumb">\s*<a href="(?P<url>[^"]+)" '\
             'title="(?P<title>[^"]+)">\s*<img src="(?P<thumb>[^"]+)"[^>]+>'

    if item.args == "latest":
        patron += r'.*?aj-eps">(?P<episode>.+?)[ ]?(?P<lang>Sub-Ita|Ita)</span>'
    patronNext = r'<a class="next page-numbers" href="(.*?)">'

##    debug = True
    return locals()


@support.scrape
def category(item):
    support.log()

    action = 'peliculas'
    patron = r'<li class="cat-item.*?href="(?P<url>[^"]+)".*?>(?P<title>.*?)</a>'

    return locals()


@support.scrape
def episodios(item):
    support.log()
    pagination = 24

    patronBlock = r'</i> Stagione (?P<block>(?P<season>\d+)</div> '\
                  '<div class="su-spoiler-content".*?)<div class="clearfix">'
    patron = r'(?:(?P<season>\d+)?</div> <div class="su-spoiler-content"(:?.+?)?> )?'\
             '<div class="su-link-ep">\s+<a.*?href="(?P<url>[^"]+)".*?strong>[ ]'\
             '(?P<title>.+?)[ ](?P<episode>\d+-\d+|\d+)[ ](?:-\s+(?P<title2>.+?))?'\
             '[ ]?(?:(?P<lang>Sub-ITA))?[ ]?</strong>'

    return locals()


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


def newest(categoria):
    support.log("newest", categoria)
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


def findvideos(item):
    support.log()
    return support.server(item, data=item.url)
