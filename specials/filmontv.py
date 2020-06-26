# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale film in tv
# ------------------------------------------------------------
from datetime import datetime
import glob, time, gzip, xbmc
from core import filetools, downloadtools, support, scrapertools
from core.item import Item
from platformcode import logger

host = "http://www.epgitalia.tv/xml/guide.gzip"
lCanali = ['Rai 1', 'Rai 2', 'Rai 3', 'Rete 4', 'Canale 5', 'Italia 1', 'Italia 2', 'Mediaset Extra', 'TeleTicino',
           'la5@it', 'La7D', 'Sky TG24 HD', 'TG Norba24', 'Rai Premium', 'Rai News DTT', 'Rai Movie', 'Rai 4 DTT',
           'Iris', 'GIALLO DTT', 'Alice', 'RAI Sport', 'Automoto TV', 'Sky Cinema Uno HD', 'Sky Cinema Uno +24 HD',
           'Sky Cinema Collection HD', 'Sky Cinema Family HD', 'Sky Cinema Romance HD', 'Sky Cinema Comedy HD',
           'Sky Cinema Action HD', 'Sky Cinema Due HD', 'Sky Cinema Due +24 HD', 'Sky Cinema Drama HD',
           'Sky Cinema Suspense HD', 'Comedy Central', 'Laeffe', 'Sky Uno HD', 'Classica HD', 'Sky Atlantic', 'Fox HD',
           'Fox Life HD', 'Fox Crime HD', 'Blaze', 'Paramount Channel Italia', 'Lei', 'Dove', 'CI Crime+ Investigation',
           'Sky Sport F1 HD', 'Sky Sport MotoGP', 'RaiSportpiuHD', 'Class Horse TV', 'SuperTennis HD', 'Eurosport HD',
           'Eurosport 2HD', 'Sky Sport 24', 'Sky Sport Uno', 'Sky Sport Football HD', 'Sky Sport Arena',
           'Sky Sport Serie A', 'Sky Sport NBA', 'Sky Sport Collection HD', 'Inter Channel', 'Lazio Style Channel',
           'Milan TV', 'Roma TV', 'Torino Channel', 'Sky Arte HD-400', 'Discovery Science HD', 'National Geo HD',
           'Nat Geo Wild HD', 'History Channel', 'FOCUS', 'DMAX HD', 'Caccia e Pesca', 'Gambero Rosso HD', 'Cielo DTT',
           'Cartoon Network', 'Baby TV', 'Nickelodeon', 'DeAKids', 'Super! DTT', 'MAN-GA', 'MTV', 'Telelombardia',
           'Spike tv', 'TV8', 'NOVE', 'Premium Cinema HD', 'Premium Cinema Energy', 'Premium Cinema Emotion',
           'Premium Cinema Comedy', 'Premium Cinema +24 HD', 'Premium Stories', 'Premium Crime DTT', 'Premium Action',
           'Top Crime', 'Sportitalia', 'MySports One F', 'MySports 2/Sky 2 F', 'MySports 3/Sky 3 F',
           'MySports 4/Sky 4 F', 'MySports 5/Sky 5 F', 'MySports 6/Sky 6 F', 'MySports 7/Sky 7 F', 'MySports 8/Sky 8 F',
           'MySports 9/Sky 9 F', 'Rai Italia', 'Radionorba TV', 'SMtv San Marino', 'Radio 1', 'Italia 7 Gold',
           'Mediaset', 'HSE 24']


def mainlist(item):
    support.log()

    itemlist = [Item(title=support.typo('Film in onda oggi', 'bold'), channel=item.channel, action='category', contentType='movie'),
                Item(title=support.typo('Serie Tv in onda oggi', 'bold'), channel=item.channel, action='peliculas', contentType='tvshow'),
                Item(title=support.typo('Guida tv per canale', 'bold'), channel=item.channel, action='listaCanali'),
                Item(title=support.typo('Canali live (Rai Play)', 'bold'), channel=item.channel, action='live')]

    return itemlist


