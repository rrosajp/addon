# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale film in tv
# ------------------------------------------------------------
from datetime import datetime, timedelta
import glob, time, gzip, xbmc
from core import filetools, downloadtools, support, scrapertools
from core.item import Item

host = "http://www.epgitalia.tv/xml/guide2.gzip"


def mainlist(item):
    support.log()

    itemlist = [Item(title=support.typo('Film in onda oggi','bold'), channel=item.channel, action='peliculas', contentType='movie'),
                Item(title=support.typo('Serie Tv in onda oggi','bold'), channel=item.channel, action='peliculas', contentType='tvshow'),
                Item(title=support.typo('Guida tv per canale','bold'), channel=item.channel, action='listaCanali'),
                Item(title=support.typo('Canali live (Rai Play)','bold'), channel=item.channel, action='live')]

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

    guide = open(xmlName).read()
    return guide

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

    for i, line in enumerate(f.splitlines()):
        if i >= pag:
            if '<programme' in line:
                channel = scrapertools.find_single_match(line, r'channel="([^"]+)"')
            elif '<title' in line:
                title = scrapertools.find_single_match(line, r'>([^<]+)<')
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
            elif '</programme' in line and title not in titles and (actors or 'Film' in genres):
                titles.append(title)
                if (item.contentType == 'movie' and not episode) or (item.contentType == 'tvshow' and episode):
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

                if len(itemlist) >= 40:
                    itemlist.append(item.clone(title=support.typo(support.config.get_localized_string(30992), 'color kod bold'), pag= i + 1, thumbnail=support.thumb(), lastTitle=titles[-1]))
                    break
    support.tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist

def listaCanali(item):
    itemlist = []
    f = getEpg()

    for line in f.splitlines():
        if '<channel' in line:
            channel = scrapertools.find_single_match(line, r'id="([^"]+)"')
        elif '<icon' in line:
            thumbnail = scrapertools.find_single_match(line, r'src="([^"]+)"')
        elif '<programme' in line:
            break
        if '</channel' in line and thumbnail:
            itemlist.append(Item(
                channel=item.channel,
                action='guidatv',
                title=support.typo(channel, 'bold'),
                channelName=channel,
                thumbnail=thumbnail
            ))
    # return itemlist
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
            title = scrapertools.find_single_match(line, r'>([^<]+)<')
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
    return search.new_search(item)


def live(item):
    from channels import raiplay
    return raiplay.dirette(raiplay.mainlist(Item())[0])
