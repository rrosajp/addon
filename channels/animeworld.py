# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per animeworld
# ----------------------------------------------------------



from core import  support, jsontools

__channel__ = "animeworld"
host = support.config.get_channel_url(__channel__)
headers = [['Referer', host]]

IDIOMAS = {'Italiano': 'Italiano'}
list_language = IDIOMAS.values()
list_servers = ['animeworld', 'verystream', 'streamango', 'openload', 'directo']
list_quality = ['default', '480p', '720p', '1080p']


def order():
    return str(support.config.get_setting("order", __channel__))


@support.menu
def mainlist(item):
    anime=['/filter?sort=',
           ('ITA',['/filter?language[]=1&sort=', 'build_menu', 'order']),
           ('SUB-ITA',['/filter?language[]=0&sort=', 'build_menu', 'order']),
           ('In Corso', ['/ongoing', 'peliculas']),
           ('Ultimi Episodi', ['/updated', 'peliculas', 'updated']),
           ('Nuove Aggiunte',['/newest', 'peliculas' ]),
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
        support.menuItem(itemlist, __channel__, support.typo(title, 'bold'), 'peliculas', host + '/filter?' + name + '=' + value + '&sort=' + order(), 'tvshow', args='sub')
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
    item.url = host + '/search?keyword=' + texto
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
        patron=r'<div class="inner">\s*<a href="(?P<url>[^"]+)" class[^>]+>\s*<img src="(?P<thumb>[^"]+)" alt?="(?P<title>[^\("]+)(?:\((?P<lang>[^\)]+)\))?"[^>]+>[^>]+>\s*(?:<div class="[^"]+">(?P<type>[^<]+)</div>)?[^>]+>[^>]+>\s*<div class="ep">[^\d]+(?P<episode>\d+)[^<]*</div>'
        action='findvideos'
    else:
        if item.args == 'order': item.url += order()
        patron= r'<div class="inner">\s*<a href="(?P<url>[^"]+)" class[^>]+>\s*<img src="(?P<thumb>[^"]+)" alt?="(?P<title>[^\("]+)(?:\((?P<lang>[^\)]+)\))?"[^>]+>[^>]+>[^>]+>[^>]+>\s*(?:<div class="[^"]+">(?P<type>[^<]+)</div>)?'
        action='episodios'
    def itemHook(item):
        support.log('Lingua= ',item.contentLanguage)
        if item.contentLanguage == '':
            item.contentLanguage = 'Sub-ITA'
            item.title += support.typo(item.contentLanguage,'_ [] color kod')
        return item
    patronNext=r'href="([^"]+)" rel="next"'
    type_content_dict={'movie':['movie']}
    type_action_dict={'findvideos':['movie']}    
    return locals()


@support.scrape
def episodios(item):
    anime=True
    patronBlock= r'server  active(?P<block>.*?)server  hidden ' 
    patron = r'<li><a [^=]+="[^"]+"[^=]+="[^"]+"[^=]+="[^"]+"[^=]+="[^"]+"[^=]+="[^"]+" href="(?P<url>[^"]+)"[^>]+>(?P<episode>[^<]+)<'
    def itemHook(item):
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
        number = support.scrapertoolsV2.find_single_match(item.title,r'(\d+) -')
        block = support.scrapertoolsV2.find_multiple_matches(data,'data-id="' + serverid + '">(.*?)<div class="server')
        ID = support.scrapertoolsV2.find_single_match(str(block),r'<a data-id="([^"]+)" data-base="' + (number if number else '1') + '"')
        if id:
            dataJson = support.httptools.downloadpage('%s/ajax/episode/info?id=%s&server=%s&ts=%s' % (host, ID, serverid, int(time.time())), headers=[['x-requested-with', 'XMLHttpRequest']]).data
            json = jsontools.load(dataJson)
            videoData +='\n'+json['grabber']

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

    return support.server(item, videoData, itemlist)

