# -*- coding: utf-8 -*-
from core import support, httptools, scrapertoolsV2
from core.item import Item
from platformcode import config, logger

__channel__ = "streamtime"
host = config.get_channel_url(__channel__)
headers = [['Referer', 'org.telegram.messenger']]
list_servers = ['directo']
list_quality = ['default']

downPrefix = 'https://stsh.ml/Down-'

@support.menu
def mainlist(item):
    film = ['?q=%23Film']
    tvshow = ['?q=%23SerieTv']
    return locals()


@support.scrape
def peliculas(item):
    patron = """tgme_widget_message_photo_wrap blured.*?image:url\("(?P<thumbnail>[^"]+).*?(?:🎥|🎬)(?P<title>.*?)(?:🎥|🎬).*?(?:Audio(?:</b>)?: (?P<lang>.*?<br>))?.*?Anno(?:</b>)?: (?P<year>[0-9]{4}).*?(?:<b>Stream</b>|Risoluzione|<b>Tipo</b>): (?P<quality>[^<]+).*?tgme_widget_message_inline_button url_button" href="(?P<url>[^"]+)"""
    def itemlistHook(itemlist):
        retItemlist = []
        # filtro per tipo
        for i in itemlist:
            if item.contentType == 'movie':
                if '/Film/' in i.url or 'Stream-' in i.url:
                    retItemlist.append(i)
            else:
                if '/SerieTv/' in i.url:
                    retItemlist.append(i)
        # rimuovo duplicati
        if item.contentType != 'movie':
            nonDupl = []
            # support.dbg()
            for i in retItemlist:
                for nd in nonDupl:
                    if i.title == nd.title:
                        break
                else:
                    daAgg = i
                    spl1 = i.url.split('-')
                    stagione1 = spl1[-2]
                    nEp1 = int(spl1[-1])

                    for i2 in retItemlist[1:]:
                        if i.title == i2.title:
                            spl2 = i2.url.split('-')
                            stagione2 = spl2[-2]
                            nEp2 = int(spl2[-1])
                            if stagione1 == stagione2 and nEp2 > nEp1:
                                daAgg = i2
                    nonDupl.append(daAgg)
            retItemlist = nonDupl
        return retItemlist[::-1]
    # debug = True
    patronNext = 'tgme_widget_message_photo_wrap blured" href="([^"]+)'
    def fullItemlistHook(itemlist):
        msgId = int(itemlist[-1].url.split('/')[-1])
        itemlist[-1].url = host + '?before=' + str(msgId) + '&after=' + str(msgId-20)
        return itemlist

    if item.contentType == 'tvshow':
        action = 'episodios'
    return locals()


def search(item, texto):
    item.url = host + "/?q=" + texto
    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
    return []


def episodios(item):
    domain, id, season, episode = scrapertoolsV2.find_single_match(item.url, r'(https?://[a-z0-9.-]+).*?/([^-/]+)-S([0-9]+)-([0-9]+)$')
    itemlist = []
    for n in range(1, int(episode)):
        url = domain + '/play_s.php?s=' + id + '-S' + season + '&e=' + str(n)
        itemlist.append(
            Item(channel=item.channel,
                 action="findvideos",
                 title=str(int(season)) + 'x' + str(n) + support.typo(item.quality, '-- [] color kod'),
                 url=url,
                 fulltitle=item.fulltitle,
                 thumbnail=item.thumbnail,
                 show=item.show,
                 quality=item.quality,
                 contentType=item.contentType,
                 folder=False,
                 args={'id': id, 'season': season, 'episode': episode}))

    support.videolibrary(itemlist, item)
    return itemlist


def findvideos(item):
    domain = scrapertoolsV2.find_single_match(item.url, 'https?://[a-z0-9.-]+')
    if item.contentType == 'movie':
        id = item.url.split('/')[-1]
        url = domain + '/play_f.php?f=' + id
    else:
        url = item.url
        id = item.args['id']
        season = item.args['season']
        episode = item.args['episode']
    res = support.match(item, 'src="([^"]+)">.*?</video>', url=url, headers=[['Referer', domain]])
    itemlist = []
    support.dbg()

    if res[0]:
        itemlist.append(
            Item(channel=item.channel,
                 action="play",
                 title='stpgs.ml' + support.typo(item.quality, '-- [] color kod'),
                 url=res[0][0],
                 server='directo',
                 fulltitle=item.fulltitle,
                 thumbnail=item.thumbnail,
                 show=item.show,
                 quality=item.quality,
                 contentType=item.contentType,
                 folder=False))
        download = itemlist[0].clone()
        if item.contentType == 'movie':
            download.url = downPrefix + id
        else:
            download.url = downPrefix + id + 'S' + season + '-' + episode
        itemlist.append(download)
    else:
        # google drive...
        pass
    support.videolibrary(itemlist, item)
    return support.controls(itemlist, item, True, True)
