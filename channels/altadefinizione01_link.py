# -*- coding: utf-8 -*-
# -*- Channel Altadefinizione01L Film - Serie -*-
# -*- Creato per Alfa-addon -*-
# -*- e adattato for KOD -*-
# -*- By Greko -*-
# -*- last change: 19/05/2019
"""
modificati:
 core/servertools.py
 channels/support.py

problemi noti:
 non ordina le categorie
 da sistemare ma in un altro file il titolo nella pagina server

Questi sono "problemi" che secondo me vanno
risolti in altri file

 autoplay
 videoteca nella pagina dei server

In questo modo si ha può avere:

    1. scheletro dei canali simile se non uguale per tutti, cambiano naturalmente gli host e le regex
    2. con una modifica si cambiano tutti i canali
    3. meno lavoro per me...
    
"""

from channels import autoplay, support
from platformcode import config, logger

__channel__ = "altadefinizione01_link"

#host = "https://altadefinizione01.link/" #riaggiornato al 29 aprile 2019
#host = "http://altadefinizione01.art/" # aggiornato al 22 marzo 2019
#host = "https://altadefinizione01.network/" #aggiornato al 22 marzo 2019
#host = "http://altadefinizione01.date/" #aggiornato al 3 maggio 2019
#host = "https://altadefinizione01.voto/" #aggiornato al 3 maggio 2019
host = "https://altadefinizione01.estate/" # aggiornato al 19 maggio 2019

# ======== def per utility INIZIO ============================
    
##__comprueba_enlaces__ = config.get_setting('comprueba_enlaces', __channel__)
##__comprueba_enlaces_num__ = config.get_setting('comprueba_enlaces_num', __channel__)

headers = [['User-Agent', 'Mozilla/50.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0'],
           ['Referer', host]]#,['Accept-Language','it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3']]

##IDIOMAS = {'Italiano': 'IT'}
##list_language = IDIOMAS.values()
list_servers = ['supervideo', 'streamcherry','rapidvideo', 'streamango', 'openload']
list_quality = ['default']

# =========== home menu ===================

def mainlist(item):
    """
    Creo il menu principale del canale
    :param item:
    :return: itemlist []
    """
    support.log()
    itemlist = []


    # Menu Principale
    support.menu(itemlist, 'Novità bold', 'peliculas', host)
    support.menu(itemlist, 'Film per Genere', 'genres', host, args='genres')
    support.menu(itemlist, 'Film per Anno submenu', 'genres', host, args='years')
    support.menu(itemlist, 'Film per Qualità submenu', 'genres', host, args='quality') 
    support.menu(itemlist, 'Al Cinema bold', 'peliculas', host+'film-del-cinema')    
    support.menu(itemlist, 'Popolari bold', 'peliculas', host+'piu-visti.html')
    support.menu(itemlist, 'Mi sento fortunato bold', 'genres', host, args='lucky')    
    support.menu(itemlist, 'Sub-ITA bold', 'peliculas', host+'film-sub-ita/')   
    support.menu(itemlist, 'Cerca film submenu', 'search', host)

    # per autoplay
    autoplay.init(item.channel, list_servers, list_quality)
    autoplay.show_option(item.channel, itemlist)
    
    return itemlist

# ======== def in ordine di action dal menu ===========================

def peliculas(item):
    support.log
    itemlist = []

    patron = r'class="innerImage">.*?href="([^"]+)".*?src="([^"]+)"'\
             '.*?class="ml-item-title">([^"]+)</.*?class="ml-item-label">(.*?)'\
             '<.*?class="ml-item-label">.*?class="ml-item-label ml-item-label-.*?">'\
             '(.*?)</div>.*?class="ml-item-label">(.*?)</'
    listGroups = ['url', 'thumb', 'title', 'year', 'quality', 'lang']

    patronNext =  '<span>\d</span> <a href="([^"]+)">'
    
    itemlist = support.scrape(item, patron=patron, listGroups=listGroups,
                          headers= headers, patronNext=patronNext,
                          action='findvideos')    
    
    return itemlist

# =========== def pagina categorie ======================================

def genres(item):
    support.log
    itemlist = []
    #data = httptools.downloadpage(item.url, headers=headers).data
    if item.args == 'genres':
        bloque = r'<ul class="listSubCat" id="Film">(.*?)</ul>'
    elif item.args == 'years':
        bloque = r'<ul class="listSubCat" id="Anno">(.*?)</ul>'
    elif item.args == 'quality':
        bloque = r'<ul class="listSubCat" id="Qualita">(.*?)</ul>'
    elif item.args == 'lucky': # sono i titoli random nella pagina, alcuni rimandano solo a server a pagamento
        bloque = r'FILM RANDOM.*?class="listSubCat">(.*?)</ul>'

    patron = r'<li><a href="([^"]+)">(.*?)<'

    listGroups = ['url','title']
    itemlist = support.scrape(item, patron=patron, listGroups=listGroups,
                          headers= headers, patron_block = bloque,
                          action='peliculas')    

    return itemlist

# =========== def per cercare film/serietv =============
#host+/index.php?do=search&story=avatar&subaction=search
def search(item, text):
    logger.info("%s mainlist search log: %s %s" % (__channel__, item, text))
    itemlist = []
    text = text.replace(" ", "+")
    item.url = host+"/index.php?do=search&story=%s&subaction=search" % (text)
    #item.extra = "search"
    try:
        return peliculas(item)
    # Se captura la excepciÛn, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.info("%s mainlist search log: %s" % (__channel__, line))
        return []

# =========== def per le novità nel menu principale =============

def newest(categoria):
    support.log(categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == "peliculas":
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
