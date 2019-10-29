# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per mondoserietv
# ----------------------------------------------------------

from core import support

__channel__ = "mondoserietv"
host = support.config.get_channel_url(__channel__)

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['akstream']
list_quality = ['default']

headers = {'Referer': host}

@support.menu
def mainlist(item):

    film =['/lista-film']

    tvshow = ['/lista-serie-tv',
              ('HD {TV}', ['/lista-serie-tv-in-altadefinizione']),
              ('Anni 50 60 70 80 {TV}',['/lista-serie-tv-anni-60-70-80'])]

    anime = ['/lista-cartoni-animati-e-anime']

    docu = [('Documentari bullet bold',['/lista-documentari', 'peliculas', '', 'tvshow']),
            ('Cerca Documentari... submenu bold', ['/lista-documentari', 'search', '', 'tvshow'])]

    return locals()

def search(item, text):
    support.log(text)
    try:
        item.search = text
        return peliculas(item)

    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("%s" % line)
        return []


@support.scrape
def peliculas(item):
    pagination = ''
    search = item.search
    patronBlock = r'<div class="entry-content pagess">(?P<block>.*?)</ul>'
    patron = r'<li><a href="(?P<url>[^"]+)" title="(?P<title>.*?)(?:\s(?P<year>\d{4}))?"[^>]*>'
    if item.contentType == 'tvshow':
        action = 'episodios'
        anime = True
    return locals()


@support.scrape
def episodios(item):
    anime = True
    patronBlock = r'<table>(?P<block>.*?)</table>'
    patron = r'<tr><td><b>(?:\d+)?.*?(?:(?P<episode>(?:\d+x\d+|\d+)))\s*(?P<title>[^<]+)(?P<url>.*?)<tr>'
    def itemHook(item):
        clear = support.re.sub(r'\[[^\]]+\]', '', item.title)
        if clear.isdigit():
            item.title = support. typo('Episodio ' + clear, 'bold')
        return item
    return locals()

def findvideos(item):
    return support.server(item, item.url)

# def search(item, texto):
#     logger.info("kod.mondoserietv search " + texto)
#     item.url = "%s/?s=%s" % (host, texto)

#     try:
#         if item.extra == "movie":
#             return search_peliculas(item)
#         if item.extra == "tvshow":
#             return search_peliculas_tv(item)

#     # Continua la ricerca in caso di errore 
#     except:
#         import sys
#         for line in sys.exc_info():
#             logger.error("%s" % line)
#         return []

# def search_peliculas(item):
#     logger.info("kod.mondoserietv search_peliculas")
#     itemlist = []

#     # Carica la pagina 
#     data = httptools.downloadpage(item.url, headers=headers).data

#     # Estrae i contenuti 
#     patron = '<div class="boxinfo">\s*<a href="([^"]+)">\s*<span class="tt">(.*?)</span>'
#     matches = re.compile(patron, re.DOTALL).findall(data)

#     for scrapedurl, scrapedtitle in matches:
#         scrapedplot = ""
#         scrapedthumbnail = ""
#         scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)

#         itemlist.append(
#             Item(channel=item.channel,
#                  action="findvideos",
#                  fulltitle=scrapedtitle,
#                  show=scrapedtitle,
#                  title=scrapedtitle,
#                  url=scrapedurl,
#                  thumbnail=scrapedthumbnail,
#                  plot=scrapedplot,
#                  extra=item.extra,
#                  folder=True))

#     tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
#     return itemlist

# def search_peliculas_tv(item):
#     logger.info("kod.mondoserietv search_peliculas_tv")
#     itemlist = []

#     # Carica la pagina 
#     data = httptools.downloadpage(item.url, headers=headers).data

#     # Estrae i contenuti 
#     patron = '<div class="boxinfo">\s*<a href="([^"]+)">\s*<span class="tt">(.*?)</span>'
#     matches = re.compile(patron, re.DOTALL).findall(data)

