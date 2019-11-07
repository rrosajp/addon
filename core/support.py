# -*- coding: utf-8 -*-
# -----------------------------------------------------------
# support functions that are needed by many channels, to no repeat the same code
import base64
import inspect
import os
import re
import urllib
import urlparse
import xbmcaddon

from channelselector import thumb
from core import httptools, scrapertoolsV2, servertools, tmdb, channeltools
from core.item import Item
from lib import unshortenit
from platformcode import logger, config
from specials import autoplay

def hdpass_get_servers(item):
    # Carica la pagina
    itemlist = []
    data = httptools.downloadpage(item.url).data.replace('\n', '')
    patron = r'<iframe(?: id="[^"]+")? width="[^"]+" height="[^"]+" src="([^"]+)"[^>]+><\/iframe>'
    url = scrapertoolsV2.find_single_match(data, patron).replace("?alta", "")
    url = url.replace("&download=1", "")
    if 'https' not in url:
        url = 'https:' + url

    if 'hdpass' or 'hdplayer' in url:
        data = httptools.downloadpage(url).data

        start = data.find('<div class="row mobileRes">')
        end = data.find('<div id="playerFront">', start)
        data = data[start:end]

        patron_res = '<div class="row mobileRes">(.*?)</div>'
        patron_mir = '<div class="row mobileMirrs">(.*?)</div>'
        patron_media = r'<input type="hidden" name="urlEmbed" data-mirror="([^"]+)" id="urlEmbed"\s*value="([^"]+)"\s*/>'

        res = scrapertoolsV2.find_single_match(data, patron_res)

        itemlist = []

        for res_url, res_video in scrapertoolsV2.find_multiple_matches(res, '<option.*?value="([^"]+?)">([^<]+?)</option>'):

            data = httptools.downloadpage(urlparse.urljoin(url, res_url)).data.replace('\n', '')

            mir = scrapertoolsV2.find_single_match(data, patron_mir)

            for mir_url, srv in scrapertoolsV2.find_multiple_matches(mir, '<option.*?value="([^"]+?)">([^<]+?)</value>'):

                data = httptools.downloadpage(urlparse.urljoin(url, mir_url)).data.replace('\n', '')
                for media_label, media_url in scrapertoolsV2.find_multiple_matches(data, patron_media):
                    itemlist.append(Item(channel=item.channel,
                                         action="play",
                                         fulltitle=item.fulltitle,
                                         quality=res_video,
                                         show=item.show,
                                         thumbnail=item.thumbnail,
                                         contentType=item.contentType,
                                         url=url_decode(media_url)))
                    log("video -> ", res_video)

    return server(item, itemlist=itemlist)


def url_decode(url_enc):
    lenght = len(url_enc)
    if lenght % 2 == 0:
        len2 = lenght / 2
        first = url_enc[0:len2]
        last = url_enc[len2:lenght]
        url_enc = last + first
        reverse = url_enc[::-1]
        return base64.b64decode(reverse)

    last_car = url_enc[lenght - 1]
    url_enc[lenght - 1] = ' '
    url_enc = url_enc.strip()
    len1 = len(url_enc)
    len2 = len1 / 2
    first = url_enc[0:len2]
    last = url_enc[len2:len1]
    url_enc = last + first
    reverse = url_enc[::-1]
    reverse = reverse + last_car
    return base64.b64decode(reverse)


def color(text, color):
    return "[COLOR " + color + "]" + text + "[/COLOR]"


def search(channel, item, texto):
    log(item.url + " search " + texto)
    if 'findhost' in dir(channel):
        channel.findhost()
    item.url = channel.host + "/?s=" + texto
    try:
        return channel.peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
    return []


def dbg():
    import web_pdb;
    if not web_pdb.WebPdb.active_instance:
        import webbrowser
        webbrowser.open('http://127.0.0.1:5555')
    web_pdb.set_trace()



def regexDbg(item, patron, headers, data=''):
    import json, urllib2, webbrowser
    url = 'https://regex101.com'

    if not data:
        html = httptools.downloadpage(item.url, headers=headers, ignore_response_code=True).data.replace("'", '"')
        html = re.sub('\n|\t', ' ', html)
    else:
        html = data
    headers = {'content-type': 'application/json'}
    data = {
        'regex': patron,
        'flags': 'gm',
        'testString': html,
        'delimiter': '"""',
        'flavor': 'python'
    }
    r = urllib2.Request(url + '/api/regex', json.dumps(data, encoding='latin1'), headers=headers)
    r = urllib2.urlopen(r).read()
    permaLink = json.loads(r)['permalinkFragment']
    webbrowser.open(url + "/r/" + permaLink)


def scrape2(item, patron = '', listGroups = [], headers="", blacklist="", data="", patronBlock="",
           patronNext="", action="findvideos", addVideolibrary = True, typeContentDict={}, typeActionDict={}):
    m = re.search(r'(?<!\\|\[)\((?!\?)', patron)
    n = 0
    while m:
        patron = patron[:m.end()] + '?P<' + listGroups[n] + '>' + patron[m.end():]
        m = re.search(r'(?<!\\|\[)\((?!\?)', patron)
        n += 1
    regexDbg(item, patron, headers)


