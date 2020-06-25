# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale film in tv
# ------------------------------------------------------------
import datetime
import glob
import time
# import xml.etree.ElementTree as ET
from core import filetools, downloadtools, jsontools, scrapertools
from core.item import Item
from platformcode import logger, config
import gzip

host = "http://www.epgitalia.tv/xml/guide.gzip"
now = datetime.datetime.now()
fileName = config.get_temp_file('guidatv-') + now.strftime('%Y %m %d')
archiveName = fileName + '.gz'
# xmlName = fileName + '.xml'
jsonName = fileName + '.json'


def mainlist(item):
    logger.info(" mainlist")
    itemlist = []

    itemlist.append(Item(title='Film in onda oggi', channel=item.channel, action='peliculas', contentType='movie'))
    itemlist.append(Item(title='Serie Tv in onda oggi', channel=item.channel, action='peliculas', contentType='tvshow'))
    # itemlist.append(Item(title='Guida tv per canale', channel=item.channel, action='listaCanali'))
    itemlist.append(Item(title='Canali live (Rai Play)', channel=item.channel, action='live'))

    return itemlist


def getEpg():
    if not filetools.exists(archiveName):
        logger.info('downloading epg')
        # cancello quelli vecchi
        for f in glob.glob(config.get_temp_file('guidatv-') + '*'):
            filetools.remove(f, silent=True)
        # inmemory = io.BytesIO(httptools.downloadpage(host).data)
        downloadtools.downloadfile(host, archiveName)
    if filetools.exists(archiveName) and not filetools.exists(jsonName):
        logger.info('opening gzip and writing Json')
        fStream = gzip.GzipFile(archiveName, mode='rb')
        guide = fStream.read()
        write_json(guide)

    with open(jsonName) as f:
        json = jsontools.load(f.read())
    return json


def peliculas(item):
    itemlist = []
    start = time.time()
    json_file = getEpg()
    logger.info('PARSE TIME: ' + str(time.time() - start))
    start = time.time()
    if item.contentType == 'movie':
        json = json_file['movies']
    else:
        json = json_file['tvshows']
    for title, value in json.items():
         if 'infoLabels' in value:
            infoLabels = value['infoLabels']
            itemlist.append(Item(
                    channel=item.channel,
                    search_text=title,
                    title=title + (' - ' + value['episode'] if 'episode' in value else ''),
                    plot=value['plot'],
                    thumbnail=value['thumbnail'],
                    contentType=item.contentType,
                    infoLabels=infoLabels
                ))
    logger.info('BUILD ITEMLIST: ' + str(time.time() - start))
    # tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def listaCanali(item):
    itemlist = []
    xml = getEpg()

    for ch in xml.iter('channel'):
        name = ch.attrib['id']
        try:
            icon = ch.find('icon').attrib['src']

            itemlist.append(Item(
                channel=item.channel,
                action='guidatv',
                title=name,
                thumbnail=icon
            ))
        except:
            pass

    return sorted(itemlist, key=lambda x: x.title)


def guidatv(item):
    itemlist = []
    xml = getEpg()
    import calendar
    weekday = dict(enumerate(calendar.day_name))

    for prog in xml.findall("programme[@channel='" + item.title + "']"):
        start = time.strptime(prog.attrib['start'].split(' ')[0], '%Y%m%d%H%M%S')
        stop = time.strptime(prog.attrib['stop'].split(' ')[0], '%Y%m%d%H%M%S')
        title = prog.find('title')
        if title is not None:
            title = title.text
            episode = prog.find('episode-num')
            if episode is not None:
                episode = ' (' + episode.text + ')'
            else:
                episode = ''
            desc = prog.find('desc')
            if desc is not None:
                desc = desc.text
            actors = prog.find('credits')
            if actors is not None:
                actors = [(actor.text, actor.attrib['role'] if 'role' in actor.attrib else '') for actor in actors]
            date = prog.find('date')
            if date is not None:
                date = date.text
            genres = prog.find('category')
            if genres is not None:
                genres = ','.join([cat.text for cat in genres])
            thumbnail = prog.find('icon')
            if thumbnail is not None:
                thumbnail = thumbnail.attrib['src']
            country = prog.find('country')
            if country is not None:
                country = country.text

            if episode:
                content = 'tvshow'
            elif actors:
                content = 'movie'
            else:
                content = ''
            itemlist.append(Item(
                channel=item.channel,
                action='new_search',
                search_text=title,
                mode='all',
                title=title + episode + '\n' + weekday[start.tm_wday] + ' alle ' + str(start.tm_hour).zfill(2) + ':' + str(start.tm_min).zfill(
                    2) + ' - ' + str(
                    stop.tm_hour).zfill(2) + ':' + str(stop.tm_min).zfill(2),
                year=date if date else '-',
                thumbnail=thumbnail if thumbnail else '',
                contentType=content,
                infoLabels={
                    'title': title,
                    'plot': desc if desc else '',
                    'castandrole': tuple(actors) if actors else '',
                    'genre': genres if genres else '',
                    'country': country if country else ''
                }
            ))

    return itemlist


def new_search(item):
    from specials import search
    return search.new_search(item)


def live(item):
    from channels import raiplay
    return raiplay.dirette(raiplay.mainlist(Item())[0])

def write_json(f):

    titles = []
    channel_dict = {}
    channel_dict['movies'] = {}
    channel_dict['tvshows'] = {}

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
        if '<programme' in line: start, stop, channel = scrapertools.find_single_match(line, r'start="(\d+)[^"]*" stop="(\d+)[^"]*" channel="([^"]+)"')
        elif '<title' in line: title = scrapertools.find_single_match(line, r'>([^<]+)<')
        elif '<desc' in line: plot = scrapertools.find_single_match(line, r'>([^<]+)<')
        elif '<actor' in line:
            match = scrapertools.find_single_match(line, r'(?:role="([^"]*)")?>([^<]+)<')
            actors.append([match[1], match[0]])
        elif '<director' in line: director = scrapertools.find_single_match(line, r'>([^<]+)<')
        elif '<date' in line: year = scrapertools.find_single_match(line, r'>([^<]+)<')
        elif '<category' in line: genres.append(scrapertools.find_single_match(line, r'>([^<]+)<'))
        elif '<country' in line: country = scrapertools.find_single_match(line, r'>([^<]+)<')
        elif '<episode-num' in line: episode = scrapertools.find_single_match(line, r'>([^<]+)<')
        elif '<icon' in line: thumbnail = scrapertools.find_single_match(line, r'src="([^"]+)"')
        elif '</programme' in line and title and title not in titles and actors:
            titles.append(title)
            if episode:
                t = channel_dict['tvshows']
            else:
                t = channel_dict['movies']
            t[title] = {}
            t[title]['infoLabels'] = {'castandrole':actors, 'director':director, 'genres':genres, 'country':country, 'year':year}
            t['start'] = start
            t['stop'] = stop
            t['episode'] = episode
            t[title]['title'] = title
            t[title]['channel_name'] = channel
            t[title]['thumbnail'] = thumbnail
            t[title]['plot'] = plot

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

    # f = json.dumps(channel_dict)
    with open(jsonName, 'w') as json_file:
        json_file.write(jsontools.dump(channel_dict, sort_keys=False))
        json_file.close()