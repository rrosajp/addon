# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per animeworld
# ----------------------------------------------------------

from core import  support, jsontools

host = support.config.get_channel_url()
headers = [['Referer', host]]

__channel__ = 'animeworld'

list_servers = ['directo', 'animeworld', 'vvvvid']
list_quality = ['default', '480p', '720p', '1080p']


def order():
    # Seleziona l'ordinamento dei risultati
    return str(support.config.get_setting("order", __channel__))


@support.menu
def mainlist(item):
    anime=['/filter?sort=',
           ('ITA',['/filter?language[]=1&sort=', 'build_menu', '1']),
           ('SUB-ITA',['/filter?language[]=0&sort=', 'build_menu', '0']),
           ('In Corso', ['/ongoing', 'peliculas','noorder']),
           ('Ultimi Episodi', ['/updated', 'peliculas', 'updated']),
           ('Nuove Aggiunte',['/newest', 'peliculas','noorder' ]),
           ('Generi',['','genres',])]
    return locals()


def genres(item):
    support.log()
    itemlist = []
    matches = support.match(item, r'<input.*?name="([^"]+)" value="([^"]+)"\s*>[^>]+>([^<]+)<\/label>' , r'<button class="btn btn-sm btn-default dropdown-toggle" data-toggle="dropdown"> Generi <span.[^>]+>(.*?)</ul>', headers=headers)[0]
    for name, value, title in matches:
        support.menuItem(itemlist, __channel__, support.typo(title, 'bold'), 'peliculas', host + '/filter?' + name + '=' + value + '&sort=' + order(), 'tvshow', args='sub')
    return itemlist


def build_menu(item):
    support.log()
    itemlist = []
    support.menuItem(itemlist, __channel__, 'Tutti bold', 'peliculas', item.url , 'tvshow' , args=item.args)
    matches = support.match(item,r'<button class="btn btn-sm btn-default dropdown-toggle" data-toggle="dropdown"> (.*?) <span.[^>]+>(.*?)</ul>',r'<form class="filters.*?>(.*?)</form>', headers=headers)[0]
    for title, html in matches:
        if title not in 'Lingua Ordine':
            support.menuItem(itemlist, __channel__, title + ' submenu bold', 'build_sub_menu', html, 'tvshow', args=item.args)
    return itemlist


def build_sub_menu(item):
    support.log()
    itemlist = []
    matches = support.re.compile(r'<input.*?name="([^"]+)" value="([^"]+)"\s*>[^>]+>([^<]+)<\/label>', support.re.DOTALL).findall(item.url)
    for name, value, title in matches:
        support.menuItem(itemlist, __channel__, support.typo(title, 'bold'), 'peliculas', host + '/filter?' + name + '=' + value + '&language[]=' + item.args + '&sort=', 'tvshow', args='sub')
    return itemlist


def newest(categoria):
    support.log(categoria)
    item = support.Item()
    try:
        if categoria == "anime":
            item.url = host + '/updated'
            item.args = "updated"
            return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("{0}".format(line))
        return []


def search(item, texto):
    support.log(texto)
    item.args = 'noorder'
    item.url = host + '/search?keyword=' + texto
    item.contentType = 'tvshow'
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("%s" % line)
        return []