def scrapeLang(scraped, lang, longtitle):
    ##    Aggiunto/modificato per gestire i siti che hanno i video
    ##    in ita e subita delle serie tv nella stessa pagina
    # altrimenti dopo un sub-ita mette tutti quelli a seguire in sub-ita
    # e credo sia utile per filtertools
    language = ''

    if scraped['lang']:
        if 'ita' in scraped['lang'].lower():
            language = 'ITA'
        if 'sub' in scraped['lang'].lower():
            language = 'Sub-' + language

    if not language: language = lang
    if language: longtitle += typo(language, '_ [] color kod')

    return language, longtitle

def cleantitle(title):
    cleantitle = scrapertoolsV2.htmlclean(scrapertoolsV2.decodeHtmlentities(title).replace('"', "'").replace('×', 'x').replace('–', '-')).strip()
    return cleantitle

def scrapeBlock(item, args, block, patron, headers, action, pagination, debug, typeContentDict, typeActionDict, blacklist, search, pag, function, lang):
    itemlist = []
    log("scrapeBlock qui", block, patron)
    matches = scrapertoolsV2.find_multiple_matches_groups(block, patron)
    log('MATCHES =', matches)

    if debug:
        regexDbg(item, patron, headers, block)

    known_keys = ['url', 'title', 'title2', 'season', 'episode', 'thumb', 'quality', 'year', 'plot', 'duration', 'genere', 'rating', 'type', 'lang']
    # Legenda known_keys per i groups nei patron
    # known_keys = ['url', 'title', 'title2', 'season', 'episode', 'thumb', 'quality',
    #                'year', 'plot', 'duration', 'genere', 'rating', 'type', 'lang']
    # url = link relativo o assoluto alla pagina titolo film/serie
    # title = titolo Film/Serie/Anime/Altro
    # title2 = titolo dell'episodio Serie/Anime/Altro
    # season = stagione in formato numerico
    # episode = numero episodio, in formato numerico.
    # thumb = linkrealtivo o assoluto alla locandina Film/Serie/Anime/Altro
    # quality = qualità indicata del video
    # year = anno in formato numerico (4 cifre)
    # duration = durata del Film/Serie/Anime/Altro
    # genere = genere del Film/Serie/Anime/Altro. Es: avventura, commedia
    # rating = punteggio/voto in formato numerico
    # type = tipo del video. Es. movie per film o tvshow per le serie. Di solito sono discrimanti usati dal sito
    # lang = lingua del video. Es: ITA, Sub-ITA, Sub, SUB ITA.
    # AVVERTENZE: Se il titolo è trovato nella ricerca TMDB/TVDB/Altro allora le locandine e altre info non saranno quelle recuperate nel sito.!!!!

    stagione = '' # per quei siti che hanno la stagione nel blocco ma non nelle puntate
    for i, match in enumerate(matches):
        if pagination and (pag - 1) * pagination > i: continue  # pagination
        if pagination and i >= pag * pagination: break          # pagination
        listGroups = match.keys()
        match = match.values()

        if len(listGroups) > len(match):  # to fix a bug
            match = list(match)
            match.extend([''] * (len(listGroups) - len(match)))

        scraped = {}
        for kk in known_keys:
            val = match[listGroups.index(kk)] if kk in listGroups else ''
            if val and (kk == "url" or kk == 'thumb') and 'http' not in val:
                val = scrapertoolsV2.find_single_match(item.url, 'https?://[a-z0-9.-]+') + val
            scraped[kk] = val

        if scraped['season']:
            stagione = scraped['season']
            episode = scraped['season'] +'x'+ scraped['episode']
        elif stagione:
            episode = stagione +'x'+ scraped['episode']
        elif item.contentType == 'tvshow' and (scraped['episode'] == '' and scraped['season'] == '' and stagione == ''):
            item.news = 'season_completed'
            episode = ''
        else:
            episode = re.sub(r'\s-\s|-|x|&#8211|&#215;', 'x', scraped['episode']) if scraped['episode'] else ''

        #episode = re.sub(r'\s-\s|-|x|&#8211|&#215;', 'x', scraped['episode']) if scraped['episode'] else ''
        title = cleantitle(scraped['title']) if scraped['title'] else ''
        title2 = cleantitle(scraped['title2']) if scraped['title2'] else ''
        quality = scraped['quality'].strip() if scraped['quality'] else ''
        Type = scraped['type'] if scraped['type'] else ''
        plot = cleantitle(scraped["plot"]) if scraped["plot"] else ''

        # make formatted Title [longtitle]
        s = ' - '
        title = episode + (s if episode and title else '') + title
        longtitle = title + (s if title and title2 else '') + title2
        longtitle = typo(longtitle, 'bold')
        longtitle += typo(quality, '_ [] color kod') if quality else ''

        lang1, longtitle = scrapeLang(scraped, lang, longtitle)

        # if title is set, probably this is a list of episodes or video sources
        # necessaria l'aggiunta di == scraped["title"] altrimenti non prende i gruppi dopo le categorie
        if item.infoLabels["title"] == scraped["title"]:
            infolabels = item.infoLabels
        else:
            infolabels = {}
            if scraped['year']:
                infolabels['year'] = scraped['year']
            if scraped["plot"]:
                infolabels['plot'] = plot
            if scraped['duration']:
                matches = scrapertoolsV2.find_multiple_matches(scraped['duration'],
                                                               r'([0-9])\s*?(?:[hH]|:|\.|,|\\|\/|\||\s)\s*?([0-9]+)')
                for h, m in matches:
                    scraped['duration'] = int(h) * 60 + int(m)
                if not matches:
                    scraped['duration'] = scrapertoolsV2.find_single_match(scraped['duration'], r'(\d+)')
                infolabels['duration'] = int(scraped['duration']) * 60
            if scraped['genere']:
                genres = scrapertoolsV2.find_multiple_matches(scraped['genere'], '[A-Za-z]+')
                infolabels['genere'] = ", ".join(genres)
            if scraped["rating"]:
                infolabels['rating'] = scrapertoolsV2.decodeHtmlentities(scraped["rating"])

        AC = CT = ''
        if typeContentDict:
            for name, variants in typeContentDict.items():
                if str(scraped['type']).lower() in variants:
                    CT = name
                    break
                else: CT = item.contentType
        if typeActionDict:
            for name, variants in typeActionDict.items():
                if str(scraped['type']).lower() in variants:
                    AC = name
                    break
                else: AC = action

        if (scraped["title"] not in blacklist) and (search.lower() in longtitle.lower()):
            it = Item(
                channel=item.channel,
                action=AC if AC else action,
                contentType='episode' if function == 'episodios' else CT if CT else item.contentType,
                title=longtitle,
                fulltitle=item.fulltitle if function == 'episodios' else title,
                show=item.show if function == 'episodios' else title,
                quality=quality,
                url=scraped["url"],
                infoLabels=infolabels,
                thumbnail=item.thumbnail if function == 'episodios' else scraped["thumb"] ,
                args=item.args,
                contentSerieName= scraped['title'] if item.contentType or CT != 'movie' and function != 'episodios' else item.fulltitle if function == 'episodios' else '',
                contentTitle= scraped['title'] if item.contentType or CT == 'movie' else '',
                contentLanguage = lang1,
                contentEpisodeNumber=episode if episode else '',
                news= item.news if item.news else ''
            )

            for lg in list(set(listGroups).difference(known_keys)):
                it.__setattr__(lg, match[listGroups.index(lg)])

            if 'itemHook' in args:
                it = args['itemHook'](it)
            itemlist.append(it)

    return itemlist, matches


