# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per animeuniverse
# ----------------------------------------------------------

from core import support

host = support.config.get_channel_url()
headers = {}

perpage_list = ['20','30','40','50','60','70','80','90','100']
perpage = perpage_list[support.config.get_setting('perpage' , 'animeuniverse')]


@support.menu
def mainlist(item):
    anime=['/anime/',
           ('Tipo',['', 'menu', 'Anime']),
           ('Anno',['', 'menu', 'Anno']),
           ('Genere', ['', 'menu','Genere']),
           ('Hentai', ['/hentai/', 'peliculas'])]
    return locals()


@support.scrape
def menu(item):
    action = 'peliculas'
    data = support.match(item, patron= item.args + r'</a><ul class="sub-menu">(.*?)</ul>').match
    patronMenu = r'<a href="(?P<url>[^"]+)">(?P<title>[^<]+)<'
    return locals()


def search(item, texto):
    support.log(texto)
    item.search = texto
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
    if '/mos/' in item.url:
        item.contentType = 'movie'
        action='findvideos'
    else:
        item.contentType = 'tvshow'
        action='episodios'
    if item.search:
        query = 's'
        searchtext = item.search
    else:
        query='category_name'
        searchtext = item.url.split('/')[-2]
    if not item.pag: item.pag = 1

    anime=True
    data = support.match(host + '/wp-content/themes/animeuniverse/functions/ajax.php', post='sorter=recent&location=&loop=main+loop&action=sort&numarticles='+perpage+'&paginated='+str(item.pag)+'&currentquery%5B'+query+'%5D='+searchtext+'&thumbnail=1').data.replace('\\','')
    patron=r'<a href="(?P<url>[^"]+)"><img width="[^"]+" height="[^"]+" src="(?P<thumb>[^"]+)" class="[^"]+" alt="" title="(?P<title>[^\["]+)\s+(?P<lang>(?:[Ss][Uu][Bb].)?[Ii][Tt][Aa])'

    def ItemItemlistHook(item, itemlist):
        if len(itemlist) == int(perpage):
            item.pag += 1
            itemlist.append(item.clone(title=support.typo(support.config.get_localized_string(30992), 'color kod bold'), action='peliculas'))
        return itemlist
    return locals()




@support.scrape
def episodios(item):
    pagination = int(perpage)
    patron = r'<td>\s*(?P<title>[A-Za-z]+ \d+)[^>]+>[^>]+>\s*<a href="(?P<url>[^"]+)"'
    return locals()


def findvideos(item):
    url = support.match(support.httptools.downloadpage(item.url).url, string=True, patron=r'file=([^$]+)').match
    if 'http' not in url: url = 'http://' + url
    itemlist=[item.clone(title='Diretto', url=url, server='directo', action='play')]
    return support.server(item, itemlist=itemlist)