#     for scrapedurl, scrapedtitle in matches:
#         scrapedplot = ""
#         scrapedthumbnail = ""
#         scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)

#         itemlist.append(
#             Item(channel=item.channel,
#                  action="episodios",
#                  fulltitle=scrapedtitle,
#                  show=scrapedtitle,
#                  title=scrapedtitle,
#                  url=scrapedurl,
#                  thumbnail=scrapedthumbnail,
#                  plot=scrapedplot,
#                  extra=item.extra,
#                  folder=True))

#     tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
#     return itemlist

# def peliculas(item):
#     logger.info("kod.mondoserietv film")
#     itemlist = []

#     p = 1
#     if '{}' in item.url:
#         item.url, p = item.url.split('{}')
#         p = int(p)

#     data = httptools.downloadpage(item.url, headers=headers).data

#     blocco = scrapertools.find_single_match(data, '<div class="entry-content pagess">(.*?)</ul>')
#     patron = r'<a href="(.*?)" title="(.*?)">'
#     matches = re.compile(patron, re.DOTALL).findall(blocco)

#     for i, (scrapedurl, scrapedtitle) in enumerate(matches):
#         if (p - 1) * PERPAGE > i: continue
#         if i >= p * PERPAGE: break
#         scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
#         itemlist.append(Item(channel=item.channel,
#                                      contentType="movie",
#                                      action="findvideos",
#                                      title=scrapedtitle,
#                                      fulltitle=scrapedtitle,
#                                      url=scrapedurl,
#                                      fanart=item.fanart if item.fanart != "" else item.scrapedthumbnail,
#                                      show=item.fulltitle,
#                                      folder=True))

#     if len(matches) >= p * PERPAGE:
#         scrapedurl = item.url + '{}' + str(p + 1)
#         itemlist.append(
#             Item(channel=item.channel,
#                  extra=item.extra,
#                  action="peliculas",
#                  title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
#                  url=scrapedurl,
#                  thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
#                  folder=True))

#     tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
#     return itemlist


# def lista_serie(item):
#     logger.info("kod.mondoserietv novità")
#     itemlist = []

#     p = 1
#     if '{}' in item.url:
#         item.url, p = item.url.split('{}')
#         p = int(p)

#     data = httptools.downloadpage(item.url, headers=headers).data

#     blocco = scrapertools.find_single_match(data, '<div class="entry-content pagess">(.*?)</ul>')
#     patron = r'<a href="(.*?)" title="(.*?)">'
#     matches = re.compile(patron, re.DOTALL).findall(blocco)
#     scrapertools.printMatches(matches)

#     for i, (scrapedurl, scrapedtitle) in enumerate(matches):
#         if (p - 1) * PERPAGE > i: continue
#         if i >= p * PERPAGE: break
#         scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle)
#         itemlist.append(Item(channel=item.channel,
#                                      action="episodios",
#                                      title=scrapedtitle,
#                                      fulltitle=scrapedtitle,
#                                      url=scrapedurl,
#                                      fanart=item.fanart if item.fanart != "" else item.scrapedthumbnail,
#                                      show=item.fulltitle,
#                                      folder=True))

#     if len(matches) >= p * PERPAGE:
#         scrapedurl = item.url + '{}' + str(p + 1)
#         itemlist.append(
#             Item(channel=item.channel,
#                  extra=item.extra,
#                  action="lista_serie",
#                  title="[COLOR lightgreen]" + config.get_localized_string(30992) + "[/COLOR]",
#                  url=scrapedurl,
#                  thumbnail="http://2.bp.blogspot.com/-fE9tzwmjaeQ/UcM2apxDtjI/AAAAAAAAeeg/WKSGM2TADLM/s1600/pager+old.png",
#                  folder=True))

#     tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
#     return itemlist


# def episodios(item):
#     logger.info("kod.mondoserietv episodios")
#     itemlist = []