def scrape(func):
    # args is a dict containing the foolowing keys:
    # patron: the patron to use for scraping page, all capturing group must match with listGroups
    # listGroups: a list containing the scraping info obtained by your patron, in order
    # accepted values are: url, title, thumb, quality, year, plot, duration, genre, rating, episode, lang

    # headers: values to pass to request header
    # blacklist: titles that you want to exclude(service articles for example)
    # data: if you want to pass data manually, maybe because you need some custom replacement
    # patronBlock: patron to get parts of the page (to scrape with patron attribute),
    #               if you need a "block inside another block" you can create a list, please note that all matches
    #               will be packed as string
    # patronNext: patron for scraping next page link
    # action: if you want results perform an action different from "findvideos", useful when scraping film by genres
    # addVideolibrary: if "add to videolibrary" should appear
    # example usage:
    #   import support
    #   itemlist = []
    #   patron = 'blablabla'
    #   headers = [['Referer', host]]
    #   blacklist = 'Request a TV serie!'
    #   return support.scrape(item, itemlist, patron, ['thumb', 'quality', 'url', 'title', 'year', 'plot', 'episode', 'lang'],
    #                           headers=headers, blacklist=blacklist)
    # 'type' is a check for typologies of content e.g. Film or TV Series
    # 'episode' is a key to grab episode numbers if it is separated from the title
    # IMPORTANT 'type' is a special key, to work need typeContentDict={} and typeActionDict={}

    def wrapper(*args):
        itemlist = []

        args = func(*args)
        function = func.__name__ if not 'actLike' in args else args['actLike']
        # log('STACK= ',inspect.stack()[1][3])

        item = args['item']

        action = args['action'] if 'action' in args else 'findvideos'
        anime = args['anime'] if 'anime' in args else ''
        addVideolibrary = args['addVideolibrary'] if 'addVideolibrary' in args else True
        search = args['search'] if 'search' in args else ''
        blacklist = args['blacklist'] if 'blacklist' in args else []
        data = args['data'] if 'data' in args else ''
        patron = args['patron'] if 'patron' in args else args['patronMenu'] if 'patronMenu' in args else ''
        if 'headers' in args:
            headers = args['headers']
        elif 'headers' in func.__globals__:
            headers = func.__globals__['headers']
        else:
            headers = ''
        patronNext = args['patronNext'] if 'patronNext' in args else ''
        patronBlock = args['patronBlock'] if 'patronBlock' in args else ''
        typeActionDict = args['typeActionDict'] if 'typeActionDict' in args else {}
        typeContentDict = args['typeContentDict'] if 'typeContentDict' in args else {}
        debug = args['debug'] if 'debug' in args else False
        if 'pagination' in args and inspect.stack()[1][3] not in ['add_tvshow', 'get_episodes', 'update', 'find_episodes']: pagination = args['pagination'] if args['pagination'] else 20
        else: pagination = ''
        lang = args['deflang'] if 'deflang' in args else ''
        pag = item.page if item.page else 1  # pagination
        matches = []

        log('PATRON= ', patron)
        if not data:
            data = httptools.downloadpage(item.url, headers=headers, ignore_response_code=True).data.replace("'", '"')
            data = re.sub('\n|\t', ' ', data)
            data = re.sub(r'>\s+<', '> <', data)
            # replace all ' with " and eliminate newline, so we don't need to worry about
            log('DATA =', data)

        if patronBlock:
            blocks = scrapertoolsV2.find_multiple_matches_groups(data, patronBlock)
            block = ""
            for bl in blocks:
                blockItemlist, blockMatches = scrapeBlock(item, args, bl['block'], patron, headers, action, pagination, debug,
                                            typeContentDict, typeActionDict, blacklist, search, pag, function, lang)
                for it in blockItemlist:
                    if 'lang' in bl:
                        it.contentLanguage, it.title = scrapeLang(bl, it.contentLanguage, it.title)
                    if 'quality' in bl and bl['quality']:
                        it.quality = bl['quality'].strip()
                        it.title = it.title + typo(bl['quality'].strip(), '_ [] color kod')
                log('BLOCK ', '=', block)
                itemlist.extend(blockItemlist)
                matches.extend(blockMatches)
        elif patron:
            itemlist, matches = scrapeBlock(item, args, data, patron, headers, action, pagination, debug, typeContentDict,
                                   typeActionDict, blacklist, search, pag, function, lang)

        if 'itemlistHook' in args:
            itemlist = args['itemlistHook'](itemlist)

        if (pagination and len(matches) <= pag * pagination) or not pagination: # next page with pagination
            if patronNext and inspect.stack()[1][3] != 'newest':
                nextPage(itemlist, item, data, patronNext, function)

        # next page for pagination
        if pagination and len(matches) > pag * pagination and not search:
            if inspect.stack()[1][3] != 'get_newest':
                itemlist.append(
                    Item(channel=item.channel,
                         action = item.action,
                         contentType=item.contentType,
                         title=typo(config.get_localized_string(30992), 'color kod bold'),
                         fulltitle= item.fulltitle,
                         show= item.show,
                         url=item.url,
                         args=item.args,
                         page=pag + 1,
                         thumbnail=thumb()))

        if action != 'play' and function != 'episodios' and 'patronMenu' not in args:
            tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

        from specials import autorenumber
        if anime:
            if function == 'episodios' or item.action == 'episodios': autorenumber.renumber(itemlist, item, 'bold')
            else: autorenumber.renumber(itemlist)
        if anime and autorenumber.check(item) == False and not scrapertoolsV2.find_single_match(itemlist[0].title, r'(\d+.\d+)'):
            pass
        else:
            if addVideolibrary and (item.infoLabels["title"] or item.fulltitle):
                # item.fulltitle = item.infoLabels["title"]
                videolibrary(itemlist, item, function=function)
            if config.get_setting('downloadenabled') and (function == 'episodios' or function == 'findvideos'):
                download(itemlist, item, function=function)

        if 'patronMenu' in args:
            itemlist = thumb(itemlist, genre=True)

        if 'fullItemlistHook' in args:
            itemlist = args['fullItemlistHook'](itemlist)

        # itemlist = filterLang(item, itemlist)   # causa problemi a newest

        return itemlist

    return wrapper


