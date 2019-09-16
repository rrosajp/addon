# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per MondoLunatico 2.0
# ------------------------------------------------------------
"""
    WARNING:
    questo sito è una kakatura di kazz...incredibile!!!
    Per renderlo compatibile con support ci vuole MOLTA PAZIENZA!!!

    Problemi noti che non superano il test del canale:
        Nelle pagine dei "FILM", film e serie nel sito sono mischiate,
        I titoli quindi non saranno nello stesso numero nelle pagine del canale.
        Alcuni Titoli sono pagine informative e NON devono apparire nel CANALE!!!
        Controllare:
            -che nelle varie sezioni dei FILM appaiano solo FILM, stessa cosa per le serie.
            -che effettivamente vengano tagliati solo gli avvisi.

        Nella TOP FILM non ci sono le voci lingua, anno ( quindi niente TMDB o vari ) e qualità
        Nella pagina delle serie potreste trovare solo il titolo senza stagione ed episodio
        Nel menu contestuale potreste non trovare le voci:
        -"Aggiungi in Videoteca"
        -"Scarica" di qualunque tipo: stagione, serie, etc...

    AVVISO:
        i link 1fichier hanno bisogno dei DNS modificati
        il server woof potrebbe rispondere con "connettore assente"
        I titoli nella sezione SUB-ITA che non riportano Sub-ITA sono in lingua originale senza sottotitoli

"""

import re
import urlparse
import urllib
import urllib2
import time

from channelselector import thumb
from specials import autoplay, filtertools
from core import scrapertools, httptools, tmdb, servertools, support, scrapertoolsV2
from core.item import Item
from platformcode import config, platformtools #,logger

__channel__ = "mondolunatico2"
host = config.get_channel_url(__channel__)
headers = [['Referer', host]]

list_servers = ['verystream', 'wstream', 'openload', 'streamango']
list_quality = ['HD', 'default']

@support.menu
def mainlist(item):
    support.log()

    top = [('Film', ['/genre/film-aggiornati/', 'peliculas', 'movies']),
           ('Al Cinema', ['/genre/al-cinema/', 'peliculas', 'cinema']),
           ('Ultimi Aggiunti', ['/movies/', 'peliculas', 'latest']),
           ('Ultime Richieste', ['/genre/richieste/', 'peliculas', 'request']),
           ('Top ImDb', ['/top-imdb/', 'peliculas', 'top']),
           ('Sub-ITA', ['/genre/subita/', 'peliculas', 'sub']),
           ('Serie TV', ['/tvshows/', 'peliculas', '', 'tvshow']),
           ('Top ImDb', ['/top-imdb/', 'peliculas', 'top', 'tvshow']),
           ('Search...',['', 'search', 'search'])
        ]

    return locals()