#     data = httptools.downloadpage(item.url, headers=headers).data
#     blocco = scrapertools.find_single_match(data, '<table>(.*?)</table>')

#     patron = "<tr><td><b>(.*?)(\d+)((?:x\d+| ))(.*?)<\/b>(.*?<tr>)"
#     matches = scrapertoolsV2.find_multiple_matches(blocco, patron)

#     for t1, s, e, t2, scrapedurl in matches:

#         if "x" not in e:
#             e = s

#         if e == s:
#             s = None

#         if s is None:
#             s = "1"

#         if s.startswith('0'):
#             s = s.replace("0", "")

#         if e.startswith('x'):
#             e = e.replace("x", "")

#         scrapedtitle = t1 + s + "x" + e + " " + t2
#         itemlist.append(
#             Item(channel=item.channel,
#                  contentType="episode",
#                  action="findvideos",
#                  items=s,
#                  iteme=e,
#                  fulltitle=scrapedtitle,
#                  show=scrapedtitle,
#                  title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
#                  url=scrapedurl,
#                  thumbnail=item.scrapedthumbnail,
#                  plot=item.scrapedplot,
#                  folder=True))

#     if config.get_videolibrary_support() and len(itemlist) != 0:
#         itemlist.append(
#             Item(channel=item.channel,
#                  title="[COLOR lightblue]%s[/COLOR]" % config.get_localized_string(30161),
#                  url=item.url,
#                  action="add_serie_to_library",
#                  extra="episodios",
#                  show=item.show))

#     return itemlist


# def findvideos(item):
#     logger.info(" findvideos")

#     if item.contentType != "episode":
#         return findvideos_movie(item)

#     itemlist = servertools.find_video_items(data=item.url)
#     logger.info(itemlist)

#     for videoitem in itemlist:
#         videoitem.title = "".join([item.title, '[COLOR green][B]' + videoitem.title + '[/B][/COLOR]'])
#         videoitem.fulltitle = item.fulltitle
#         videoitem.thumbnail = item.thumbnail
#         videoitem.show = item.show
#         videoitem.plot = item.plot
#         videoitem.channel = item.channel
#         videoitem.contentType = item.contentType
#         videoitem.language = IDIOMAS['Italiano']

#     # Requerido para Filtrar enlaces

#     if checklinks:
#         itemlist = servertools.check_list_links(itemlist, checklinks_number)

#     # Requerido para FilterTools

#     # itemlist = filtertools.get_links(itemlist, item, list_language)

#     # Requerido para AutoPlay

#     autoplay.start(itemlist, item)

#     if item.contentType != 'episode':
#         if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
#             itemlist.append(
#                 Item(channel=item.channel, title='[COLOR yellow][B]Aggiungi alla videoteca[/B][/COLOR]', url=item.url,
#                      action="add_pelicula_to_library", extra="findvideos", contentTitle=item.contentTitle))

#     return itemlist


# def findvideos_movie(item):
#     logger.info(" findvideos_movie")

#     # Carica la pagina 

#     data = httptools.downloadpage(item.url).data

#     patron = r"<a href='([^']+)'[^>]*?>[^<]*?<img src='[^']+' style='[^']+' alt='[^']+'>[^<]+?</a>"
#     matches = re.compile(patron, re.DOTALL).findall(data)
#     for scrapedurl in matches:
#         url, c = unshorten(scrapedurl)
#         data += url + '\n'

#     itemlist = servertools.find_video_items(data=data)

#     for videoitem in itemlist:
#         videoitem.title = "".join([item.title, '[COLOR green][B]' + videoitem.title + '[/B][/COLOR]'])
#         videoitem.fulltitle = item.fulltitle
#         videoitem.thumbnail = item.thumbnail
#         videoitem.show = item.show
#         videoitem.plot = item.plot
#         videoitem.channel = item.channel
#         videoitem.contentType = item.contentType

#     return itemlist