def dooplay_get_links(item, host):
    # get links from websites using dooplay theme and dooplay_player
    # return a list of dict containing these values: url, title and server

    data = httptools.downloadpage(item.url).data.replace("'", '"')
    patron = r'<li id="player-option-[0-9]".*?data-type="([^"]+)" data-post="([^"]+)" data-nume="([^"]+)".*?<span class="title".*?>([^<>]+)</span>(?:<span class="server">([^<>]+))?'
    matches = scrapertoolsV2.find_multiple_matches(data, patron)

    ret = []

    for type, post, nume, title, server in matches:
        postData = urllib.urlencode({
            "action": "doo_player_ajax",
            "post": post,
            "nume": nume,
            "type": type
        })
        dataAdmin = httptools.downloadpage(host + '/wp-admin/admin-ajax.php', post=postData,headers={'Referer': item.url}).data
        link = scrapertoolsV2.find_single_match(dataAdmin, "<iframe.*src='([^']+)'")
        ret.append({
            'url': link,
            'title': title,
            'server': server
        })

    return ret


@scrape
def dooplay_get_episodes(item):
    item.contentType = 'tvshow'
    patron = '<li class="mark-[0-9]+">.*?<img.*?(?:data-lazy-)?src="(?P<thumb>[^"]+).*?(?P<episode>[0-9]+ - [0-9]+).*?<a href="(?P<url>[^"]+)">(?P<title>[^<>]+).*?(?P<year>[0-9]{4})'
    actLike = 'episodios'

    return locals()


