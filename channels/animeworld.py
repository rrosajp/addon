# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per animeworld
# ----------------------------------------------------------
import re
import time
import urllib

import urlparse

import channelselector
from channelselector import thumb
from core import httptools, scrapertoolsV2, servertools, tmdb, support, jsontools
from core.item import Item
from platformcode import logger, config
from specials import autoplay, autorenumber

__channel__ = 'animeworld'
host = config.get_setting("channel_host", __channel__)
headers = [['Referer', host]]

IDIOMAS = {'Italiano': 'Italiano'}
list_language = IDIOMAS.values()
list_servers = ['diretto']
list_quality = []

checklinks = config.get_setting('checklinks', 'animeworld')
checklinks_number = config.get_setting('checklinks_number', 'animeworld')


def mainlist(item):
    logger.info(__channel__+"  mainlist")
    
    itemlist =[]
    
    support.menu(itemlist, 'Anime bold', 'lista_anime', host+'/az-list')
    support.menu(itemlist, 'ITA submenu', 'build_menu', host+'/filter?language[]=1', args=["anime"])
    support.menu(itemlist, 'Sub-ITA submenu', 'build_menu', host+'/filter?language[]=0', args=["anime"])
    support.menu(itemlist, 'Archivio A-Z submenu', 'alfabetico', host+'/az-list', args=["tvshow","a-z"])
    support.menu(itemlist, 'In corso submenu', 'video', host+'/', args=["in sala"])
    support.menu(itemlist, 'Generi submenu', 'generi', host+'/')
    support.menu(itemlist, 'Ultimi Aggiunti bold', 'video', host+'/newest', args=["anime"])
    support.menu(itemlist, 'Ultimi Episodi bold', 'video', host+'/updated', args=["novita'"])
    support.menu(itemlist, 'Cerca...', 'search')

    
    autoplay.init(item.channel, list_servers, list_quality)
    autoplay.show_option(item.channel, itemlist)

    itemlist.append(
        Item(channel='setting',
             action="channel_config",
             title=support.typo("Configurazione Canale color lime"),
             config=item.channel,
             folder=False,
             thumbnail=channelselector.get_thumb('setting_0.png'))
    )

    return itemlist

# Crea menu dei generi =================================================

def generi(item):
    support.log(item.channel+" generi")
    itemlist = []
    patron_block = r'</i>\sGeneri</a>\s*<ul class="sub">(.*?)</ul>'
    patron = r'<a href="([^"]+)"\stitle="([^"]+)">'
    matches = support.match(item,patron, patron_block, headers)[0]

    for scrapedurl, scrapedtitle in matches:
        itemlist.append(Item(
            channel=item.channel,
            action="video",
            title=scrapedtitle,
            url="%s%s" % (host,scrapedurl)))

    return itemlist


# Crea Menu Filtro ======================================================

def build_menu(item):
    itemlist = []
    itemlist.append(Item(
                    channel=item.channel,
                    action="video",
                    title="[B]Tutti[/B]",
                    url=item.url))

    data = httptools.downloadpage(item.url).data
    data = re.sub(r'\n|\t','',data)
    data = re.sub(r'>\s*<','><',data)
 
    block = scrapertoolsV2.find_single_match(data, r'<form class="filters.*?>(.*?)<\/form>')
    
    matches = re.compile(r'<button class="btn btn-sm btn-default dropdown-toggle" data-toggle="dropdown"> (.*?) <span.*?>(.*?)<\/ul>', re.DOTALL).findall(block)

    for title, html in matches:
        itemlist.append(
            Item(channel=item.channel,
                 action='build_sub_menu',
                 contentType="tvshow",
                 title='[B] > ' + title + '[/B]',
                 fulltitle=title,
                 show=title,
                 url=item.url,
                 html=html,
                 thumbnail=item.thumbnail,
                 fanart=item.fanart))

    # Elimina FLingua dal Menu
    itemlist.pop(6)
    itemlist.pop(6)

    itemlist = thumb(itemlist)

    return itemlist

# Crea SottoMenu Filtro ======================================================

