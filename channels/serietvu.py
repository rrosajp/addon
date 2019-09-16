# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per SerieTVU
# Thanks to Icarus crew & Alfa addon & 4l3x87
# ----------------------------------------------------------

"""
    Trasformate le sole def per support.menu e support.scrape
    da non inviare nel test.
    Test solo a trasformazione completa

"""
import re

from core import tmdb, scrapertools, support
from core.item import Item
from core.support import log
from platformcode import config, logger

__channel__ = 'serietvu'
host = config.get_channel_url(__channel__)
headers = [['Referer', host]]

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['speedvideo']
list_quality = ['default']


@support.menu
def mainlist(item):
    log()
    tvshow = ['/category/serie-tv',
              ('Novità', ['/ultimi-episodi', 'latestep']),
              ('Categorie', ['', 'categorie'])
    ]

    return locals()


# ----------------------------------------------------------------------------------------------------------------
def cleantitle(scrapedtitle):
    log()
    scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle.strip())
    scrapedtitle = scrapedtitle.replace('[HD]', '').replace('’', '\'').replace('– Il Trono di Spade', '').replace(
        'Flash 2014', 'Flash').replace('"', "'")
    year = scrapertools.find_single_match(scrapedtitle, '\((\d{4})\)')
    if year:
        scrapedtitle = scrapedtitle.replace('(' + year + ')', '')

    return scrapedtitle.strip()


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def peliculas(item):
    log()
    itemlist = []

    patron = r'<div class="item">\s*<a href="([^"]+)" data-original="([^"]+)" class="lazy inner">'
    patron += r'[^>]+>[^>]+>[^>]+>[^>]+>([^<]+)<'
    matches, data = support.match(item, patron, headers=headers)

    for scrapedurl, scrapedimg, scrapedtitle in matches:
        infoLabels = {}
        year = scrapertools.find_single_match(scrapedtitle, '\((\d{4})\)')
        if year:
            infoLabels['year'] = year
        scrapedtitle = cleantitle(scrapedtitle)

        itemlist.append(
            Item(channel=item.channel,
                 action="episodios",
                 title=scrapedtitle,
                 fulltitle=scrapedtitle,
                 url=scrapedurl,
                 thumbnail=scrapedimg,
                 show=scrapedtitle,
                 infoLabels=infoLabels,
                 contentType='episode',
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    # Pagine
    support.nextPage(itemlist, item, data, '<li><a href="([^"]+)">Pagina successiva')

    return itemlist


# ================================================================================================================


# ----------------------------------------------------------------------------------------------------------------
def episodios(item):
    log()
    itemlist = []

    patron = r'<option value="(\d+)"[\sselected]*>.*?</option>'
    matches, data = support.match(item, patron, headers=headers)

    for value in matches:
        patron = r'<div class="list [active]*" data-id="%s">(.*?)</div>\s*</div>' % value
        blocco = scrapertools.find_single_match(data, patron)
        log(blocco)
        patron = r'(<a data-id="\d+[^"]*" data-href="([^"]+)"(?:\sdata-original="([^"]+)")?\sclass="[^"]+">)[^>]+>[^>]+>([^<]+)<'
        matches = scrapertools.find_multiple_matches(blocco, patron)

        for scrapedextra, scrapedurl, scrapedimg, scrapedtitle in matches:
            contentlanguage = ''
            if 'sub-ita' in scrapedtitle.lower():
                contentlanguage = 'Sub-ITA'
                scrapedtitle = scrapedtitle.replace(contentlanguage, '')

            number = cleantitle(scrapedtitle.replace("Episodio", "")).strip()

            title = value + "x" + number.zfill(2)
            title += " "+support.typo(contentlanguage, '_ [] color kod') if contentlanguage else ''

            infoLabels = {}
            infoLabels['episode'] = number.zfill(2)
            infoLabels['season'] = value

            itemlist.append(
                Item(channel=item.channel,
                     action="findvideos",
                     title=title,
                     fulltitle=scrapedtitle,
                     contentType="episode",
                     url=scrapedurl,
                     thumbnail=scrapedimg,
                     extra=scrapedextra,
                     infoLabels=infoLabels,
                     folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    support.videolibrary(itemlist, item, 'bold color kod')

    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def findvideos(item):
    log()
    return support.server(item, data=item.url)



# ================================================================================================================


# ----------------------------------------------------------------------------------------------------------------
def findepisodevideo(item):
    log()

    patron_block = r'<div class="list [active]*" data-id="%s">(.*?)</div>\s*</div>' % item.extra[0][0]
    patron = r'<a data-id="%s[^"]*" data-href="([^"]+)"(?:\sdata-original="[^"]+")?\sclass="[^"]+">' % item.extra[0][1].lstrip("0")
    matches = support.match(item, patron, patron_block, headers)[0]
    data = ''
    if len(matches) > 0:
        data = matches[0]
    item.contentType = 'movie'
    return support.server(item, data=data)


# ================================================================================================================


# ----------------------------------------------------------------------------------------------------------------
def latestep(item):
    log()
    itemlist = []
    titles = []

    patron_block = r"Ultimi episodi aggiunti.*?<h2>"
    patron = r'<a href="([^"]*)"\sdata-src="([^"]*)"\sclass="owl-lazy.*?".*?class="title">(.*?)<small>\((\d*?)x(\d*?)\s(Sub-Ita|Ita)'
    matches = support.match(item, patron, patron_block, headers, host)[0]

    for scrapedurl, scrapedimg, scrapedtitle, scrapedseason, scrapedepisode, scrapedlanguage in matches:
        infoLabels = {}
        year = scrapertools.find_single_match(scrapedtitle, '\((\d{4})\)')
        if year:
            infoLabels['year'] = year
        infoLabels['episode'] = scrapedepisode
        infoLabels['season'] = scrapedseason
        episode = scrapedseason + "x" + scrapedepisode

        scrapedtitle = cleantitle(scrapedtitle)
        title = scrapedtitle + " - " + episode
        contentlanguage = ""
        if scrapedlanguage.strip().lower() != 'ita':
            title += " "+support.typo("Sub-ITA", '_ [] color kod')
            contentlanguage = 'Sub-ITA'

        titles.append(title)
        itemlist.append(
            Item(channel=item.channel,
                 action="findepisodevideo",
                 title=title,
                 fulltitle=title,
                 url=scrapedurl,
                 extra=[[scrapedseason, scrapedepisode]],
                 thumbnail=scrapedimg,
                 contentSerieName=scrapedtitle,
                 contentLanguage=contentlanguage,
                 contentType='episode',
                 infoLabels=infoLabels,
                 folder=True))

    patron = r'<div class="item">\s*<a href="([^"]+)" data-original="([^"]+)" class="lazy inner">'
    patron += r'[^>]+>[^>]+>[^>]+>[^>]+>([^<]+)<small>([^<]+)<'
    matches = support.match(item, patron, headers=headers)[0]

    for scrapedurl, scrapedimg, scrapedtitle, scrapedinfo in matches:
        infoLabels = {}
        year = scrapertools.find_single_match(scrapedtitle, '\((\d{4})\)')
        if year:
            infoLabels['year'] = year
        scrapedtitle = cleantitle(scrapedtitle)

        infoLabels['tvshowtitle'] = scrapedtitle

        episodio = re.compile(r'(\d+)x(\d+)', re.DOTALL).findall(scrapedinfo)
        infoLabels['episode'] = episodio[0][1]
        infoLabels['season'] = episodio[0][0]

        episode = infoLabels['season'] + "x" + infoLabels['episode']
        title = "%s - %s" % (scrapedtitle, episode)
        title = title.strip()
        contentlanguage = ""
        if 'sub-ita' in scrapedinfo.lower():
            title += " "+support.typo("Sub-ITA", '_ [] color kod')
            contentlanguage = 'Sub-ITA'

        if title in titles: continue
        itemlist.append(
            Item(channel=item.channel,
                 action="findepisodevideo",
                 title=title,
                 fulltitle=title,
                 url=scrapedurl,
                 extra=episodio,
                 thumbnail=scrapedimg,
                 contentSerieName=scrapedtitle,
                 contentLanguage=contentlanguage,
                 infoLabels=infoLabels,
                 contentType='episode',
                 folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
def newest(categoria):
    log(categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "series":
            item.url = host + "/ultimi-episodi"
            item.action = "latestep"
            itemlist = latestep(item)

            if itemlist[-1].action == "latestep":
                itemlist.pop()

    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
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


# ================================================================================================================

# ----------------------------------------------------------------------------------------------------------------
@support.scrape
def categorie(item):
    log()

    blacklist = ["Home Page", "Calendario Aggiornamenti"]
    action = 'peliculas'
    patronBlock = r'<h2>Sfoglia</h2>\s*<ul>(?P<block>.*?)</ul>\s*</section>'
    patron = r'<li><a href="(?P<url>[^"]+)">(?P<title>[^<]+)</a></li>'
    debug = True

    return locals()

# ================================================================================================================