@support.scrape
def peliculas(item):
    support.log()

    action = 'findvideos'
    blacklist = ['Avviso Agli Utenti',]

    if item.args != 'search':
        if item.contentType == 'movie':
            action = 'findvideos'
            patron = r'class="item movies"><div class="poster"><img src="(?P<thumb>[^"]+)"'\
                         '[^>]+>(?:<div class="rating">)?[^>]+>.+?(?P<rating>\d+.\d+|\d+)'\
                         '[^>]+>[^>]+>[^>]+>(:?(?P<lang>SubITA)?|(?P<quality>[^<]+)?)?'\
                         '<.+?href="(?P<url>[^"]+)">[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>'\
                         '[^>]+>(?P<title>.+?)</a>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>'\
                         '[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<year>\d+)</span>'\
                         '[^>]+>(?P<duration>\d+)?.+?<[^>]+>(?:[^>]+>[^>]+>[^>]+>[^>]+>)(?P<plot>.+?)<'
            if item.args == 'movies':
                patronBlock = r'<h1>\*Film Aggiornati</h1>(?P<block>.*?)<div class="pagination">'
            elif item.args == 'cinema':
                patronBlock = r'<h1>\*Al Cinema</h1>(?P<block>.*?)<div class="pagination">'
            elif item.args == 'latest':
                patronBlock = r'<h1>Film</h1>(?P<block>.*?)<div class="pagination">'
            elif item.args == 'request':
                patronBlock = r'<h1>\*Richieste</h1>(?P<block>.*?)<div class="pagination">'
            elif item.args == 'sub':
                patronBlock = r'<h1>\*SubITA</h1>(?P<block>.*?)<div class="pagination">'
            elif item.args == 'top':
                patronBlock = r'<h3>Film</h3>(?P<block>.*?)<div class="top-imdb-list tright">'
                patron = r'<div class="image"><div class="[^"]+"><a href="(?P<url>[^"]+)"'\
                         '[^"]+"(?P<thumb>[^"]+)"[^"]+alt="(?P<title>[^"]+)">[^>]+>[^>]+>'\
                         '[^>]+>[^>]+>[^>]+>[^>]+>(?P<rating>[^<]+)<'
                pagination = 25
        else:
            action = 'episodios'
            if item.args == 'top':
                patronBlock = r'<h3>TVShows</h3>(?P<block>.*?)<h2 class="widget-title">'
                patron = r'<div class="image"><div class="[^"]+"><a href="(?P<url>[^"]+)"'\
                         '[^"]+"(?P<thumb>[^"]+)"[^"]+alt="(?P<title>[^"]+)">[^>]+>[^>]+>'\
                         '[^>]+>[^>]+>[^>]+>[^>]+>(?P<rating>[^<]+)<'
            else:
                patronBlock = r'<h1>Serie T[v|V]</h1>(?P<block>.*?)<div class="pagination">'
                patron = r'class="item tvshows">[^>]+>.+?src="(?P<thumb>[^"]+)".+?>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+><a href="(?P<url>[^"]+)">[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<title>[^<]+)</h4>[^>]+>[^>]+> (?:<span class="imdb">IMDb: (?P<rating>\d+.\d+|\d+|N\/A)(?:</span>)?[^>]+>(?P<year>\d+))?<[^>]+>[^>]+>[^>]+>(?:[^>]+>[^>]+>(?P<plot>[^<]+)<)'
    else:
        patronBlock = r'<h1>Results found\:.+?</h1>(?P<block>.*?)<div class="sidebar scrolling">'
        patron = r'<div class="result-item">[^>]+>[^>]+>[^>]+>.+?href="(?P<url>[^"]+)">.+?src="(?P<thumb>[^"]+)" alt="(?P<title>[^"]+)"[^>]+>[^>]+>(?P<type>[^>]+)<[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>IMDb (?P<rating>\d+.\d+|\d+)[^>]+>[^>]+>(?P<year>\d+)<[^>]+>[^>]+>[^>]+>[^>]+>(:?[^>]+>[^>]+>)?(?P<plot>[^<]+)<'

        type_content_dict={'movie': ['film'], 'tvshow': ['tv']}
        type_action_dict={'findvideos': ['film'], 'episodios': ['tv']}

    patronNext = r'<span class="current">.*?href="([^"]+)" class="inactive">'

##    debug = True
    return locals()