def build_sub_menu(item):
    itemlist = []
    matches = re.compile(r'<input.*?name="(.*?)" value="(.*?)".*?><label.*?>(.*?)<\/label>', re.DOTALL).findall(item.html)
    for name, value, title in matches:
        itemlist.append(
            Item(channel=item.channel,
                 action='video',
                 contentType="tvshow",
                 title='[B]' + title + ' >[/B]',
                 fulltitle=title,
                 show=title,
                 url=item.url + '&' + name + '=' + value,
                 plot=""))
    itemlist = thumb(itemlist)
    return itemlist

# Novità ======================================================

def newest(categoria):
    logger.info(__channel__+"  newest")
    itemlist = []
    item = Item()
    try:
        if categoria == "anime":
            item.url = host + '/newest'
            item.action = "video"
            itemlist = video(item)

            if itemlist[-1].action == "video":
                itemlist.pop()
    # Continua la ricerca in caso di errore 
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


# Cerca ===========================================================

def search(item, texto):
    logger.info(texto)
    item.url = host + '/search?keyword=' + texto
    try:
        return video(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []




# Lista A-Z ====================================================

def alfabetico(item):
    logger.info(__channel__+"  alfabetico")
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r'\n|\t','',data)
    data = re.sub(r'>\s*<','><',data)

    block = scrapertoolsV2.find_single_match(data, r'<span>.*?A alla Z.<\/span>.*?<ul>(.*?)<\/ul>')

    matches = re.compile('<a href="([^"]+)" title="([^"]+)">', re.DOTALL).findall(block)
    scrapertoolsV2.printMatches(matches)

    for url, title in matches:
        itemlist.append(
            Item(channel=item.channel,
                 action='lista_anime',
                 contentType="tvshow",
                 title=title,
                 fulltitle=title,
                 show=title,
                 url=url,
                 plot=""))

    return itemlist

def lista_anime(item):
    logger.info(__channel__+"  lista_anime")

    itemlist = []

    # Carica la pagina
    data = httptools.downloadpage(item.url).data
    data = re.sub(r'\n|\t','',data)
    data = re.sub(r'>\s*<','><',data)

    # Estrae i contenuti
    patron = r'<div class="item"><a href="([^"]+)".*?src="([^"]+)".*?data-jtitle="([^"]+)".*?>([^<]+)<\/a><p>(.*?)<\/p>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumb, scrapedoriginal, scrapedtitle, scrapedplot in matches:
        
        if scrapedoriginal == scrapedtitle:
            scrapedoriginal=''
        else:
            scrapedoriginal = ' - [ ' + scrapedoriginal + ' ]'

        year = ''
        lang = ''
        if '(' in scrapedtitle:
            year = scrapertoolsV2.find_single_match(scrapedtitle, r'(\([0-9]+\))')
            lang = scrapertoolsV2.find_single_match(scrapedtitle, r'(\([a-zA-Z]+\))')
        
        title = scrapedtitle.replace(year,'').replace(lang,'')
        original = scrapedoriginal.replace(year,'').replace(lang,'')
        title = '[B]' + title + '[/B]' + year + lang + original
        itemlist.append(
                Item(channel=item.channel,
                     extra=item.extra,
                     contentType="episode",
                     action="episodios",
                     text_color="azure",
                     title=title,
                     url=scrapedurl,
                     thumbnail=scrapedthumb,
                     fulltitle=title,
                     show=title,
                     plot=scrapedplot,
                     folder=True))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)    
    autorenumber.renumber(itemlist)

    # Next page
    support.nextPage(itemlist, item, data, r'<a class="page-link" href="([^"]+)" rel="next"')
    # next_page = scrapertoolsV2.find_single_match(data, '<a class="page-link" href="([^"]+)" rel="next"')
    #
    # if next_page != '':
    #     itemlist.append(
    #         Item(channel=item.channel,
    #              action='lista_anime',
    #              title='[B]' + config.get_localized_string(30992) + ' >[/B]',
    #              url=next_page,
    #              contentType=item.contentType,
    #              thumbnail=thumb()))


    return itemlist