@scrape
def dooplay_peliculas(item, mixed=False, blacklist=""):
    actLike = 'peliculas'
    if item.args == 'searchPage':
        return dooplay_search_vars(item, blacklist)
    else:
        if item.contentType == 'movie':
            action = 'findvideos'
            patron = '<article id="post-[0-9]+" class="item movies">.*?<img src="(?!data)(?P<thumb>[^"]+)".*?<span class="quality">(?P<quality>[^<>]+).*?<a href="(?P<url>[^"]+)">(?P<title>[^<>]+)</a></h3>.*?(?:<span>[^<>]*(?P<year>[0-9]{4})</span>|</article>)'
        else:
            action = 'episodios'
            patron = '<article id="post-[0-9]+" class="item (?P<type>' + ('\w+' if mixed else 'tvshows') + ')">.*?<img src="(?!data)(?P<thumb>[^"]+)".*?(?:<span class="quality">(?P<quality>[^<>]+))?.*?<a href="(?P<url>[^"]+)">(?P<title>[^<>]+)</a></h3>.*?(?:<span>(?P<year>[0-9]{4})</span>|</article>).*?(?:<div class="texto">(?P<plot>[^<>]+)|</article>).*?(?:genres">(?P<genre>.*?)</div>|</article>)'
        patronNext = '<div class="pagination">.*?class="current".*?<a href="([^"]+)".*?<div class="resppages">'
        addVideolibrary = False

        if mixed:
            typeActionDict={'findvideos': ['movies'], 'episodios': ['tvshows']}
            typeContentDict={'film': ['movies'], 'serie': ['tvshows']}

        return locals()


@scrape
def dooplay_search(item, blacklist=""):
    return dooplay_search_vars(item, blacklist)


def dooplay_search_vars(item, blacklist):
    if item.contentType == 'list':  # ricerca globale
        type = '(?P<type>movies|tvshows)'
        typeActionDict = {'findvideos': ['movies'], 'episodios': ['tvshows']}
        typeContentDict = {'movie': ['movies'], 'tvshow': ['tvshows']}
    elif item.contentType == 'movie':
        type = 'movies'
        action = 'findvideos'
    else:
        type = 'tvshows'
        action = 'episodios'
    patron = '<div class="result-item">.*?<img src="(?P<thumb>[^"]+)".*?<span class="' + type + '">(?P<quality>[^<>]+).*?<a href="(?P<url>[^"]+)">(?P<title>[^<>]+)</a>.*?<span class="year">(?P<year>[0-9]{4}).*?<div class="contenido"><p>(?P<plot>[^<>]+)'
    patronNext = '<a class="arrow_pag" href="([^"]+)"><i id="nextpagination"'

    return locals()

def swzz_get_url(item):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:59.0) Gecko/20100101 Firefox/59.0'}

    if "/link/" in item.url:
        data = httptools.downloadpage(item.url, headers=headers).data
        if "link =" in data:
            data = scrapertoolsV2.find_single_match(data, 'link = "([^"]+)"')
            if 'http' not in data:
                data = 'https:' + data
        else:
            match = scrapertoolsV2.find_single_match(data, r'<meta name="og:url" content="([^"]+)"')
            match = scrapertoolsV2.find_single_match(data, r'URL=([^"]+)">') if not match else match

            if not match:
                from lib import jsunpack

                try:
                    data = scrapertoolsV2.find_single_match(data.replace('\n', ''), r"(eval\s?\(function\(p,a,c,k,e,d.*?)</script>")
                    data = jsunpack.unpack(data)

                    logger.debug("##### play /link/ unpack ##\n%s\n##" % data)
                except:
                    logger.debug("##### The content is yet unpacked ##\n%s\n##" % data)

                data = scrapertoolsV2.find_single_match(data, r'var link(?:\s)?=(?:\s)?"([^"]+)";')
                data, c = unshortenit.unwrap_30x_only(data)
            else:
                data = match
        if data.startswith('/'):
            data = urlparse.urljoin("http://swzz.xyz", data)
            if not "vcrypt" in data:
                data = httptools.downloadpage(data).data
        logger.debug("##### play /link/ data ##\n%s\n##" % data)
    else:
        data = item.url

    return data


def menuItem(itemlist, filename, title='', action='', url='', contentType='movie', args=[]):
    # Function to simplify menu creation

    # Call typo function
    title = typo(title)

    if contentType == 'movie': extra = 'movie'
    else: extra = 'tvshow'

    itemlist.append(Item(
        channel = filename,
        title = title,
        action = action,
        url = url,
        extra = extra,
        args = args,
        contentType = contentType
    ))

    # Apply auto Thumbnails at the menus
    from channelselector import thumb
    thumb(itemlist)
    return itemlist