def search(item, texto):
    support.log('s-> '+texto)

    item.url = host + "/?s=" + texto

    try:
        return peliculas(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
            return []


def findvideos(item):
    support.log()

    if item.contentType == "tvshow":
        ret=support.dooplay_get_links(item, host)

        if ret == []:
            return episodios(item)
        else:
            item.url = ret[0]["url"]
            return videoplayer(item)

    #if item.args == "movies" or "movie":
    if item.contentType == 'movie':
        return videoplayer(item)

    else:
        return halfplayer(item)


def episodios(item):
    support.log()
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data

    if "<h2>Stagioni ed Episodi</h2>" in data:
        # Se è presente direttamente la lista Stagioni con i relativi episodi
        block = scrapertools.find_single_match(data, r'<h2>Stagioni ed Episodi</h2>(.*?)<div class=\'sbox\'>')
        patron = r'episodiotitle.*?href=\'([^\']+)\'>([^<]+)'
        matches = re.compile(patron, re.DOTALL).findall(block)
        for scrapedurl, scrapedtitle in matches:
            itemlist.append(
                Item(channel=__channel__,
                     action="videoplayer",
                     contentType=item.contentType,
                     title=scrapedtitle,
                     thumbnail=item.thumbnail,
                     fulltitle=scrapedtitle,
                     url=scrapedurl,
                     args=item.args,
                     show=item.show))
        support.videolibrary(itemlist, item, 'color kod')
        return itemlist

    if "File Unico..." in data:
        #Se è direttamente un file unico
        return dooplayer(item)

    if "http://mondolunatico.org/stream/wp-content/uploads/2017/08/hand.gif" in data:
        # Keeplinks
        return keeplink(item)

    else:
        # Se nella lista è presente Dooplayer con elenco episodi
        patron = r'<div class="sp-head" title="Espandi">([^<]+).*?<iframe.*?src="([^"]+)'
        matches = re.compile(patron, re.DOTALL).findall(data)
        if len(matches) > 1:
            for scrapedtitle, scrapedurl in matches:
                itemlist.append(
                    Item(channel=__channel__,
                         action="player_list",
                         contentType=item.contentType,
                         title=scrapedtitle,
                         thumbnail=item.thumbnail,
                         fulltitle=scrapedtitle,
                         url=scrapedurl,
                         show=item.show))
            return itemlist
        else:
             return dooplayer(item)

# ---------------------------------------------------------------------------------------------------------------------------------------------

def player(item):
    support.log()

    data = httptools.downloadpage(item.url, headers=headers).data

    item.url = scrapertools.find_single_match(item.url, r'([^/]+//[^/]+/[^/]+/[^/]+)')

    if "https://mondolunatico.tk" in data:
        data = httptools.downloadpage(item.url, headers=headers).data
        link = scrapertools.find_single_match(data, r'<p><iframe src="(.*?/.*?)[A-Z]')
        item.url = link
        return halfplayer(item)

    if "mondolunatico.tk" in item.url:
        return halfplayer(item)

    #Scarica il link del video integrato nella pagina
    ret=support.dooplay_get_links(item, host)

    #Prelevo il link del video integrato
    url = ret[0]["url"]

    data = httptools.downloadpage(url, headers=headers).data

    if "zmdi zmdi-playlist-audio zmdi-hc-3x" in data:
        return player_list(item)

    else:
        #Correggo il link con il lin del POST
        url = url.replace("/v/", "/api/source/").replace("/p/", "/api/source/")

        postData = urllib.urlencode({
            "r": "",
            "d": "modolunatico.tk",
        })

        block = httptools.downloadpage(url, post=postData).data

        patron = r'"file":".*?\/(r[^"]+)'
        matches = re.compile(patron, re.DOTALL).findall(block)

        itemlist = []

        for scrapedurl in matches:
            scrapedurl = "https://fvs.io/" + scrapedurl
            itemlist.append(
                Item(channel=__channel__,
                    action="play",
                    contentType=item.contentType,
                    title=item.title,
                    thumbnail=item.thumbnail,
                    fulltitle=item.title,
                     url=scrapedurl,
                    show=item.show))

        autoplay.start(itemlist, item)

        return itemlist

# ---------------------------------------------------------------------------------------------------------------------------------------------

def player_list(item):
    support.log()
    itemlist = []

    # Scarico la pagina
    data = httptools.downloadpage(item.url, headers=headers).data

    if "panel_toggle toggleable" in data:
        # Prelevo il blocco lista puntate
        block = scrapertools.find_single_match(data, r'panel_toggle toggleable.*?(<div.*?)<!-- Javascript -->')

        patron = r'data-url="([^"]+)">.*?([A-Z].*?)  '
        matches = re.compile(patron, re.DOTALL).findall(block)

        for scrapedurl, scrapedtitle in matches:
            scrapedtitle = re.sub('mp4|avi|mkv', '', scrapedtitle)
            scrapedtitle = re.sub('WebRip|WEBRip|x264|AC3|1080p|DLMux|XviD-|BDRip|BluRay|HD|WEBMux|H264|BDMux|720p|TV|NFMux|DVDRip|DivX|DVDip|Ac3|Dvdrip|Mux|NovaRip|DVD|SAT|Divx', '', scrapedtitle)
            scrapedtitle = re.sub('ITA|ENG|Italian|SubITA|SUBITA|iTALiAN|LiAN|Ita', '', scrapedtitle)
            scrapedtitle = re.sub('Pir8|UBi|M L|BEDLAM|REPACK|DD5.1|bloody|SVU', '', scrapedtitle)
            scrapedtitle = scrapedtitle.replace(".", " ").replace(" - ", " ").replace("  -", "").replace("  ", "")
            itemlist.append(
                Item(channel=__channel__,
                    action="halfplayer",
                    contentType=item.contentType,
                    title=scrapedtitle,
                    thumbnail=item.thumbnail,
                    fulltitle=scrapedtitle,
                    url="https://mondolunatico.tk" + scrapedurl,
                    show=item.show))

        support.videolibrary(itemlist, item, 'color kod')

        return itemlist

    else:
        return player(item)

# ---------------------------------------------------------------------------------------------------------------------------------------------

def dooplayer(item):
    support.log()
    itemlist = []

    url = item.url
    data = httptools.downloadpage(url, headers=headers).data

    link= scrapertools.find_single_match(data, r'(https://mondolunatico.tk/./[^"]+)')

    data = httptools.downloadpage(link, headers=headers).data
    if "panel_toggle toggleable" in data:
        item.url = link
        return player_list(item)

    # Correggo il link con il lin del POST
    link1 = link.replace("/v/", "/api/source/").replace("/p/", "/api/source/")

    postData = urllib.urlencode({
        "r": link,
        "d": "modolunatico.tk",
    })

    block = httptools.downloadpage(link1, post=postData).data

    patron = r'"file":".*?\/(r[^"]+)'
    matches = re.compile(patron, re.DOTALL).findall(block)

    for scrapedurl in matches:
        scrapedurl = "https://fvs.io/" + scrapedurl
        itemlist.append(
            Item(channel=__channel__,
                 action="play",
                 contentType=item.contentType,
                 title=item.title,
                 thumbnail=item.thumbnail,
                 fulltitle=item.title,
                 url=scrapedurl,
                 show=item.show))

    autoplay.start(itemlist, item)
    support.videolibrary(itemlist, item, 'color kod')

    return itemlist

# ---------------------------------------------------------------------------------------------------------------------------------------------

def keeplink(item):
    support.log()
    itemlist = []

    # Scarico la pagina
    data = httptools.downloadpage(item.url).data

    # Prendo url keeplink
    patron = 'href="(https?://www\.keeplinks\.(?:co|eu)/p92/([^"]+))"'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for keeplinks, id in matches:
        headers = [['Cookie', 'flag[' + id + ']=1; defaults=1; nopopatall=' + str(int(time.time()))],
                   ['Referer', keeplinks]]

        html = httptools.downloadpage(keeplinks, headers=headers).data
        data += str(scrapertools.find_multiple_matches(html, '</lable><a href="([^"]+)" target="_blank"'))

        patron = 'src="([^"]+)" frameborder="0"'
        matches = re.compile(patron, re.DOTALL).findall(data)
        for scrapedurl in matches:
            data += httptools.downloadpage(scrapedurl).data

        for videoitem in servertools.find_video_items(data=data):
            videoitem.title = item.title + " - " + videoitem.title
            videoitem.fulltitle = item.fulltitle
            videoitem.thumbnail = item.thumbnail
            videoitem.show = item.show
            videoitem.plot = item.plot
            videoitem.channel = item.channel
            itemlist.append(videoitem)

    return itemlist

# ---------------------------------------------------------------------------------------------------------------------------------------------

def videoplayer(item):
    support.log()
    itemlist = []

    for link in support.dooplay_get_links(item, host):
        server = link['server'][:link['server'].find(".")]
        if server == "":
            server = "mondolunatico"

        itemlist.append(
            Item(channel=item.channel,
                 action="player" if "mondolunatico" in server else "play",
                 title=server + " [COLOR blue][" + link['title'] + "][/COLOR]",
                 url=link['url'],
                 server=server,
                 fulltitle=item.fulltitle,
                 thumbnail=item.thumbnail,
                 show=item.show,
                 quality=link['title'],
                 contentType=item.contentType,
                 folder=False))

    support.videolibrary(itemlist, item, 'color kod', function_level=2)

    autoplay.start(itemlist, item)

    return itemlist

# ---------------------------------------------------------------------------------------------------------------------------------------------

def halfplayer(item):
    support.log()

    url=item.url

    # Correggo il link con il lin del POST
    url = url.replace("/v/", "/api/source/").replace("/p/", "/api/source/")

    postData = urllib.urlencode({
        "r": "",
        "d": "modolunatico.tk",
    })

    block = httptools.downloadpage(url, post=postData).data

    patron = r'"file":".*?\/(r[^"]+)'
    matches = re.compile(patron, re.DOTALL).findall(block)

    for scrapedurl in matches:
        item.url = "https://fvs.io/" + scrapedurl
        item.server = ""
        itemlist = platformtools.play_video(item, force_direct=True, autoplay=True)

        return itemlist