def video(item):
    logger.info(__channel__+"  video")
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r'\n|\t','',data)
    data = re.sub(r'>\s*<','><',data)

    patron = r'<a href="([^"]+)" class="poster.*?><img src="([^"]+)"(.*?)data-jtitle="([^"]+)" .*?>(.*?)<\/a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedthumb ,scrapedinfo, scrapedoriginal, scrapedtitle in matches:
        # Cerca Info come anno o lingua nel Titolo
        year = ''
        lang = ''
        if '(' in scrapedtitle:
            year = scrapertoolsV2.find_single_match(scrapedtitle, r'( \([0-9]+\))')
            lang = scrapertoolsV2.find_single_match(scrapedtitle, r'( \([a-zA-Z]+\))')
        
        # Rimuove Anno e Lingua nel Titolo
        title = scrapedtitle.replace(year,'').replace(lang,'')
        original = scrapedoriginal.replace(year,'').replace(lang,'')
        
        # Compara Il Titolo con quello originale
        if original == title:
            original=''
        else:
            original = ' - [ ' + scrapedoriginal + ' ]'

        # cerca info supplementari
        ep = ''
        ep = scrapertoolsV2.find_single_match(scrapedinfo, '<div class="ep">(.*?)<')
        if  ep != '':
            ep = ' - ' + ep

        ova = ''
        ova = scrapertoolsV2.find_single_match(scrapedinfo, '<div class="ova">(.*?)<')
        if  ova != '':
            ova = ' - (' + ova + ')'
        
        ona = ''
        ona = scrapertoolsV2.find_single_match(scrapedinfo, '<div class="ona">(.*?)<')
        if  ona != '':
            ona = ' - (' + ona + ')'

        movie = ''
        movie = scrapertoolsV2.find_single_match(scrapedinfo, '<div class="movie">(.*?)<')
        if  movie != '':
            movie = ' - (' + movie + ')'

        special = ''
        special = scrapertoolsV2.find_single_match(scrapedinfo, '<div class="special">(.*?)<')
        if  special != '':
            special = ' - (' + special + ')'


        # Concatena le informazioni
        info = ep + lang + year + ova + ona + movie + special

        # Crea il title da visualizzare
        long_title = '[B]' + title + '[/B]' + info + original

        # Controlla se sono Episodi o Film
        if movie == '':
            contentType = 'episode'
            action = 'episodios'
        else:
            contentType = 'movie'
            action = 'findvideos'
        
        itemlist.append(
                Item(channel=item.channel,
                     contentType=contentType,
                     action=action,
                     title=long_title,
                     url=scrapedurl,
                     fulltitle=title,
                     show=title,
                     thumbnail=scrapedthumb,
                     context = autoplay.context))
    
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    autorenumber.renumber(itemlist)

    # Next page
    support.nextPage(itemlist, item, data, r'<a\sclass="page-link"\shref="([^"]+)"\srel="next"\saria-label="Successiva')
    # next_page = scrapertoolsV2.find_single_match(data, '<a class="page-link" href=".*?page=([^"]+)" rel="next"')
    #
    # if next_page != '':
    #     itemlist.append(
    #         Item(channel=item.channel,
    #              action='video',
    #              title='[B]' + config.get_localized_string(30992) + ' >[/B]',
    #              url=re.sub('&page=([^"]+)', '', item.url) + '&page=' + next_page,
    #              contentType=item.contentType,
    #              thumbnail=thumb()))

    return itemlist


