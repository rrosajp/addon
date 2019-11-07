# -*- coding: utf-8 -*-
# ----------------------------------------------------------
# Canale per animetubeita
# ----------------------------------------------------------
import re
import urllib
from core import support

__channel__ = "animetubeita"
host = support.config.get_channel_url(__channel__)

headers = {'Upgrade-Insecure-Requests': '1',
               'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:52.0) Gecko/20100101 Firefox/52.0'}

list_servers = ['directo']
list_quality = ['default']

@support.menu
def mainlist(item):
	anime = [('Generi',['/generi', 'genres', 'genres']),
             ('Ordine Alfabetico',['/lista-anime', 'peliculas', 'list']),
             ('In Corso',['/category/serie-in-corso/', 'peliculas', 'in_progress'])
             ]
	return locals()

@support.scrape
def genres(item):
    blacklist = ['Ultimi Episodi', 'Serie in Corso']
    patronMenu = r'<li[^>]+><a href="(?P<url>[^"]+)" >(?P<title>[^<]+)</a>'
    action = 'peliculas'
    return locals()


def search(item, text):
    support.log(text)
    item.url = host + '/lista-anime'
    item.args = 'list'
    item.search = text
    try:
        return peliculas(item)
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("%s" % line)
        return []


def newest(categoria):
    support.log(categoria)
    item = support.Item()
    try:
        if categoria == "anime":
            item.contentType='tvshow'
            item.url = host
            item.args = "last"
            return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("{0}".format(line))
        return []


@support.scrape
def peliculas(item):
    anime = True
    if not item.search: pagination = ''
    action = 'episodios'

    if item.args == 'list':
        search = item.search
        patronBlock = r'<ul class="page-list ">(?P<block>.*?)<div class="wprc-container'
        patron = r'<li.*?class="page_.*?href="(?P<url>[^"]+)">(?P<title>.*?) Sub Ita'
    elif item.args == 'last':
        action = 'findvideos'
        item.contentType='episode'
        patronBlock = r'<div class="blocks">(?P<block>.*?)<div id="sidebar'
        patron = r'<h2 class="title"><a href="(?P<url>[^"]+)" [^>]+>.*?<img.*?src="(?P<thumb>[^"]+)".*?<strong>Titolo</strong></td>.*?<td>(?P<title>.*?)\s*Episodio\s*(?P<episode>\d+)[^<]+</td>.*?<td><strong>Trama</strong></td>\s*<td>(?P<plot>[^<]+)<'
    elif item.args in  ['in_progress','genres']:
        patronBlock = r'<div class="blocks">(?P<block>.*?)<div id="sidebar'
        patron = r'<h2 class="title"><a href="(?P<url>[^"]+)"[^>]+>(?P<title>.*?)\s* Sub Ita[^<]+</a></h2>.*?<img.*?src="(?P<thumb>.*?)".*?<td><strong>Trama</strong></td>.*?<td>(?P<plot>[^<]+)<'
        patronNext = r'href="([^"]+)" >&raquo;'
    else:
        patronBlock = r'<div class="blocks">(?P<block>.*?)<div id="sidebar'
        patron = r'<img.*?src="(?P<thumb>[^"]+)".*?<strong>Titolo</strong></td>.*?<td>\s*(?P<title>.*?)\s*Episodio[^<]+</td>.*?<td><strong>Trama</strong></td>\s*<td>(?P<plot>[^<]+)<.*?<a.*?href="(?P<url>[^"]+)"'
        patronNext = r'href="([^"]+)" >&raquo;'
    return locals()


@support.scrape
def episodios(item):
    patronBlock = r'<h6>Episodio</h6>(?P<block>.*?)(?:<!--|</table>)'
    patron = r'<strong>(?P<title>[^<]+)</strong>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>[^>]+><a href="http://link\.animetubeita\.com/2361078/(?P<url>[^"]+)"'
    action = 'findvideos'
    return locals()


def findvideos(item):
    itemlist=[]
    if item.args == 'last':
        match = support.match(item, r'href="(?P<url>[^"]+)"[^>]+><strong>DOWNLOAD &amp; STREAMING</strong>', url=item.url)[0]
        if match:
            patronBlock = r'<h6>Episodio</h6>(?P<block>.*?)(?:<!--|</table>)'
            patron = r'<a href="http://link\.animetubeita\.com/2361078/(?P<url>[^"]+)"'
            match = support.match(item, patron, patronBlock, headers, match[0])[0]
        else: return itemlist

        if match: item.url = match[-1]
        else: return itemlist
    data = support.httptools.downloadpage(item.url, headers=headers).data
    cookies = ""
    matches = re.compile('(.animetubeita.com.*?)\n', re.DOTALL).findall(support.config.get_cookie_data())
    for cookie in matches:
        name = cookie.split('\t')[5]
        value = cookie.split('\t')[6]
        cookies += name + "=" + value + ";"

    headers['Referer'] =  item.url
    headers['Cookie'] = cookies[:-1]

    url = support.scrapertoolsV2.find_single_match(data, """<source src="([^"]+)" type='video/mp4'>""")
    if not url: url = support.scrapertoolsV2.find_single_match(data, 'file: "([^"]+)"')
    if url:
        url += '|' + urllib.urlencode(headers)
        itemlist.append(
            support.Item(channel=item.channel,
                        action="play",
                        title='diretto',
                        server='directo',
                        quality='',
                        url=url,
                        thumbnail=item.thumbnail,
                        fulltitle=item.fulltitle,
                        show=item.show,
                        contentType=item.contentType,
                        folder=False))
    return support.server(item, itemlist=itemlist)