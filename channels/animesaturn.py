# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per AnimeSaturn
# Thanks to 4l3x87
# ----------------------------------------------------------

from core import support

__channel__ = "animesaturn"
host = support.config.get_setting("channel_host", __channel__)
headers={'X-Requested-With': 'XMLHttpRequest'}

IDIOMAS = {'Italiano': 'ITA'}
list_language = IDIOMAS.values()
list_servers = ['openload', 'fembed', 'animeworld']
list_quality = ['default', '480p', '720p', '1080p']

@support.menu
def mainlist(item):

    anime = ['/animelist?load_all=1',
             ('Più Votati',['/toplist','menu', 'top']),
             ('In Corso',['/animeincorso','peliculas','incorso']),
             ('Ultimi Episodi',['/fetch_pages.php?request=episodes','peliculas','updated'])]

    return locals()


@support.scrape
def search(item, texto):
    search = texto
    item.contentType = 'tvshow'
    anime = True
    patron = r'href="(?P<url>[^"]+)"[^>]+>[^>]+>(?P<title>[^<|(]+)(?:(?P<lang>\(([^\)]+)\)))?<|\)'
    action = 'check'
    return locals()


def newest(categoria):
    support.log()
    itemlist = []
    item = support.Item()
    try:
        if categoria == "anime":
            item.url = host + '/fetch_pages.php?request=episodes'
            item.args = "updated"
            return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("{0}".format(line))
        return []

    return itemlist

@support.scrape
def menu(item):
    patronMenu = r'u>(?P<title>[^<]+)<u>(?P<url>.*?)</div> </div>'
    action = 'peliculas'
    return locals()


@support.scrape
def peliculas(item):
    anime = True
    deflang= 'Sub-ITA'
    if item.args == 'updated':
        post = "page=" + str(item.page if item.page else 1) if item.page > 1 else None
        page, data = support.match(item, r'data-page="(\d+)" title="Next">', post=post, headers=headers)
        patron = r'<img alt="[^"]+" src="(?P<thumb>[^"]+)" [^>]+></div></a>\s*<a href="(?P<url>[^"]+)"><div class="testo">(?P<title>[^\(<]+)(?:(?P<lang>\(([^\)]+)\)))?</div></a>\s*<a href="[^"]+"><div class="testo2">[^\d]+(?P<episode>\d+)</div></a>'
        if page: nextpage = page
        item.contentType='episode'
        action = 'findvideos'
    elif item.args == 'top':
        data = item.url
        patron = r'<a href="(?P<url>[^"]+)">[^>]+>(?P<title>[^<\(]+)(?:\((?P<year>[0-9]+)\))?(?:\((?P<lang>[A-Za-z]+)\))?</div></a><div class="numero">(?P<title2>[^<]+)</div>.*?src="(?P<thumb>[^"]+)"'
        action = 'check'
    else:
        pagination = ''
        if item.args == 'incorso': patron = r'"slider_title" href="(?P<url>[^"]+)"><img src="(?P<thumb>[^"]+)"[^>]+>(?P<title>[^\(<]+)(?:\((?P<year>\d+)\))?</a>'
        else: patron = r'href="(?P<url>[^"]+)"[^>]+>[^>]+>(?P<title>.+?)(?:\((?P<lang>ITA)\))?(?:(?P<year>\((\d+)\)))?</span>'
        action = 'check'
    return locals()


def check(item):
    movie, data = support.match(item, r'Episodi:</b> (\d*) Movie')
    anime_id = support.match(data, r'anime_id=(\d+)')[0][0]
    item.url = host + "/loading_anime?anime_id=" + anime_id
    if movie:
        item.contentType = 'movie'
        episodes = episodios(item)
        if len(episodes) > 0: item.url = episodes[0].url
        return findvideos(item)
    else:
        item.contentType = 'tvshow'
        return episodios(item)


@support.scrape
def episodios(item):
    if item.contentType != 'movie': anime = True
    patron = r'<strong" style="[^"]+">(?P<title>[^<]+)</b></strong></td>\s*<td style="[^"]+"><a href="(?P<url>[^"]+)"'
    return locals()


def findvideos(item):
    support.log()
    itemlist = []
    urls = support.match(item, r'<a href="([^"]+)"><div class="downloadestreaming">', headers=headers)[0]
    if urls:
        links = support.match(item, r'(?:<source type="[^"]+"\s*src=|file:\s*)"([^"]+)"', url=urls[0], headers=headers)[0]
        for link in links:
            itemlist.append(
                support.Item(channel=item.channel,
                            action="play",
                            title='Diretto',
                            quality='',
                            url=link,
                            server='directo',
                            fulltitle=item.fulltitle,
                            show=item.show,
                            contentType=item.contentType,
                            folder=False))
    return support.server(item, itemlist=itemlist)









