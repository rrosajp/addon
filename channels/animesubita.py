# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per AnimeSubIta
# ------------------------------------------------------------


from core import support

host = support.config.get_channel_url()
headers = {'Upgrade-Insecure-Requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:52.0) Gecko/20100101 Firefox/52.0'}

list_servers = ['directo']
list_quality = ['default']


@support.menu
def mainlist(item):
    anime = ['/lista-anime/',
             ('Ultimi Episodi',['/category/ultimi-episodi/', 'peliculas', 'updated']),
             ('in Corso',['/category/anime-in-corso/', 'peliculas', 'alt']),
             ('Generi',['/generi/', 'genres', 'alt'])]
    return locals()


def newest(categoria):
    support.log(categoria)
    itemlist = []
    item = support.Item()
    try:
        if categoria == "anime":
            item.url = host
            item.args = "updated"
            itemlist = peliculas(item)

            if itemlist[-1].action == "ultimiep":
                itemlist.pop()
    # Continua l'esecuzione in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("{0}".format(line))
        return []

    return itemlist


def search(item, texto):
    support.log(texto)
    item.url = host + "/?s=" + texto
    item.args = 'alt'
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("%s" % line)
        return []


@support.scrape
def genres(item):
    blacklist= ['Anime In Corso','Ultimi Episodi']
    patronMenu=r'<li><a title="[^"]+" href="(?P<url>[^"]+)">(?P<title>[^<]+)</a>'
    action = 'peliculas'
    return locals()


@support.scrape
def peliculas(item):
    anime = True
    if item.args == 'updated':
        patron = r'<div class="post-thumbnail">\s*<a href="(?P<url>[^"]+)" title="(?P<title>.*?)\s*Episodio (?P<episode>\d+) (?P<lang>[a-zA-Z-\s]+)[^"]*"> <img[^src]+src="(?P<thumb>[^"]+)"'
        patronNext = r'<link rel="next" href="([^"]+)"\s*/>'
        action = 'findvideos'
    elif item.args == 'alt':
        patron = r'<div class="post-thumbnail">\s*<a href="(?P<url>[^"]+)" title="(?P<title>.*?)(?: [Oo][Aa][Vv])?(?:\s*(?P<lang>[Ss][Uu][Bb].[Ii][Tt][Aa]))[^"]+">\s*<img[^src]+src="(?P<thumb>[^"]+)"'
        patronNext = r'<link rel="next" href="([^"]+)"\s*/>'
        action = 'episodios'
    else:
        pagination = ''
        patronBlock = r'<ul class="lcp_catlist"[^>]+>(?P<block>.*?)</ul>'
        patron = r'<a href="(?P<url>[^"]+)"[^>]+>(?P<title>.*?)(?: [Oo][Aa][Vv])?(?:\s*(?P<lang>[Ss][Uu][Bb].[Ii][Tt][Aa])[^<]+)?</a>'
        action = 'episodios'
    return locals()


@support.scrape
def episodios(item):
    anime = True
    patron = r'<td style="[^"]*?">\s*.*?<strong>(?P<episode>[^<]+)</strong>\s*</td>\s*<td[^>]+>\s*<a href="(?P<url>[^"]+)"[^>]+>\s*<img src="(?P<thumb>[^"]+?)"[^>]+>'
    return locals()


def findvideos(item):
    support.log(item)
    itemlist = []

    if item.args == 'updated':
        ep = support.match(item.fulltitle, patron=r'(\d+)').match
        item.url = support.re.sub(r'episodio-\d+-|oav-\d+-'+ep, '',item.url)
        if 'streaming' not in item.url: item.url = item.url.replace('sub-ita','sub-ita-streaming')
        item.url = support.match(item, patron= ep + r'[^>]+>[^>]+>[^>]+><a href="([^"]+)"').match

    # post
    url = host + '/' + support.match(item.url, patron=r'(episodio\d*.php.*?)"').match.replace('%3F','?').replace('%3D','=')
    headers['Referer'] =  url
    cookies = ""
    matches = support.re.compile('(.%s.*?)\n' % host.replace("http://", "").replace("www.", ""), support.re.DOTALL).findall(support.config.get_cookie_data())
    for cookie in matches:
        cookies += cookie.split('\t')[5] + "=" + cookie.split('\t')[6] + ";"
    headers['Cookie'] = cookies[:-1]

    url = support.match(url, patron=r'<source src="([^"]+)"[^>]+>').match

    itemlist.append(
        support.Item(channel=item.channel,
                     action="play",
                     title='Diretto',
                     url=url + '|' + support.urllib.urlencode(headers),
                     server='directo'))

    return support.server(item,itemlist=itemlist)