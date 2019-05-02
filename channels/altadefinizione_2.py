# -*- coding: utf-8 -*-
# -*- Created for KOD -*-
# -*- By Greko -*-
# -*- 

#import base64
import re
#import urlparse
# gli import sopra sono da includere all'occorrenza

from channelselector import get_thumb
from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from core import channeltools
from core import tmdb
from platformcode import config, logger


__channel__ = "altadefinizione_2" #stesso di id nel file json

host = "https://www2.altadefinizione.im/" 

# ======== def per utility INIZIO =============================
try:
    __modo_grafico__ = config.get_setting('modo_grafico', __channel__)
    __perfil__ = int(config.get_setting('perfil', __channel__))
except:
    __modo_grafico__ = True
    __perfil__ = 0

# Fijar perfil de color
perfil = [['0xFFFFE6CC', '0xFFFFCE9C', '0xFF994D00', '0xFFFE2E2E', '0xFFFFD700'],
          ['0xFFA5F6AF', '0xFF5FDA6D', '0xFF11811E', '0xFFFE2E2E', '0xFFFFD700'],
          ['0xFF58D3F7', '0xFF2E9AFE', '0xFF2E64FE', '0xFFFE2E2E', '0xFFFFD700']]

if __perfil__ < 3:
    color1, color2, color3, color4, color5 = perfil[__perfil__]
else:
    color1 = color2 = color3 = color4 = color5 = ""

__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', __channel__)
__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', __channel__)

headers = [['User-Agent', 'Mozilla/50.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0'],
           ['Referer', host]]#,['Accept-Language','it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3']]

parameters = channeltools.get_channel_parameters(__channel__)
fanart_host = parameters['fanart']
thumbnail_host = parameters['thumbnail']

IDIOMAS = {'Italiano': 'IT'}
list_language = IDIOMAS.values()
list_servers = ['verystream','vidoza','openload','thevideo','streamcherry','rapidvideo','vidcloud'] # per l'autoplay
list_quality = ['360p','480p','720p','1080p','hd','4k'] # per l'autoplay


# =========== home menu ===================
""""
Queste sono le voci del menu che si vedranno 
entrati nel canale
Togliere aggiungere a seconda del sito
"""

def mainlist(item):
    """
    Creo il menu principale del canale
    :param item:
    :return: itemlist []
    """
    logger.info("%s mainlist log: %s" % (__channel__, item))
    itemlist = []
    title = ''

    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist = [
        # new upload
        Item(channel=__channel__, title="Ultimi Arrivi", action="peliculas",
             url="%s" % host, text_color=color4, extra="film", # color4 = red
             thumbnail=get_thumb(title, auto = True)
             ),
        # x to Cinema
        Item(channel=__channel__, title="Al Cinema", action="peliculas",
             url="%sal-cinema/" % host, text_color=color4, extra="",
             thumbnail=get_thumb(title, auto = True)
             ),
        # Popolari
        Item(channel=__channel__, title="Popolari", action="peliculas",
             url="%spiu-visti.html" % host, text_color=color4, extra="",
             thumbnail=get_thumb(title, auto = True)
             ),
        # x Sub-ita
        Item(channel=__channel__, title="Sottotitolati", action="peliculas",
             url="%sfilm-sub-ita/" % host, text_color=color4, extra="",
             thumbnail=get_thumb(title, auto = True)
             ),
        # x mi sento fortunato - Prende solo film con player a pagamento
        Item(channel=__channel__, title="Mi Sento Fortunato", action="categorie",
             url="%s" % host, text_color=color4, extra="lucky",
             thumbnail=""),
        # x Category
        Item(channel=__channel__, title="Generi", action="categorie",
             url="%s" % host, text_color=color4, extra="genres",
             viewcontent='movies',
             thumbnail=get_thumb(title, auto = True)
             ),
        # x year
        Item(channel=__channel__, title="Anno", action="categorie",
             url="%s" % host, text_color=color4, extra="year",
             thumbnail=get_thumb(title, auto = True)
             ),
        # x quality
        Item(channel=__channel__, title="Qualità", action="categorie",
             url="%s" % host, text_color=color4, extra="quality",
             thumbnail=get_thumb(title, auto = True)
             ),
        # Search
        Item(channel=__channel__, title="Cerca Film...", action="search",
             text_color=color4, extra="",
             thumbnail=get_thumb(title, auto = True)
             ),
                ]

    autoplay.show_option(item.channel, itemlist)
    
    return itemlist


# ======== def in ordine di menu ===========================