def menu(func):
    def wrapper(*args):
        log()
        args = func(*args)

        item = args['item']
        host = func.__globals__['host']
        list_servers = func.__globals__['list_servers']
        list_quality = func.__globals__['list_quality']
        filename = func.__module__.split('.')[1]

        # listUrls = ['film', 'filmSub', 'tvshow', 'tvshowSub', 'anime', 'animeSub', 'search', 'top', 'topSub']
        listUrls = ['top', 'film', 'tvshow', 'anime', 'search']
        listUrls_extra = []
        dictUrl = {}


        # Main options
        itemlist = []

        for name in listUrls:
            dictUrl[name] = args[name] if name in args else None
            log(dictUrl[name])
            if name == 'film': title = 'Film'
            if name == 'tvshow': title = 'Serie TV'
            if name == 'anime': title = 'Anime'

            if name == 'search' and dictUrl[name] is not None:
                menuItem(itemlist, filename, 'Cerca… bold', 'search', host + dictUrl['search'])

            # Make TOP MENU
            elif name == 'top' and dictUrl[name] is not None:
                for sub, var in dictUrl['top']:
                    menuItem(itemlist, filename,
                             title = sub + ' italic bold',
                             url = host + var[0] if len(var) > 0 else '',
                             action = var[1] if len(var) > 1 else 'peliculas',
                             args=var[2] if len(var) > 2 else '',
                             contentType= var[3] if len(var) > 3 else 'movie',)

            # Make MAIN MENU
            elif dictUrl[name] is not None:
                if len(dictUrl[name]) == 0: url = ''
                else: url = dictUrl[name][0] if type(dictUrl[name][0]) is not tuple and len(dictUrl[name][0]) > 0 else ''
                menuItem(itemlist, filename,
                         title + ' bullet bold', 'peliculas',
                         host + url,
                         contentType='movie' if name == 'film' else 'tvshow')
                if len(dictUrl[name]) > 0:
                    if type(dictUrl[name][0]) is not tuple and type(dictUrl[name]) is not str: dictUrl[name].pop(0)
                if dictUrl[name] is not None and type(dictUrl[name]) is not str:
                    for sub, var in dictUrl[name]:
                        menuItem(itemlist, filename,
                             title = sub + ' submenu' + typo(title,'_ {}'),
                             url = host + var[0] if len(var) > 0 else '',
                             action = var[1] if len(var) > 1 else 'peliculas',
                             args=var[2] if len(var) > 2 else '',
                             contentType= var[3] if len(var) > 3 else 'movie' if name == 'film' else 'tvshow',)
                # add search menu for category
                if 'search' not in args: menuItem(itemlist, filename, 'Cerca ' + title + '… submenu bold', 'search', host + url, contentType='movie' if name == 'film' else 'tvshow')

        # Make EXTRA MENU (on bottom)
        for name, var in args.items():
            if name not in listUrls and name != 'item':
               listUrls_extra.append(name)
        for name in listUrls_extra:
            dictUrl[name] = args[name] if name in args else None
            for sub, var in dictUrl[name]:
                menuItem(itemlist, filename,
                             title = sub + ' ',
                             url = host + var[0] if len(var) > 0 else '',
                             action = var[1] if len(var) > 1 else 'peliculas',
                             args=var[2] if len(var) > 2 else '',
                             contentType= var[3] if len(var) > 3 else 'movie',)


        autoplay.init(item.channel, list_servers, list_quality)
        autoplay.show_option(item.channel, itemlist)
        channel_config(item, itemlist)

        return itemlist

    return wrapper


def typo(string, typography=''):

    kod_color = '0xFF65B3DA' #'0xFF0081C2'
    try: string = str(string)
    except: string = str(string.encode('utf8'))
    # Check if the typographic attributes are in the string or outside
    if typography:
        string = string + ' ' + typography
    if config.get_localized_string(30992) in string:
        string = string + ' >'

    # If there are no attributes, it applies the default ones
    attribute = ['[]','()','{}','submenu','color','bold','italic','_','--','[B]','[I]','[COLOR]']

    movie_word_list = ['film', 'serie', 'tv', 'anime', 'cinema', 'sala']
    search_word_list = ['cerca']
    categories_word_list = ['genere', 'categoria', 'categorie', 'ordine', 'lettera', 'anno', 'alfabetico', 'a-z', 'menu']

    if not any(word in string for word in attribute):
        if any(word in string.lower() for word in search_word_list):
            string = '[COLOR '+ kod_color +']' + string + '[/COLOR]'
        elif any(word in string.lower() for word in categories_word_list):
            string = ' > ' + string
        elif any(word in string.lower() for word in movie_word_list):
            string = '[B]' + string + '[/B]'

    # Otherwise it uses the typographical attributes of the string
    else:
        if '[]' in string:
            string = '[' + re.sub(r'\s\[\]','',string) + ']'
        if '()' in string:
            string = '(' + re.sub(r'\s\(\)','',string) + ')'
        if '{}' in string:
            string = '{' + re.sub(r'\s\{\}','',string) + '}'
        if 'submenu' in string:
            string = u"\u2022\u2022 ".encode('utf-8') + re.sub(r'\ssubmenu','',string)
        if 'color' in string:
            color = scrapertoolsV2.find_single_match(string,'color ([a-z]+)')
            if color == 'kod' or '': color = kod_color
            string = '[COLOR '+ color +']' + re.sub(r'\scolor\s([a-z]+)','',string) + '[/COLOR]'
        if 'bold' in string:
            string = '[B]' + re.sub(r'\sbold','',string) + '[/B]'
        if 'italic' in string:
            string = '[I]' + re.sub(r'\sitalic','',string) + '[/I]'
        if '_' in string:
            string = ' ' + re.sub(r'\s_','',string)
        if '--' in string:
            string = ' - ' + re.sub(r'\s--','',string)
        if 'bullet' in string:
            string = '[B]' + u"\u2022".encode('utf-8') + '[/B] ' + re.sub(r'\sbullet','',string)

    return string


