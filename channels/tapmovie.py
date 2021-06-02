# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per 'dvdita'

from core import support, httptools
from core.item import Item
import sys
if sys.version_info[0] >= 3: from concurrent import futures
else: from concurrent_py2 import futures

host = support.config.get_channel_url()
api_url = '/api/v2/'
per_page = 24


@support.menu
def mainlist(item):
    film = ['/browse/movie']
    tvshow = ['/browse/tvshow']
    search = ''

    # [Voce Menu,['url','action','args',contentType]
    top = [('Generi', ['', 'genres', '', 'undefined'])]

    return locals()


def peliculas(item):
    itemlist = []
    movie = item.contentType == 'movie'
    key = 'latest_updated' if movie else 'latest_tvshows'
    action = 'findvideos' if movie else 'episodios'
    json = httptools.downloadpage(host + api_url + 'home', post={}).json[key]
    for i in json:
        itemlist.append(item.clone(id=i.get('id'), title=i.get('title'), contentTitle=i.get('title'), contentSerieName='' if movie else i.get('title'),
                                   contentPlot=i.get('description'), thumbnail=i.get('poster'),
                                    fanart=i.get('backdrop'), year=i.get('year'), action=action,
                                   url='{}/{}/{}-{}'.format('https://filmigratis.org', item.contentType, i.get('id'), support.scrapertools.slugify(i.get('title')))))
    support.tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def episodios(item):
    support.info(item)
    itemlist = []

    with futures.ThreadPoolExecutor() as executor:
        thL = []
        for season in httptools.downloadpage(host + api_url + 'tvshow', post={'tvshow_id': item.id}).json.get('season', []):
            season_id = season['season_number']
            thL.append(executor.submit(httptools.downloadpage, host + api_url + 'episodes', post={'tvshow_id': item.id, 'season_id': season_id}))
        for th in futures.as_completed(thL):
            for episode in th.result().json.get('episodes', []):
                itemlist.append(item.clone(action="findvideos", contentSeason=episode['season_id'], contentEpisodeNumber=episode['episode_number'], id=item.id,
                                           title=episode['season_id']+'x'+episode['episode_number'], contentType='episode'))
    support.scraper.sort_episode_list(itemlist)
    support.videolibrary(itemlist, item)
    support.download(itemlist, item)

    return itemlist


def genres(item):
    itemlist = []
    for n, genre in enumerate(httptools.downloadpage(host + api_url + 'categories', post={}).json.get('categories', [])):
        itemlist.append(item.clone(action="search_", genre=genre.get('name'), title=genre.get('value'), n=n))
    return support.thumb(itemlist, genre=True)


def search_(item, text=''):
    support.info('search', item)
    itemlist = []
    if item.genre:
        text = item.genre
        cmd = 'search/category'
    else:
        cmd = 'search'

    try:
        page = int(item.url.split('?p=')[1])
    except:
        page = 1
    results = httptools.downloadpage(host + api_url + cmd, post={'search': text, 'page': page}).json.get('results', [])
    for result in results:
        contentType = 'movie' if result['type'] == 'FILM' else 'tvshow'
        itemlist.append(item.clone(id=result.get('id'), title=result.get('title'), contentTitle=result.get('title'),
                                   contentSerieName='' if contentType == 'movie' else result.get('title'),
                                   contentPlot=result.get('description'), thumbnail=result.get('poster'),
                                   fanart=result.get('backdrop'), year=result.get('year'), action='episodios' if contentType == 'tvshow' else 'findvideos',
                                   url='{}/{}/{}-{}'.format('https://filmigratis.org', contentType, result.get('id'), support.scrapertools.slugify(result.get('title'))),
                                   contentType=contentType))
    support.tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    if len(results) >= per_page:
        page += 1
        support.nextPage(itemlist, item, next_page='https://filmigratis.org/category/' + str(item.n) + '/' + item.genre + '?p=' + str(page))
    return itemlist


def search(item, text):
    return search_(item, text)


def findvideos(item):
    itemlist = []
    if not item.contentSeason:  # film
        json = httptools.downloadpage(host + api_url + 'movie', post={'movie_id': item.id}).json
    else:
        json = httptools.downloadpage(host + api_url + 'episode/links', post={'tvshow_id': item.id, 'season_id': item.contentSeason, 'episode_id': item.contentEpisodeNumber}).json

    for i in json.get('links', []) + json.get('special', []):
        itemlist.append(Item(url=i.get('link')))
    return support.server(item, itemlist=itemlist)