def episodios(item):
    logger.info(__channel__+"  episodios")
    itemlist = [] 

    data = httptools.downloadpage(item.url).data.replace('\n', '')
    data = re.sub(r'>\s*<', '><', data)
    block1 = scrapertoolsV2.find_single_match(data, r'<div class="widget servers".*?>(.*?)<div id="download"')
    block = scrapertoolsV2.find_single_match(block1,r'<div class="server.*?>(.*?)<div class="server.*?>')
   
    patron = r'<li><a.*?href="([^"]+)".*?>(.*?)<\/a>'
    matches = re.compile(patron, re.DOTALL).findall(block)

    extra = {}
    extra['data'] = block1.replace('<strong>Attenzione!</strong> Non ci sono episodi in questa sezione, torna indietro!.','')

    for scrapedurl, scrapedtitle in matches:
        extra['episode'] = scrapedtitle
        scrapedtitle = '[B] Episodio ' + scrapedtitle + '[/B]'
        itemlist.append(
            Item(
                channel=item.channel,
                action="findvideos",
                contentType="episode",
                title=scrapedtitle,
                url=urlparse.urljoin(host, scrapedurl),
                fulltitle=scrapedtitle,
                show=scrapedtitle,
                plot=item.plot,
                fanart=item.thumbnail,
                extra=extra,
                thumbnail=item.thumbnail))
    
    autorenumber.renumber(itemlist, item,'bold')
    
    
    # Aggiungi a Libreria
    # if config.get_videolibrary_support() and len(itemlist) != 0:
    #     itemlist.append(
    #         Item(
    #             channel=item.channel,
    #             title="[COLOR lightblue]%s[/COLOR]" % config.get_localized_string(30161),
    #             url=item.url,
    #             action="add_serie_to_library",
    #             extra="episodios",
    #             show=item.show))
    support.videolibrary(itemlist, item)

    return itemlist


def findvideos(item):
    logger.info(__channel__+"  findvideos")

    itemlist = []
    # logger.debug(item.extra)
    episode = '1'
    #recupero i server disponibili
    if item.extra and item.extra['episode']:
        data = item.extra['data']
        episode = item.extra['episode']
    else:
        data = httptools.downloadpage(item.url,headers=headers).data
    block = scrapertoolsV2.find_single_match(data,r'data-target="\.widget\.servers.*?>(.*?)</div>')
    servers = scrapertoolsV2.find_multiple_matches(block,r'class="tab.*?data-name="([0-9]+)">([^<]+)</span')
    videolist = []
    videoData = ''
    for serverid, servername in servers:
        #recupero l'id del video per questo server
        block = scrapertoolsV2.find_single_match(data,r'<div class="server.*?data-id="'+serverid+'">(.*?)</ul>')
        id = scrapertoolsV2.find_single_match(block,r'<a\sdata-id="([^"]+)"\sdata-base="'+episode+'"')

        dataJson = httptools.downloadpage('%s/ajax/episode/info?id=%s&server=%s&ts=%s' % (host, id, serverid, int(time.time())), headers=[['x-requested-with', 'XMLHttpRequest']]).data
        json = jsontools.load(dataJson)

        videoData +='\n'+json['grabber']

        if serverid == '33':
            post = urllib.urlencode({'r': '', 'd': 'www.animeworld.biz'})
            dataJson = httptools.downloadpage(json['grabber'].replace('/v/','/api/source/'),headers=[['x-requested-with', 'XMLHttpRequest']],post=post).data
            json = jsontools.load(dataJson)
            logger.debug(json['data'])
            if json['data']:
                for file in json['data']:
                    itemlist.append(
                        Item(
                            channel=item.channel,
                            action="play",
                            title='diretto',
                            url=file['file'],
                            quality=file['label'],
                            server='directo',
                            show=item.show,
                            contentType=item.contentType,
                            folder=False))

        if serverid == '28':
            itemlist.append(
                Item(
                    channel=item.channel,
                    action="play",
                    title='diretto',
                    quality='',
                    url=json['grabber'],
                    server='directo',
                    show=item.show,
                    contentType=item.contentType,
                    folder=False))


    itemlist += servertools.find_video_items(item,videoData)

    return support.server(item,itemlist=itemlist)

    anime_id = scrapertoolsV2.find_single_match(item.url, r'.*\..*?\/(.*)')
    data = httptools.downloadpage(host + "/ajax/episode/serverPlayer?id=" + anime_id).data
    patron = '<source src="([^"]+)"'

    matches = re.compile(patron, re.DOTALL).findall(data)


    for video in matches:
        itemlist.append(
            Item(
                channel=item.channel,
                action="play",
                # title=item.title + " [[COLOR orange]Diretto[/COLOR]]",
                title='diretto',
                quality='',
                url=video,
                server='directo',
                show=item.show,
                contentType=item.contentType,
                folder=False))

    return support.server(item,data, itemlist)

    # Requerido para Filtrar enlaces

    if checklinks:
        itemlist = servertools.check_list_links(itemlist, checklinks_number)

    # Requerido para FilterTools

    # itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    return itemlist


