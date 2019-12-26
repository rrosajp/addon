# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# XBMC Plugin
# Canale  per cineblog01 - anime
# ------------------------------------------------------------

from core import support

host = support.config.get_channel_url() + '/anime'

Blacklist = ['AVVISO IMPORTANTE – CB01.ROCKS', 'Lista Alfabetica Completa Anime/Cartoon', 'CB01.UNO ▶ TROVA L’INDIRIZZO UFFICIALE','Lista Richieste Up &amp; Re-Up']
list_servers = ['verystream', 'openload', 'streamango', 'thevideome']
list_quality = ['1080p', '720p', '480p', '360']

checklinks = support.config.get_setting('checklinks', __channel__)
checklinks_number = support.config.get_setting('checklinks_number', __channel__)
headers = [['Referer', host]]

@support.menu
def mainlist(item):
    anime = [('Genere',['','menu', '2']),
             ('Per Lettera',['','menu', '1']),
             ('Per Anno',['','menu', '3']),
             ('Ultimi Anime Aggiornati',['','peliculas', 'newest'])]
    return locals()


@support.scrape
def menu(item):
    blacklist = ['Anime per Genere', 'Anime per Anno', 'Anime per Lettera']
    patronBlock = r'<select name="select%s"(?P<block>.*?)</select>' % item.args
    patronMenu = r'<option value="(?P<url>[^"]+)">(?P<title>[^<]+)</option>'
    action = 'peliculas'
    return locals()


def search(item, texto):
    support.log(texto)
    item.url = host + "/?s=" + texto
    return peliculas(item)

def newest(categoria):
    support.log(categoria)
    itemlist = []
    item = support.Item()
    try:
        if categoria == "anime":
            item.url = host
            item.args = 'newest'
            itemlist = peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("{0}".format(line))
        return []

    return itemlist

@support.scrape
def peliculas(item):
    blacklist = Blacklist
    item.contentType = 'tvshow'
    if item.args == 'newest':
        data = support.match(item)[1]
        patron = r'<div id="blockvids"><ul><li><a href="(?P<url>[^"]+)"[^>]+><img src="(?P<thumb>[^"]+)"[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<title>[^\[]+)\[(?P<lang>[^\]]+)\]'
    else:
        patron = r'<div class="span4">\s*<a href="(?P<url>[^"]+)"><img src="(?P<thumb>[^"]+)"[^>]+><\/a>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+> <h1>(?P<title>[^<\[]+)(?:\[(?P<lang>[^\]]+)\])?</h1></a>.*?-->(?:.*?<br />)?\s*(?P<plot>[^<]+)'
        patronNext = r'<link rel="next" href="([^"]+)"'
    action = 'check'
    return locals()

def check(item):
    item.url = support.match(item,r'(?:<p>|/>)(.*?)(?:<br|</td>|</p>)', r'Streaming:(.*?)</tr>')[0]
    if 'Episodio' in str(item.url):
        item.contentType = 'tvshow'
        return episodios(item)
    else:
        item.contentType = 'movie'
        return findvideos(item)

@support.scrape
def episodios(item):
    support.log('EPISODIOS ', item.data)
    data = ''
    matches = item.data
    season = 1
    s = 1
    e = 0
    sp = 0
    for match in item.url:
        if 'stagione' in match.lower():
            find_season = support.match(match, r'Stagione\s*(\d+)')[0]
            season = int(find_season[0]) if find_season else season + 1 if 'prima' not in match.lower() else season
        else:
            try: title = support.match(match,'<a[^>]+>([^<]+)</a>')[0][0]
            except: title = ''
            if title:
                if 'episodio' in title.lower():
                    ep = support.match(match, r'Episodio ((?:\d+.\d|\d+|\D+))')[0][0]
                    check = ep.isdigit()
                    if check or '.' in ep:
                        if '.' in ep:
                            sp += 1
                            title = '0' + 'x' + str(sp).zfill(2) + ' - ' + title
                        else:
                            ep = int(ep)
                            if season > s and ep > 1:
                                s += 1
                                e = ep - 1
                            title = str(season) + 'x' + str(ep-e).zfill(2) + ' - ' + title
                        data += title + '|' + match + '\n'
                    else:
                        title += ' #movie'
                        data += title + '|' + match + '\n'
    def itemHook(item):
        if '#movie' in item.title:
            item.contentType='movie'
            item.title = item.title.replace(' #movie','')
        return item

    patron = r'(?P<title>[^\|]+)\|(?P<url>[^\n]+)\n'
    action = 'findvideos'
    return locals()

def findvideos(item):
    return support.server(item, item.url)