def peliculas(item):
    logger.info("%s peliculas log: %s" % (__channel__, item))
    itemlist = []
    # scarico la pagina
    data = httptools.downloadpage(item.url, headers=headers).data
    #blocco = '<section id="lastUpdate">(.*?)<div class="sliderLastUpdate ismobile">'
    # da qui fare le opportuni modifiche
    patron = '<h2 class="titleFilm">.*?href="(.*?)">(.*?)</a>.*?(\d{4})' #url - title - year - lang nel titolo
             #'class="innerImage">.*?href="([^"]+)".*?src="([^"]+)".*?'\
             #'class="ml-item-title">([^"]+)</.*?class="ml-item-label">'\
             #'(.*?)<.*?class="ml-item-label">.*?class="ml-item-label">(.*?)</'
    matches = scrapertools.find_multiple_matches(data, patron)
    
    for scrapedurl, scrapedtitle, scrapedyear in matches:
        if '[sub-ita]' in scrapedtitle.lower():
            scrapedlang = 'Sub-Ita'
        else:
            scrapedlang = 'ITA'
        scrapedtitle = scrapedtitle.replace('[Sub-ITA]','').strip()
        itemlist.append(Item(
            channel=item.channel,
            action="findvideos",
            contentTitle=scrapedtitle,
            fulltitle=scrapedtitle,
            url=host+scrapedurl,
            infoLabels={'year': scrapedyear},
            contenType="movie",
            #thumbnail=scrapedimg,
            title="%s [%s]" % (scrapedtitle, scrapedlang), #scrapedtitle + ' %s' % scrapedlang,
            text_color=color5,
            language=scrapedlang,
            context="buscar_trailer"
        ))

    # poiché c'è l'anno negli item prendiamo le info direttamente da tmdb, anche se a volte può non esserci l'informazione
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True, idioma_busqueda='it')

    # Paginazione
    next_page = scrapertools.find_single_match(data, "<link rel='next' href='(.*?)' />")
    if not next_page:
        next_page = scrapertools.find_single_match(data, '<div class="paginationC nomobile">.*?class="page-numbers" href="(.*?)">')
    
    if next_page != "":
        itemlist.append(
            Item(channel=item.channel,
                 action="peliculas",
                 title=config.get_localized_string(30992),
                 url=host+next_page,
                 extra=item.extra,
                 text_color=color4,
                 thumbnail= get_thumb('nextpage', auto = True)
                 ))
                    
    return itemlist

# =========== def pagina categorie ======================================

def categorie(item):
    logger.info("altadefinizione01_link categorie log: %s" % item)
    itemlist = []
    # scarico la pagina
    data = httptools.downloadpage(item.url, headers=headers).data

    # da qui fare le opportuni modifiche
    if item.extra == 'genres':
        bloque = scrapertools.find_single_match(data, '<ul class="listSubCat" id="Film">(.*?)</ul>')
    elif item.extra == 'year':
        bloque = scrapertools.find_single_match(data, '<ul class="listSubCat" id="Anno">(.*?)</ul>')
    elif item.extra == 'quality':
        bloque = scrapertools.find_single_match(data, '<ul class="listSubCat" id="Qualita">(.*?)</ul>')
    if item.extra == 'lucky':
        bloque = scrapertools.find_single_match(data, '<ul class="listSubCat">(.*?)</ul>')
    patron = '<li><a href="/(.*?)">(.*?)<'
    matches = scrapertools.find_multiple_matches(bloque, patron)

    for scrapurl, scraptitle in sorted(matches):

        itemlist.append(Item(
            channel=item.channel,
            action="peliculas",
            title = scraptitle,
            url=host+scrapurl,
            #extra = '',
            text_color=color4,
            thumbnail=get_thumb(scraptitle, auto = True),
            #Folder = True,
        ))

    return itemlist

# =========== def findvideos ======================================
def findvideos(item):
    logger.info("%s mainlist findvideos_film log: %s" % (__channel__, item))
    itemlist = []

    #Carica la pagina
    data = httptools.downloadpage(item.url, headers=headers).data

    #Estrae il contenuto
    patron = r'<iframe id="iframeVid".*?src="(.*?)".*?</iframe>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    
    #Ricarico la pagina
    url = host + matches[0]
    data = httptools.downloadpage(url).data

    try:
        itemlist = servertools.find_video_items(data=data)

        for videoitem in itemlist:
            #logger.info("Videoitemlist: %s" % videoitem)
            videoitem.title = "%s [%s]" % (item.contentTitle, videoitem.title)
            videoitem.show = item.show
            videoitem.contentTitle = item.contentTitle
            videoitem.contentType = item.contentType
            videoitem.channel = item.channel
            videoitem.text_color = color5
            #videoitem.language = lang_orders[4]
            videoitem.year = item.infoLabels['year']
            videoitem.infoLabels['plot'] = item.infoLabels['plot']
    except AttributeError:
        logger.error("data doesn't contain expected URL")

    # Controlla se i link sono validi
    if __comprueba_enlaces__:
        itemlist = servertools.check_list_links(itemlist, __comprueba_enlaces_num__)

    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    
    # Opción "Añadir esta película a la biblioteca de KODI"
    if item.extra != "library":

        itemlist.append(Item(channel=__channel__, title="Aggiungi alla Videoteca", text_color="green",
                             action="add_pelicula_to_library", url=item.url,
                             thumbnail= get_thumb('videolibrary', auto = True),
                             contentTitle=item.contentTitle, infoLabels = item.infoLabels
                             ))
    
    return itemlist


# =========== def per cercare film/serietv =============

def search(item, text):
    logger.info("%s search log: %s" % (__channel__, item))
    itemlist = []
    text = text.replace(" ", "+")
    item.url = host+"?search=%s" % (text)
    #item.extra = "search"
    try:
        return peliculas(item)
    # Se captura la excepciÛn, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("altadefinizione01_band Search: %s" % line)
        return []


# =========== def per le novità nel menu principale =============

def newest(categoria):
    logger.info("%s newest log: %s" % (__channel__, item))
    itemlist = []
    item = Item()
    try:
        if categoria == "film":
            item.url = host
            item.action = "peliculas"
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