@support.scrape
def peliculas(item):
    anime=True

    if item.args == 'updated':
        item.contentType='episode'
        patron=r'<div class="inner">\s*<a href="(?P<url>[^"]+)" class[^>]+>\s*<img src="(?P<thumb>[^"]+)" alt?="(?P<title>[^\("]+)(?:\((?P<lang>[^\)]+)\))?"[^>]+>[^>]+>\s*(?:<div class="[^"]+">(?P<type>[^<]+)</div>)?[^>]+>[^>]+>\s*<div class="ep">[^\d]+(?P<episode>\d+)[^<]*</div>'
        action='findvideos'
    else:
        if item.args != 'noorder' and not item.url[-1].isdigit(): item.url += order() # usa l'ordinamento di configura canale
        patron= r'<div class="inner">\s*<a href="(?P<url>[^"]+)" class[^>]+>\s*<img src="(?P<thumb>[^"]+)" alt?="(?P<title>[^\("]+)(?:\((?P<year>\d+)\) )?(?:\((?P<lang>[^\)]+)\))?"[^>]+>[^>]+>(?:\s*<div class="dub">[^>]+>)?\s*(?:<div class="[^"]+">(?P<type>[^<]+)</div>)?'
        action='episodios'

    # Controlla la lingua se assente
    patronNext=r'href="([^"]+)" rel="next"'
    type_content_dict={'movie':['movie', 'special']}
    type_action_dict={'findvideos':['movie', 'special']}
    check_lang = item.url
    def itemHook(item):
        if not item.contentLanguage:
            if 'language[]=1' in check_lang:
                item.contentLanguage = 'ITA'
                item.title += support.typo(item.contentLanguage,'_ [] color kod')
            else:
                item.contentLanguage = 'Sub-ITA'
                item.title += support.typo(item.contentLanguage,'_ [] color kod')
        return item


    return locals()


@support.scrape
def episodios(item):
    anime=True
    pagination = 50
    data = support.match(item, headers=headers)[1]
    if 'VVVVID' in data: patronBlock= r'<div class="server\s*active\s*"(?P<block>.*?)</ul>'
    else: patronBlock= r'server  active(?P<block>.*?)server  hidden '
    patron = r'<li><a [^=]+="[^"]+"[^=]+="[^"]+"[^=]+="[^"]+"[^=]+="[^"]+"[^=]+="[^"]+" href="(?P<url>[^"]+)"[^>]+>(?P<episode>[^<]+)<'
    def itemHook(item):
        item.number = support.re.sub(r'\[[^\]]+\]', '', item.title)
        item.title += support.typo(item.fulltitle,'-- bold')
        return item
    action='findvideos'
    return locals()


def findvideos(item):
    import time
    support.log(item)
    itemlist = []
    matches, data = support.match(item, r'class="tab.*?data-name="([0-9]+)">', headers=headers)
    videoData = ''
 
    for serverid in matches:
        if not item.number: item.number = support.scrapertools.find_single_match(item.title, r'(\d+) -')
        block = support.scrapertools.find_multiple_matches(data, 'data-id="' + serverid + '">(.*?)<div class="server')
        ID = support.scrapertools.find_single_match(str(block), r'<a data-id="([^"]+)" data-base="' + (item.number if item.number else '1') + '"')
        support.log('ID= ',serverid)
        if id:
            if serverid == '26':
                matches = support.match(item, r'<a href="([^"]+)"', url='%s/ajax/episode/serverPlayer?id=%s' % (host, item.url.split('/')[-1]))[0]
                for url in matches:
                        videoData += '\n' + url
            else:
                try:
                    dataJson = support.httptools.downloadpage('%s/ajax/episode/info?id=%s&server=%s&ts=%s' % (host, ID, serverid, int(time.time())), headers=[['x-requested-with', 'XMLHttpRequest']]).data
                    json = jsontools.load(dataJson)
                    support.log(json)
                    if 'keepsetsu' in json['grabber']:
                        matches = support.match(item, r'<iframe\s*src="([^"]+)"', url=json['grabber'])[0]
                        for url in matches:
                            videoData += '\n' + url
                    else:
                        videoData += '\n' + json['grabber']

                    if serverid == '28':
                        itemlist.append(
                            support.Item(
                                channel=item.channel,
                                action="play",
                                title='diretto',
                                quality='',
                                url=json['grabber'],
                                server='directo',
                                fulltitle=item.fulltitle,
                                show=item.show,
                                contentType=item.contentType,
                                folder=False))
                except:
                    pass

    return support.server(item, videoData, itemlist)

