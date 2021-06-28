from platformcode import config
from core import httptools, scrapertools, support, tmdb

host = 'https://aniplay.it'

@support.menu
def mainlist(item):
    anime=['/api/anime/advanced-search',
        ('A-Z', ['/api/anime/advanced-search', 'alphabetical_strip', '']),
        ('Anno', ['', 'seasonal_by_year', '']),
        ('Top', ['', 'top_items', '']),
        ('Ultimi aggiunti', ['', 'latest_added', '']),
    ]
    return locals()

def alphabetical_strip(item):
    itemlist = []
    alphabet = ("0-9, A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X, Y, Z").split(', ')
    for letter in alphabet:
        itemlist.append(
                item.clone(title = support.typo(letter, 'bold'),
                        fulltitle= letter,
                        show= letter,
                        url= host + '/api/anime/find-by-char',
                        action= 'peliculas',
                        videolibrary= False,
                        variable= '&character=' + letter,
                        thumbnail=support.thumb('az'))
        )
    return itemlist

def seasonal_by_year(item):
    itemlist = []
    from datetime import date
    current = date.today().year
    first = int(httptools.downloadpage('{}/api/anime/advanced-search?page=0&size=1&sort=startDate,asc&sort=id'.format(host)).json[0]['startDate'].split('-')[0]) -1
    for year in range(current, first, -1):
        itemlist.append(
                item.clone(title = support.typo(year, 'bold'),
                        fulltitle= year,
                        show= year,
                        action= 'seasonal',
                        videolibrary= False,
                        variable= year,
                        thumbnail=support.thumb('az'))
        )

    return itemlist


def top_items(item):
    itemlist = []
    links = {'Top del giorno':'daily-top', 'Top della settimana':'weekly-top', 'Top del mese':'monthly-top'}
    for label in links:
        link = links[ label ]
        itemlist.append(
                item.clone(title = support.typo(label, 'bold'),
                    fulltitle= label,
                    show= label,
                    action= 'top_of',
                    videolibrary= False,
                    variable= link,
                )
        )
    return itemlist


def seasonal(item):
    itemlist = []
    url= '{}/api/seasonal-view?page=0&size=36&years={}'.format(host, item.variable)
    js = httptools.downloadpage(url).json[0]['seasonalAnime']
    for season in js:
        seasons = {'winter':'Inverno', 'spring':'Primavera', 'summer':'Estate', 'fall':'Autunno'}
        s = season['season'].split('.')[-1]
        title = seasons[s]
        itemlist.append(
            item.clone(title=title,
                url = '{}/api/seasonal-view/{}-{}'.format(host, s, item.variable),
                thumbnail = support.thumb(s),
                action = 'peliculas',
                variable=''
            )
        )
    return itemlist


def top_of(item):
    itemlist = []
    url= '{}/api/home/{}'.format(host, item.variable)
    js = httptools.downloadpage(url).json
    for anime in js:
        fulltitle = anime['animeTitle']
        title = fulltitle.split('(')[0].strip()
        scrapedlang = scrapertools.find_single_match(fulltitle, r'\(([^\)]+)')
        lang = scrapedlang.upper() if scrapedlang else 'Sub-ITA'
        long_title = support.typo(title, 'bold') + support.typo(lang, '_ [] color kod')

        itemlist.append(
            item.clone(title=long_title,
                id=anime['animeId'],
                url = '{}/api/anime/{}'.format(host, anime['animeId']),
                thumbnail = get_thumbnail(anime, prop='animeHorizontalImages'),
                action = 'episodios',
                variable=anime['animeId']
            )
        )

    return itemlist


def latest_added(item):
    itemlist = []
    page = item.page if item.page else 0
    url= '{}/api/home/latest-episodes?page={}'.format(host, page)
    js = httptools.downloadpage(url).json
    for episode in js:
        fulltitle = episode['title']
        title = fulltitle
        quality = episode['fullHd']
        lang = 'FHD' if quality else 'HD'
        long_title = support.typo(title, 'bold') + support.typo(lang, '_ [] color kod')
        itemlist.append(
            item.clone(
                title=long_title,
                animeId = episode['animeId'],
                id=episode['id'],
                contentType = 'episode',
                contentTitle = fulltitle,
                contentSerieName = episode['animeTitle'], 
                animeUrl = '{}/api/anime/{}'.format(host, episode['animeId']),
                thumbnail = get_thumbnail(episode, prop='episodeImages'),
                action = 'findvideos',
            )
        )
    support.nextPage(itemlist, item.clone(page = page + 1))
    return itemlist