def getEpg():
    now = datetime.now()
    fileName = support.config.get_temp_file('guidatv-') + now.strftime('%Y %m %d')
    archiveName = fileName + '.gz'
    xmlName = fileName + '.xml'
    if not filetools.exists(archiveName):
        support.log('downloading epg')
        # cancello quelli vecchi
        for f in glob.glob(support.config.get_temp_file('guidatv-') + '*'):
            filetools.remove(f, silent=True)
        # inmemory = io.BytesIO(httptools.downloadpage(host).data)
        downloadtools.downloadfile(host, archiveName)
        support.log('opening gzip and writing xml')
        fStream = gzip.GzipFile(archiveName, mode='rb')
        guide = fStream.read()
        with open(xmlName, 'w') as f:
            f.write(guide)
    else:
        guide = open(xmlName).read()
    return guide


def category(item):
    itemlist = [Item(title="Tutti", all=True, channel=item.channel, action='peliculas', contentType=item.contentType)]
    category = ['Famiglia', 'Documentario', 'Thriller', 'Azione', 'Crime', 'Drammatico', 'Western', 'Avventura', 'Commedia', 'Fantascienza', 'Fantastico', 'Animazione', 'Horror', 'Mistero', 'Sport', 'Mondo e Tendenze', 'Intrattenimento', 'Musicale', 'Guerra', 'Storico', 'Biografico', 'Poliziesco']

    for cat in category:
        itemlist.append(Item(title=cat, category=cat, channel=item.channel, action='peliculas', contentType=item.contentType))
    return itemlist


def peliculas(item, f=None, ):
    f = getEpg()
    titles = [item.lastTitle] if not item.titles else item.titles
    itemlist = []
    pag = item.pag if item.pag else 0

    channel = ''
    title = ''
    episode = ''
    plot = ''
    thumbnail = ''
    actors = []
    director = ''
    year = ''
    genres = []
    country = ''
    skip = False

    for i, line in enumerate(f.splitlines()):
        if i >= pag:
            if '<programme' in line:
                channel = scrapertools.find_single_match(line, r'channel="([^"]+)"')
                if channel not in lCanali:
                    skip = True
            elif '<title' in line:
                title = scrapertools.find_single_match(line, r'>([^<]+?)(?: - 1\s*\^\s*TV)?<')
                if title in titles:
                    skip = True
            elif not skip and '<desc' in line:
                plot = scrapertools.find_single_match(line, r'>([^<]+)<')
            elif not skip and '<actor' in line:
                match = scrapertools.find_single_match(line, r'(?:role="([^"]*)")?>([^<]+)<')
                actors.append([match[1], match[0]])
            elif not skip and '<director' in line:
                director = scrapertools.find_single_match(line, r'>([^<]+)<')
            elif not skip and '<date' in line:
                year = scrapertools.find_single_match(line, r'>([^<]+)<')
            elif not skip and '<category' in line:
                genres.append(scrapertools.find_single_match(line, r'>([^<]+)<'))
            elif not skip and '<country' in line:
                country = scrapertools.find_single_match(line, r'>([^<]+)<')
            elif not skip and '<episode-num' in line:
                episode = scrapertools.find_single_match(line, r'>([^<]+)<')
                if item.contentType == 'movie':
                    skip = True
            elif not skip and '<icon' in line:
                thumbnail = scrapertools.find_single_match(line, r'src="([^"]+)"')
            elif '</programme' in line:
                if not skip and (actors or 'Film' in genres):
                    titles.append(title)
                    if (item.contentType == 'movie' and (item.category in genres or item.all==True)) or (item.contentType == 'tvshow'):
                        itemlist.append(Item(
                            channel=item.channel,
                            action='new_search',
                            title=support.typo(title + (' - ' + episode if episode else ''), 'bold'),
                            fulltitle=title,
                            search_text=title,
                            mode=item.contentType,
                            thumbnail=thumbnail if thumbnail else item.thumbnail,
                            contentType=item.contentType,
                            channel_name=channel,
                            infoLabels={
                                'title': title,
                                'plot': plot,
                                'castandrole': actors,
                                'director': director,
                                'genre': genres,
                                'country': country,
                                'year': year
                            }
                        ))

                channel = ''
                title = ''
                episode = ''
                plot = ''
                thumbnail = ''
                actors = []
                director = ''
                year = ''
                genres = []
                country = ''
                skip = False

                if len(itemlist) >= 40:
                    itemlist.append(item.clone(title=support.typo(support.config.get_localized_string(30992), 'color kod bold'), pag= i + 1, thumbnail=support.thumb(), lastTitle=titles[-1]))
                    break
    support.tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist

