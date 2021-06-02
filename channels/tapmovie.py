# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per 'dvdita'

from core import support, httptools
from core.item import Item

host = support.config.get_channel_url()
api_url = '/api/v2/'


@support.menu
def mainlist(item):
    film = ['/browse/movie']
    tvshow = ['/browse/tvshow']
    search = ''

    # [Voce Menu,['url','action','args',contentType]
    # top = [('Generi', ['', 'genres', '', 'undefined'])]

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
                                   url='{}/{}/{}-{}'.format(host, item.contentType, i.get('id'), support.scrapertools.slugify(i.get('title')))))
    support.tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def episodios(item):
    support.info(item)
    itemlist = []

    for season in httptools.downloadpage(host + api_url + 'tvshow', post={'tvshow_id': item.id}).json.get('season', []):
        season_id = season['season_number']
        for episode in httptools.downloadpage(host + api_url + 'episodes', post={'tvshow_id': item.id, 'season_id': season_id}).json.get('episodes', []):
            itemlist.append(item.clone(action="findvideos", contentSeason=season_id, contentEpisodeNumber=episode['episode_number'], id=item.id,
                                       title=str(season_id)+'x'+episode['episode_number'], contentType='episode'))
    support.videolibrary(itemlist, item)
    support.download(itemlist, item)

    return itemlist


def search(item, text):
    support.info('search', item)
    itemlist = []
    for result in httptools.downloadpage(host + api_url + 'search', post={'search': text}).json.get('results', []):
        contentType = 'movie' if result['type'] == 'FILM' else 'tvshow'
        itemlist.append(item.clone(id=result.get('id'), title=result.get('title'), contentTitle=result.get('title'),
                                   contentSerieName='' if contentType == 'movie' else result.get('title'),
                                   contentPlot=result.get('description'), thumbnail=result.get('poster'),
                                   fanart=result.get('backdrop'), year=result.get('year'), action='episodios' if contentType == 'tvshow' else 'findvideos',
                                   url='{}/{}/{}-{}'.format(host, contentType, result.get('id'), support.scrapertools.slugify(result.get('title'))),
                                   contentType=contentType))
    support.tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist


def findvideos(item):
    itemlist = []
    if not item.contentSeason:  # film
        json = httptools.downloadpage(host + api_url + 'movie', post={'movie_id': item.id}).json
    else:
        json = httptools.downloadpage(host + api_url + 'episode/links', post={'tvshow_id': item.id, 'season_id': item.contentSeason, 'episode_id': item.contentEpisodeNumber}).json

    for i in json.get('links', []) + json.get('special', []):
        itemlist.append(Item(url=i.get('link')))
    return support.server(item, itemlist=itemlist)