def get_thumbnail(data, key = 'medium', prop = 'verticalImages'):
    """
    " Returns the vertical image as per given key and prop
    " possibile key values are:
    " - small
    " - full
    " - blurred
    " - medium
    " possibile prop values are:
    " - verticalImages
    " - animeHorizontalImages
    " - animeVerticalImages
    " - horizontalImages
    " - episodeImages
    """
    value = None
    verticalImages = data[prop]
    if verticalImages:
        first = verticalImages[0]
        if first:
            value = first[ 'image' + key.capitalize() ]
    return value


def search(item, texto):
    support.info(texto)
    item.url = host + '/api/anime/advanced-similar-search'
    item.variable = '&query=' + texto

    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.logger.error("%s" % line)
        return []

def peliculas(item):
    itemlist = []
    page = item.page if item.page else 0
    js = httptools.downloadpage('{}?page={}&size=36{}&sort=title,asc&sort=id'.format(item.url, page, item.variable)).json
    for it in js:
        title = it['title'].split('(')[0].strip()
        scrapedlang = scrapertools.find_single_match(it['title'], r'\(([^\)]+)')
        lang = scrapedlang.upper() if scrapedlang else 'Sub-ITA'
        long_title = support.typo(title, 'bold') + support.typo(lang, '_ [] color kod')
        itemlist.append(item.clone(title = long_title,
                                   fulltitle = title,
                                   show = title,
                                   contentLanguage = lang,
                                   contentType = 'tvshow' if it['type'] == 'Serie' else 'movie',
                                   contentTitle = title,
                                   contentSerieName = title if it['type'] == 'Serie' else '',
                                   action = 'episodios' if it['type'] == 'Serie' else 'findvideos',
                                   plot = it['storyline'],
                                   year = it['startDate'].split('-')[0],
                                   id= it['id']
                                   ))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    support.nextPage(itemlist, item.clone(page = page + 1))
    return itemlist

def episodios(item):
    support.info(item)

    # support.dbg()

    url = '{}/api/anime/{}'.format(host, item.id)

    json = httptools.downloadpage(url, CF=False ).json
    # json = jsontools.load( jsonDataStr )

    itemlist = []

    if 'seasons' in json and len(json['seasons']) > 0:
        seasons = json['seasons']

        seasons.sort(key=lambda s: s['episodeStart'])

        for i, it in enumerate(seasons):
            title = it['name'] # .split('(')[0].strip()

            itemlist.append(
                item.clone(title = title,
                    id= '{}/season/{}'.format(it['animeId'], it['id']),
                    contentType = 'season',
                    contentSeason = i,
                    action = 'episodios',
                    plot = json['storyline'],
                    year = it['yearStart']
                )
            )

    elif ('episodes' in json and len(json['episodes']) > 0) or len(json) > 0:
        episodes = json['episodes'] if 'episodes' in json else json

        episodes.sort(key=lambda ep: int(ep['episodeNumber']))

        itemlist = build_itemlist_by_episodes(episodes, item)

    # tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)

    return itemlist

def build_itemlist_by_episodes(episodes, item):
    itemlist = []
    # support.dbg()
    for it in episodes:
        title = it['title'] # .split('(')[0].strip()

        itemlist.append(
            item.clone(title = '{}x{:02d}. {}'.format(item.contentSeason if item.contentSeason else 1, int(it['episodeNumber']), title),
                id= it['id'],
                url= 'api/episode/{}'.format(it['id']),
                contentType = 'episode',
                contentEpisodeNumber = int(it['episodeNumber']),
                contentSeason = item.contentSeason if item.contentSeason else 1,
                action = 'findvideos',
                year = it['airingDate'].split('-')[0]
            )
        )
    return itemlist

def findvideos(item):
    support.info()

    url = '{}/api/{}/{}'.format(host, 'episode' if item.contentType == 'episode' else 'anime', item.id)

    json = httptools.downloadpage(url, CF=False ).json

    if json.get('episodes', []):
        json = httptools.downloadpage('{}/api/episode/{}'.format(host, json['episodes'][0]['id'])).json

    videourl = json['episodeVideo']

    itemlist = [
        item.clone(
            title=config.get_localized_string(30137),
            url=videourl,
            server='directo'
        )
    ]
    return support.server(item, itemlist=itemlist)