def match(item, patron='', patronBlock='', headers='', url='', post=''):
    matches = []
    if type(item) == str:
        data = item
    else:
        url = url if url else item.url
        if post:
            data = httptools.downloadpage(url, headers=headers, ignore_response_code=True, post=post).data.replace("'", '"')
        else:
            data = httptools.downloadpage(url, headers=headers, ignore_response_code=True).data.replace("'", '"')
    data = re.sub(r'\n|\t', ' ', data)
    data = re.sub(r'>\s\s*<', '><', data)
    log('DATA= ', data)

    if patronBlock:
        block = scrapertoolsV2.find_single_match(data, patronBlock)
        log('BLOCK= ',block)
    else:
        block = data

    if patron:
        matches = scrapertoolsV2.find_multiple_matches(block, patron)
        log('MATCHES= ',matches)

    return matches, block


def download(itemlist, item, typography='', function_level=1, function=''):
    if not typography: typography = 'color kod bold'

    if item.contentType == 'movie':
        from_action = 'findvideos'
        title = typo(config.get_localized_string(60354), typography)
    elif item.contentType == 'episode':
        from_action = 'findvideos'
        title = typo(config.get_localized_string(60356), typography) + ' - ' + item.title
    else:
        from_action = 'episodios'
        title = typo(config.get_localized_string(60355), typography)

    function = function if function else inspect.stack()[function_level][3]

    contentSerieName=item.contentSerieName if item.contentSerieName else ''
    contentTitle=item.contentTitle if item.contentTitle else ''

    if itemlist and item.contentChannel != 'videolibrary':
        itemlist.append(
            Item(channel='downloads',
                from_channel=item.channel,
                title=title,
                fulltitle=item.fulltitle,
                show=item.fulltitle,
                contentType=item.contentType,
                contentSerieName=contentSerieName,
                url=item.url,
                action='save_download',
                from_action=from_action,
                contentTitle=contentTitle,
                path=item.path
            ))
        if from_action == 'episodios':
            itemlist.append(
                Item(channel='downloads',
                    from_channel=item.channel,
                    title=typo(config.get_localized_string(60357),typography),
                    fulltitle=item.fulltitle,
                    show=item.fulltitle,
                    contentType=item.contentType,
                    contentSerieName=contentSerieName,
                    url=item.url,
                    action='save_download',
                    from_action=from_action,
                    contentTitle=contentTitle,
                    download='season'
                ))

    return itemlist


def videolibrary(itemlist, item, typography='', function_level=1, function=''):
    # Simply add this function to add video library support
    # Function_level is useful if the function is called by another function.
    # If the call is direct, leave it blank
    log()

    if item.contentType == 'movie':
        action = 'add_pelicula_to_library'
        extra = 'findvideos'
        contentType = 'movie'
    else:
        action = 'add_serie_to_library'
        extra = 'episodios'
        contentType = 'tvshow'

    function = function if function else inspect.stack()[function_level][3]

    if not typography: typography = 'color kod bold'

    title = typo(config.get_localized_string(30161), typography)
    contentSerieName=item.contentSerieName if item.contentSerieName else ''
    contentTitle=item.contentTitle if item.contentTitle else ''

    if (function == 'findvideos' and contentType == 'movie') \
        or (function == 'episodios' and contentType != 'movie') \
        or function == 'get_seasons' and item.channel == 'community':
        if config.get_videolibrary_support() and len(itemlist) > 0:
            itemlist.append(
                Item(channel=item.channel,
                        title=title,
                        fulltitle=item.fulltitle,
                        show=item.fulltitle,
                        contentType=contentType,
                        contentSerieName=contentSerieName,
                        url=item.url,
                        action=action,
                        extra=extra,
                        contentTitle=contentTitle,
                        path=item.path
                        ))

    return itemlist

def nextPage(itemlist, item, data='', patron='', function_or_level=1, next_page='', resub=[]):
    # Function_level is useful if the function is called by another function.
    # If the call is direct, leave it blank
    action = inspect.stack()[function_or_level][3] if type(function_or_level) == int else function_or_level
    if next_page == '':
        next_page = scrapertoolsV2.find_single_match(data, patron)

    if next_page != "":
        if resub: next_page = re.sub(resub[0], resub[1], next_page)
        if 'http' not in next_page:
            next_page = scrapertoolsV2.find_single_match(item.url, 'https?://[a-z0-9.-]+') + next_page
        next_page = re.sub('&amp;', '&',next_page)
        log('NEXT= ', next_page)
        itemlist.append(
            Item(channel=item.channel,
                 action = action,
                 contentType=item.contentType,
                 title=typo(config.get_localized_string(30992), 'color kod bold'),
                 url=next_page,
                 args=item.args,
                 thumbnail=thumb()))

    return itemlist

