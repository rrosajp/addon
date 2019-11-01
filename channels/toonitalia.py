# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per ToonItalia
# ------------------------------------------------------------

from core import support

__channel__ = "toonitalia"
host = support.config.get_channel_url(__channel__)

headers = [['Referer', host]]

list_servers = ['wstream', 'openload', 'streamango']
list_quality = ['HD', 'default']


@support.menu
def mainlist(item):

    top = [('Novità',['', 'peliculas', 'new', 'tvshow']),
           ('Aggiornamenti', ['', 'peliculas', 'last', 'tvshow']),
           ('Popolari', ['', 'peliculas', 'most_view', 'tvshow'])]   
    tvshow = '/lista-serie-tv/'
    anime =['/lista-anime-2/',
               ('Sub-Ita',['/lista-anime-sub-ita/']),
               ('Film Animati',['/lista-film-animazione/','peliculas', '', 'movie'])]    
    search = ''

    return locals()


@support.scrape
def peliculas(item):
    pagination = ''
    anime = True
    blacklist = ['-Film Animazione disponibili in attesa di recensione ']
    
    if item.args == 'search':
        patron = r'<h2 class="entry-title"><a href="(?P<url>[^"]+)" rel="bookmark">(?P<title>[^<]+)</a>'
    elif item.args == 'last':
        patronBlock = 'Aggiornamenti</h2>(?P<block>.*)</ul>'
        patron = '<a href="(?P<url>[^"]+)">(?P<title>[^<]+)</a>'
    elif item.args == 'most_view':
        patronBlock = 'I piu visti</h2>(?P<block>.*)</ul>'
        patron = '<a href="(?P<url>[^"]+)" title="(?P<title>[^"]+)"'
    elif item.args == 'new':
        patronBlock = '<main[^>]+>(?P<block>.*)</main>'
        patron = '<a href="(?P<url>[^"]+)" rel="bookmark">(?P<title>[^<]+)</a>[^>]+>[^>]+>[^>]+><img.*?src="(?P<thumb>[^"]+)".*?<p>(?P<plot>[^<]+)</p>'
        patronNext = '<a class="next page-numbers" href="([^"]+)">'
    else:
        patronBlock = '"lcp_catlist"[^>]+>(?P<block>.*)</ul>'
        patron = r'<li ><a href="(?P<url>[^"]+)" title="[^>]+">(?P<title>[^<|\(]+)?(?:\([^\d]*(?P<year>\d+)\))?[^<]*</a>'
        
    action = 'findvideos' if item.contentType == 'movie' else 'episodios'

    return locals()

def episodios(item):
    logger.info("[toonitalia.py] episodios")
    itemlist = []

    data = httptools.downloadpage(item.url, headers=headers).data
    support.log('DATA= ', data)

    patron = r'<br />\s*<a href="([^"]+)"\s*target="_blank"\s*rel[^>]+>([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    if "https://vcrypt.net" in data:
        patron = r'(?:<p>|<br />)\s*([^<]+) &#8211; <a href="([^"]+)'
        matches = re.compile(patron, re.DOTALL).findall(data)

        for scrapedtitle, scrapedurl in matches:
            if 'Wikipedia' not in scrapedurl:
                scrapedtitle = scrapertools.decodeHtmlentities(scrapedtitle).replace("×", "x")
                scrapedtitle = scrapedtitle.replace("_", " ")
                scrapedtitle = scrapedtitle.replace(".mp4", "")
                puntata = scrapedtitle
                for i in itemlist:
                    if i.args == puntata:  # è già stata aggiunta
                        i.url += " " + scrapedurl
                        break

                else:
                    itemlist.append(
                        Item(channel=__channel__,
                             action="findvideos",
                             contentType=item.contentType,
                             title="[COLOR azure]" + scrapedtitle + "[/COLOR]",
                             thumbnail=item.thumbnail,
                             fulltitle=scrapedtitle,
                             url=scrapedurl,
                             args=puntata,
                             show=item.show,
                             plot=item.plot))
    else:
        patron = '<br /> <a href="(?P<url>[^"]+)" target="_blank" rel="noopener[^>]+>(?P<title>[^<]+)</a>'

    def itemHook(item):
        item.title = item.title.replace('_',' ').replace('–','-')
        item.title = support.re.sub(item.fulltitle + ' - ','',item.title)
        return item

    return locals()

def findvideos(item):
    return support.server(item, item.url if item.contentType != 'movie' else support.httptools.downloadpage(item.url, headers=headers).data )
