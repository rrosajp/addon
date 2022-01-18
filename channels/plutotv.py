# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Pluto TV
# ------------------------------------------------------------

import uuid, datetime, requests
from platformcode import logger, config
from core.item import Item
from core import support, httptools


host = support.config.get_channel_url()
api = 'https://api.pluto.tv'
UUID = 'sid={}&deviceId={}'.format(uuid.uuid1().hex, uuid.uuid4().hex)

now = datetime.datetime.now()
start = (now.strftime('%Y-%m-%dT%H:00:00Z'))
stop  = (now + datetime.timedelta(hours=2)).strftime('%Y-%m-%dT%H:00:00Z')


live_url = '{}/v2/channels.json?{}'.format(api, UUID)
guide_url = '{}/v2/channels?start={}&stop={}&{}'.format(api, start, stop, UUID)
vod_url = '{}/v3/vod/categories?includeItems=true&deviceType=web&'.format(api, UUID)


@support.menu
def mainlist(item):
    top =  [('Dirette {bold}', ['/it/live-tv/', 'live'])]

    menu = sorted([(it['name'], ['/it/on-demand', 'peliculas', it['items']]) for it in httptools.downloadpage(vod_url).json['categories'][1:]])

    search = ''

    return locals()

def live(item):
    logger.debug()
    def calcTime(t):
        return datetime.datetime.strftime(datetime.datetime.strptime(t, '%Y-%m-%dT%H:%M:%S.%fZ'), '%H:%M')

    guide = {}
    for g in  httptools.downloadpage(guide_url).json:
        guide[g['number']] = [g['timelines'][0]['title'],
                              '{}/{}'.format(calcTime(g['timelines'][0]['start']), calcTime(g['timelines'][0]['stop'])),
                              g['timelines'][1]['title']]

    itemlist = []
    for it in httptools.downloadpage(live_url).json:
        itemlist.append(item.clone(title= '[B]{}[/B] | {} | {}'.format(it['name'], guide[it['number']][0], guide[it['number']][1]),
                                   number=it['number'],
                                   contentTitle=it['name'],
                                   action='findvideos',
                                   thumbnail=it['solidLogoPNG']['path'],
                                   fanart=it['featuredImage']['path'],
                                   plot='{}\n\n[B]A seguire:[/B]\n{}'.format(it['summary'], guide[it['number']][2]),
                                   url= it['stitched']['urls'][0]['url'],
                                   forcethumb=True))
    itemlist.sort(key=lambda it: it.number)
    return itemlist

def search(item, text):
    logger.debug('Search', text)
    try:
        item.search = text.lower()
        item.args = []
        for it in httptools.downloadpage(vod_url).json['categories'][1:]:
            item.args.extend(it['items'])
        return peliculas(item)

    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("%s" % line)
            return []


def peliculas(item):
    logger.debug()
    itemlist = []
    recordlist = []
    for i, it in enumerate(item.args):
        if item.search in it['name'].lower():
            itm = Item(channel=item.channel,
                       title=it['name'],
                       contentTitle=it['name'],
                       contentSerieName= it['name'] if it['type'] == 'series' else '',
                       plot=it['description'],
                       contentType='tvshow' if it['type'] == 'series' else 'movie',
                       action='episodios' if it['type'] == 'series' else 'findvideos',
                       thumbnail= it['covers'][0]['url'],
                       fanart= it['covers'][2]['url'] if len(it['covers']) > 2 else '',
                       id= it['_id'],
                       url= it['stitched']['urls'][0]['url'])

            if i < 20 or item.search:
                itemlist.append(itm)
            else:
                recordlist.append(it)

    support.tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    if recordlist and not item.search:
        itemlist.append(item.clone(title=support.typo(support.config.get_localized_string(30992), 'color kod bold'), thumbnail=support.thumb(), args=recordlist))
    return itemlist


def episodios(item):
    logger.debug()
    itemlist = []
    seasons = httptools.downloadpage('{}/v3/vod/series/{}/seasons?includeItems=true&deviceType=web&{}'.format(api, item.id, UUID)).json['seasons']
    for season in seasons:
        for episode in season['episodes']:
            itemlist.append(item.clone(title='{}x{:02d} - {}'.format(episode['season'], episode['number'], episode['name']),
                                       contrentTitle=episode['name'],
                                       contentSeason=episode['season'],
                                       contentEpisodeNumber=episode['number'],
                                       plot=episode['description'],
                                       thumbnail=episode['covers'][1]['url'],
                                       url=episode['stitched']['urls'][0]['url'],
                                       action='findvideos'))

    if config.get_setting('episode_info'):
        support.tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    support.videolibrary(itemlist,item)
    return itemlist


def findvideos(item):
    logger.debug()
    item.server = 'directo'
    item.manifest='hls'
    item.url = item.url.replace('deviceType=&','deviceType=web&')
    item.url = item.url.replace('deviceMake=&','deviceMake=firefox&')
    item.url = item.url.replace('deviceModel=&','deviceModel=firefox&')
    item.url = item.url.replace('appName=&','appName=web&')
    item.url = item.url.replace('sid=&','')
    item.url = '{}&sid={}'.format(item.url, uuid.uuid1().hex)
    return support.server(item, itemlist=[item],  Download=False, Videolibrary=False)