def pagination(itemlist, item, page, perpage, function_level=1):
    if len(itemlist) >= page * perpage:
        itemlist.append(
            Item(channel=item.channel,
                 action=inspect.stack()[function_level][3],
                 contentType=item.contentType,
                 title=typo(config.get_localized_string(30992), 'color kod bold'),
                 url=item.url,
                 args=item.args,
                 page=page + 1,
                 thumbnail=thumb()))
    return itemlist

def server(item, data='', itemlist=[], headers='', AutoPlay=True, CheckLinks=True, down_load=True):

    if not data and not itemlist:
        data = httptools.downloadpage(item.url, headers=headers, ignore_response_code=True).data

    itemList = servertools.find_video_items(data=str(data))
    itemlist = itemlist + itemList

    verifiedItemlist = []
    for videoitem in itemlist:
        if not videoitem.server:
            findS = servertools.findvideos(videoitem.url)
            if findS:
                findS = findS[0]
            else:
                log(videoitem, 'Non supportato')
                continue
            videoitem.server = findS[2]
            videoitem.title = findS[0]
            videoitem.url = findS[1]
        item.title = item.contentTitle.strip() if item.contentType == 'movie' or (
                    config.get_localized_string(30161) in item.title) else item.title
        videoitem.title = item.title + (typo(videoitem.title, '_ color kod []') if videoitem.title else "") + (typo(videoitem.quality, '_ color kod []') if videoitem.quality else "")
        videoitem.fulltitle = item.fulltitle
        videoitem.show = item.show
        videoitem.thumbnail = item.thumbnail
        videoitem.channel = item.channel
        videoitem.contentType = item.contentType
        verifiedItemlist.append(videoitem)

    return controls(verifiedItemlist, item, AutoPlay, CheckLinks, down_load)

def controls(itemlist, item, AutoPlay=True, CheckLinks=True, down_load=True):
    from core import jsontools
    from platformcode.config import get_setting

    CL = get_setting('checklinks') or get_setting('checklinks', item.channel)
    autoplay_node = jsontools.get_node_from_file('autoplay', 'AUTOPLAY')
    channel_node = autoplay_node.get(item.channel, {})
    if not channel_node:  # non ha mai aperto il menu del canale quindi in autoplay_data.json non c'e la key
        channelFile = __import__('channels.' + item.channel, fromlist=["channels.%s" % item.channel])
        autoplay.init(item.channel, channelFile.list_servers, channelFile.list_quality)

    autoplay_node = jsontools.get_node_from_file('autoplay', 'AUTOPLAY')
    channel_node = autoplay_node.get(item.channel, {})
    settings_node = channel_node.get('settings', {})
    AP = get_setting('autoplay') or settings_node['active']

    if CL and not AP:
        if get_setting('checklinks', item.channel):
            checklinks = get_setting('checklinks', item.channel)
        else:
            checklinks = get_setting('checklinks')
        if get_setting('checklinks_number', item.channel):
            checklinks_number = get_setting('checklinks_number', item.channel)
        else:
            checklinks_number = get_setting('checklinks_number')
        itemlist = servertools.check_list_links(itemlist, checklinks_number)

    if AutoPlay == True and inspect.stack()[4][3] != 'start_download':
        autoplay.start(itemlist, item)

    if item.contentChannel != 'videolibrary': videolibrary(itemlist, item, function_level=3)
    if get_setting('downloadenabled') and down_load == True: download(itemlist, item, function_level=3)
    return itemlist

def filterLang(item, itemlist):
    import channeltools
    list_language = channeltools.get_lang(item.channel)
    if len(list_language) > 1:
        from specials import filtertools
        itemlist = filtertools.get_links(itemlist, item, list_language)
    return itemlist

def aplay(item, itemlist, list_servers='', list_quality=''):
    if inspect.stack()[1][3] == 'mainlist':
        autoplay.init(item.channel, list_servers, list_quality)
        autoplay.show_option(item.channel, itemlist)
    else:
        autoplay.start(itemlist, item)


def log(stringa1="", stringa2="", stringa3="", stringa4="", stringa5=""):
    # Function to simplify the log
    # Automatically returns File Name and Function Name

    frame = inspect.stack()[1]
    filename = frame[0].f_code.co_filename
    filename = os.path.basename(filename)
    logger.info("[" + filename + "] - [" + inspect.stack()[1][3] + "] " + str(stringa1) + ( ' ' + str(stringa2) if stringa2 else '') + ( ' ' + str(stringa3) if stringa3 else '') + ( ' ' + str(stringa4) if stringa4 else '') + ( ' ' + str(stringa5) if stringa5 else '') )


def channel_config(item, itemlist):
    from  channelselector import get_thumb
    itemlist.append(
        Item(channel='setting',
             action="channel_config",
             title=typo("Configurazione Canale color kod bold"),
             config=item.channel,
             folder=False,
             thumbnail=get_thumb('setting_0.png'))
    )


def extract_wrapped(decorated):
    from types import FunctionType
    closure = (c.cell_contents for c in decorated.__closure__)
    return next((c for c in closure if isinstance(c, FunctionType)), None)
