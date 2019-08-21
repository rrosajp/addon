# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per AnimeSubIta
# ------------------------------------------------------------


from core import support

__channel__ = "animesubita"
host = support.config.get_channel_url(__channel__)
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
        patron = r'<div class="post-thumbnail">\s*<a href="(?P<url>[^"]+)" title="(?P<title>.*?)\s*(?P<episode>Episodio \d+)[^"]+"[^>]*>\s*<img[^src]+src="(?P<thumb>[^"]+)"'
        patronNext = r'<link rel="next" href="([^"]+)"\s*/>'
        action = 'findvideos'
    elif item.args == 'alt':
        # debug = True
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
        ep = support.match(item.fulltitle,r'(Episodio\s*\d+)')[0][0]
        item.url = support.re.sub(r'episodio-\d+-|oav-\d+-', '',item.url)
        if 'streaming' not in item.url: item.url = item.url.replace('sub-ita','sub-ita-streaming')
        item.url = support.match(item, r'<a href="([^"]+)"[^>]+>', ep + '(.*?)</tr>', )[0][0]

    urls = support.match(item.url, r'(episodio\d*.php.*)')[0]
    for url in urls:
        url = host + '/' + url
        headers['Referer'] =  url
        data = support.match(item, headers=headers, url=url)[1]
        cookies = ""
        matches = support.re.compile('(.%s.*?)\n' % host.replace("http://", "").replace("www.", ""), support.re.DOTALL).findall(support.config.get_cookie_data())
        for cookie in matches:
            cookies += cookie.split('\t')[5] + "=" + cookie.split('\t')[6] + ";"

        headers['Cookie'] = cookies[:-1]
        
        url = support.match(data, r'<source src="([^"]+)"[^>]+>')[0][0] + '|' + support.urllib.urlencode(headers)
        itemlist.append(
            support.Item(channel=item.channel,
                         action="play",
                         title='diretto',
                         quality='',
                         url=url,
                         server='directo',
                         fulltitle=item.fulltitle,
                         show=item.show))

    return support.server(item,url,itemlist)
