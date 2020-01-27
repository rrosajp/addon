# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per SerieHD
# ------------------------------------------------------------


from core import scrapertools, httptools, support
from core.item import Item

host = support.config.get_channel_url()
headers = [['Referer', host]]


list_servers = ['mixdrop', 'vidoza', 'vcstream', 'gounlimited']
list_quality = ['1080p', '720p', '480p', '360']

@support.menu
def mainlist(item):

    tvshow = [('Genere', ['', 'menu', 'genre']),
              ('A-Z', ['', 'menu', 'a-z']),
              ('In Corso', ['/category/serie-tv-streaming/serie-in-corso', 'peliculas']),
              ('Complete', ['/category/serie-tv-streaming/serie-complete', 'peliculas']),
              ('Americane', ['/category/serie-tv-streaming/serie-tv-americane', 'peliculas']),
              ('Italiane', ['/category/serie-tv-streaming/serie-tv-italiane', 'peliculas']),
              ('Ultimi Episodi', ['/aggiornamenti', 'peliculas', 'last']),
              ('Evidenza', ['', 'peliculas', 'best'])]
    return locals()


def search(item, texto):
    support.log(texto)


    item.contentType = 'tvshow'
    item.url = host + "/?s=" + texto
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore .
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("%s" % line)
        return []


def newest(categoria):
    support.log(categoria)

    itemlist = []
    item = support.Item()
    item.url = host + '/aggiornamenti'
    item.args = 'last'
    try:
        if categoria == "series":
            item.contentType = 'tvshow'
            return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("{0}".format(line))
        return []

    return itemlist


@support.scrape
def peliculas(item):
    if item.args == 'last':
        action = 'findvideos'
        patron = r'singleUpdate">[^>]+>[^>]+>\s*<img src="(?P<thumb>[^"]+)"[^>]+>[^>]+>[^>]+>\s*<h2>(?P<title>[^<]+)<[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>\s*<a href="(?P<url>[^"]+)">[^>]+>[^>]+>[^>]+>\s*(?P<season>\d+)\D+(?P<episode>\d+)(?:[^\(]*\()?(?P<lang>[^\)]+)?(?:\))?'
    elif item.args == 'best':
        action='episodios'
        patron = r'col-md-3">\s*<a href="(?P<url>[^"]+)">[^>]+>\s*<div class="infoVetrina">[^>]+>(?P<year>\d{4})[^>]+>[^>]+>(?P<title>[^<]+)<[^>]+>[^>]+>[^>]+>[^>]+>(?P<rating>[^<]+)[^>]+>[^>]+>[^>]+>[^>]+>\s*<img src="(?P<thumb>[^"]+)"'
    else:
        action='episodios'
        patron = r'<a href="(?P<url>[^"]+)">[^>]+>\s*<div class="infoSeries">\s*<h2>(?P<title>[^<]+)<[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<rating>[^<]+)?[^>]+>[^>]+>[^>]+>\s*<img src="(?P<thumb>[^"]+)"[^>]+>[^>]+>[^>]+>(?P<quality>[^<]+)<[^>]+>[^>]+>(?P<year>\d{4})'
        patronNext=r'next page-numbers" href="([^"]+)"'

    return locals()


@support.scrape
def episodios(item):
    data =''
    url = support.match(item, patron=r'<iframe id="iframeVid" width="[^"]+" height="[^"]+" src="([^"]+)" allowfullscreen').match
    seasons = support.match(url, patron=r'<a href="([^"]+)">(\d+)<', patronBlock=r'<h3>STAGIONE</h3><ul>(.*?)</ul>', headers=headers).matches
    for season_url, season in seasons:
        season_url = support.urlparse.urljoin(url, season_url)
        episodes = support.match(season_url, patron=r'<a href="([^"]+)">(\d+(?:-\d+)?)<', patronBlock=r'<h3>EPISODIO</h3><ul>(.*?)</ul>', headers=headers).matches
        for episode_url, episode in episodes:
            episode_url = support.urlparse.urljoin(url, episode_url)
            if '-' in episode: episode = episode.split('-')[0].zfill(2) + 'x' + episode.split('-')[1].zfill(2)
            title = season + "x" + episode.zfill(2) + ' - ' + item.fulltitle
            data += title + '|' + episode_url + '\n'
    patron = r'(?P<title>[^\|]+)\|(?P<url>[^\n]+)\n'
    action = 'findvideos'
    return locals()


@support.scrape
def menu(item):
    if item.args == 'genre':
        patronMenu = r'<a href="(?P<url>[^"]+)">(?P<title>[^<]+)</a>'
    else:
        patronMenu = r'<a href="(?P<url>[^"]+)" class="">(?P<title>[^<]+)'

    blacklist = ['Serie TV Streaming','Serie TV Americane','Serie TV Italiane','Serie Complete','Serie in Corso','altadefinizione']
    action = 'peliculas'
    return locals()


def findvideos(item):
    support.log(item)
    if item.args == 'last':
        url = support.match(item, patron = r'<iframe id="iframeVid" width="[^"]+" height="[^"]+" src="([^"]+)" allowfullscreen').match
        matches = support.match(url,patron=r'<a href="([^"]+)">(\d+)<', patronBlock=r'<h3>EPISODIO</h3><ul>(.*?)</ul>').matches
        if matches: item.url = support.urlparse.urljoin(url, matches[-1][0])
    return support.hdpass_get_servers(item)