def listaCanali(item):
    itemlist = []
    f = getEpg()
    thumbnail = None
    skip = False

    for line in f.splitlines():
        if '<channel' in line:
            channel = scrapertools.find_single_match(line, r'id="([^"]+)"')
            if channel not in lCanali:
                skip = True
        elif not skip and '<icon' in line:
            thumbnail = scrapertools.find_single_match(line, r'src="([^"]+)"')
        elif not skip and '<programme' in line:
            break
        if '</channel' in line:
            if not skip and thumbnail: #and 'channel="' + channel + '"' in f:
                itemlist.append(Item(
                    channel=item.channel,
                    action='guidatv',
                    title=support.typo(channel, 'bold'),
                    channelName=channel,
                    thumbnail=thumbnail
                ))
                lCanali.remove(channel)
            thumbnail = None
            skip = False
        if not lCanali:
            break
    # return itemlist
    # logger.info([i.title for i in itemlist])
    return sorted(itemlist, key=lambda x: x.title)


def guidatv(item):
    itemlist = []
    f = getEpg()
    days = []
    for day in range(11, 18):days.append(xbmc.getLocalizedString(day))

    channel = ''
    title = ''
    episode = ''
    plot = ''
    thumbnail = ''
    actors = []
    director = ''
    year = ''
    genres = []
    country = ''
    start = ''
    stop = ''

    for line in f.splitlines():
        if '<programme' in line:
            start, stop, channel = scrapertools.find_single_match(line,r'start="([^"]*)" stop="([^"]*)" channel="([^"]+)"')
        elif '<title' in line:
            title = scrapertools.find_single_match(line, r'>([^<]+?)<')
        elif '<desc' in line:
            plot = scrapertools.find_single_match(line, r'>([^<]+)<')
        elif '<actor' in line:
            match = scrapertools.find_single_match(line, r'(?:role="([^"]*)")?>([^<]+)<')
            actors.append([match[1], match[0]])
        elif '<director' in line:
            director = scrapertools.find_single_match(line, r'>([^<]+)<')
        elif '<date' in line:
            year = scrapertools.find_single_match(line, r'>([^<]+)<')
        elif '<category' in line:
            genres.append(scrapertools.find_single_match(line, r'>([^<]+)<'))
        elif '<country' in line:
            country = scrapertools.find_single_match(line, r'>([^<]+)<')
        elif '<episode-num' in line:
            episode = scrapertools.find_single_match(line, r'>([^<]+)<')
        elif '<icon' in line:
            thumbnail = scrapertools.find_single_match(line, r'src="([^"]+)"')
        elif '</programme' in line:
            if item.channelName in channel:
                start = time.strptime(str(int(start.split(' ')[0]) + int(start.split('+')[1])), '%Y%m%d%H%M%S')
                stop = time.strptime(str(int(stop.split(' ')[0]) + int(stop.split('+')[1])), '%Y%m%d%H%M%S')
                duration = days[start.tm_wday] + ' alle ' + str(start.tm_hour).zfill(2) + ':' + str(start.tm_min).zfill(2) + ' - ' + str(stop.tm_hour).zfill(2) + ':' + str(stop.tm_min).zfill(2) + ' - '
                itemlist.append(Item(
                    channel=item.channel,
                    action='new_search',
                    title=duration + support.typo(title + (' - ' + episode if episode else ''), 'bold'),
                    fulltitle=title,
                    search_text=title,
                    mode=item.contentType,
                    thumbnail=thumbnail if thumbnail else item.thumbnail,
                    contentType=item.contentType,
                    channel_name=channel,
                    infoLabels={
                        'title': title,
                        'plot': plot,
                        'castandrole': actors,
                        'director': director,
                        'genre': genres,
                        'country': country,
                        'year': year
                    }
                ))

            channel = ''
            title = ''
            episode = ''
            plot = ''
            thumbnail = ''
            actors = []
            director = ''
            year = ''
            genres = []
            country = ''
            start = ''
            stop = ''
    return itemlist


def new_search(item):
    from specials import search
    item.channel = 'search'
    # se risultato certo, vai dritto alla ricerca per id
    if item.infoLabels['tmdb_id']:
        return search.channel_search(item)
    else:
        return search.new_search(item)


def live(item):
    from channels import raiplay
    return raiplay.dirette(raiplay.mainlist(Item())[0])
