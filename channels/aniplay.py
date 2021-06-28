# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per 'aniplay'
# By: fatshotty!
# ringrazio mia mamma
# ------------------------------------------------------------
# Rev: 0.1

# Qui gli import

# per l'uso dei decoratori, per i log, e funzioni per siti particolari
from core import support, config, tmdb
from datetime import datetime
# in caso di necessità
from core import scrapertools, httptools, jsontools
from core.item import Item 

host = config.get_channel_url()
headers = [['Referer', host]]


@support.menu
def mainlist(item):
    support.info(item)

    # Voce ANIME, puoi solo impostare l'url
    top = [ # url per la voce Anime, se possibile la pagina con titoli di anime
        #Voce Menu,['url','action','args',contentType]
        ('Lista Anime', ['/ricerca-avanzata', 'alphabetical_strip', ''])
        # ('Calendario',['/calendario', 'calendar', '', '']),
        # ('News',['/news', 'newest', '', '']),
        # ('Anime stagionali',['/anime-stagionali', 'seasonal', '', ''])
        ]
    
    ontop = [
        ('Top di oggi',['/api/home/daily-top', 'toplist', '']),
        ('Top della settimana',['/api/home/weekly-top', 'toplist', '']),
        ('Top del mese',['/api/home/monthly-top', 'toplist', ''])
    ]

    # stagionali = ['' , get_seasonal_menu()]

    search = ''

    return locals()



def get_seasonal_menu():
    today = datetime.today()
    years = [
        str(today.year),
        str(today.year - 1),
        str(today.year - 2),
        str(today.year - 3)
    ]
    url = '{}/api/seasonal-view?page=0&size=36&years={}'.format( host, ','.join(years) )
    
    jsonDataStr = httptools.downloadpage(url, CF=False ).data
    json = jsontools.load( jsonDataStr )
    
    seasonal = ()

    for year in json:
        y = year['year']
        seasons = year['seasonalAnime']
        for season in seasons:
            seasonStr = season['season']
            stagione = 'Autunno'
            if 'winter' in seasonStr:
                stagione = 'Inverno'
            elif 'spring' in seasonStr:
                stagione = 'Primavera'
            elif 'summer' in seasonStr:
                stagione = 'Estate'
            seasonal = seasonal + ( '{} {} ({})'.format(stagione, str(y) , str(season['animeCount']) )  , ['', 'seasonal', ''])
    
    return seasonal

def toplist(item):
    
    url = item.url
    jsonDataStr = httptools.downloadpage(url, CF=False ).data
    json = jsontools.load( jsonDataStr )
    itemlist = []
    for it in json:

        title = it['animeTitle'].split('(')[0].strip()
        scrapedlang = scrapertools.find_single_match(it['animeTitle'], r'\(([^\)]+)')
        lang = scrapedlang.upper() if scrapedlang else 'Sub-ITA'
        long_title = support.typo(title, 'bold') + support.typo(lang, '_ [] color kod')


        itemlist.append( 
            item.clone(
                id= it['animeId'],
                url = 'api/anime/{}'.format(it['animeId']),
                title = long_title,
                show = title,
                contentLanguage = lang,
                contentType = 'tvshow',
                contentTitle = title,
                contentSerieName = title,
                action = 'episodios' ,
                videolibrary= True,
                thumbnail= get_thumbnail(it, prop ='animeHorizontalImages' )
            )
        )
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    return itemlist



def seasonal(item):
    pass

# Legenda known_keys per i groups nei patron
# known_keys = ['url', 'title', 'title2', 'season', 'episode', 'thumb', 'quality',
#                'year', 'plot', 'duration', 'genere', 'rating', 'type', 'lang']
# url = link relativo o assoluto alla pagina titolo film/serie
# title = titolo Film/Serie/Anime/Altro
# title2 = titolo dell'episodio Serie/Anime/Altro
# season = stagione in formato numerico
# episode = numero episodio, in formato numerico.
# thumb = linkrealtivo o assoluto alla locandina Film/Serie/Anime/Altro
# quality = qualità indicata del video
# year = anno in formato numerico (4 cifre)
# duration = durata del Film/Serie/Anime/Altro
# genere = genere del Film/Serie/Anime/Altro. Es: avventura, commedia
# rating = punteggio/voto in formato numerico
# type = tipo del video. Es. movie per film o tvshow per le serie. Di solito sono discrimanti usati dal sito
# lang = lingua del video. Es: ITA, Sub-ITA, Sub, SUB ITA.
# AVVERTENZE: Se il titolo è trovato nella ricerca TMDB/TVDB/Altro allora le locandine e altre info non saranno quelle recuperate nel sito.!!!!
@support.scrape
def peliculas(item):
    pass



def alphabetical_strip(item):
    # support.dbg()
    itemlist = []
    alphabet = ("0-9, A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X, Y, Z").split(', ')
    for letter in alphabet:
        itemlist.append(
                item.clone(
                    title = support.typo(letter, 'bold'),
                    fulltitle= letter,
                    show= letter,
                    letter = letter.upper(),
                    action= 'alphabetical_letter',
                    videolibrary= False)
        )
    
    return itemlist


def alphabetical_letter(item):
    # support.dbg()
    page = item.page if item.page else 0
    url = '{}/api/anime/find-by-char?page={}&size=36&character={}&sort=title,asc&sort=id'.format( host, page, item.letter )
    
    jsonDataStr = httptools.downloadpage(url, CF=False ).data
    json = jsontools.load( jsonDataStr )
    
    itemlist = []
    
    for it in json:
        title = it['title'].split('(')[0].strip()
        scrapedlang = scrapertools.find_single_match(it['title'], r'\(([^\)]+)')
        lang = scrapedlang.upper() if scrapedlang else 'Sub-ITA'
        long_title = support.typo(title, 'bold') + support.typo(lang, '_ [] color kod')

        thumb = get_thumbnail(it, 'medium')

        itemlist.append(item.clone(title = long_title,
                                    id= it['id'],
                                    url = 'api/anime/{}'.format(it['id']),
                                   fulltitle = title,
                                   show = title,
                                   contentLanguage = lang,
                                   contentType = 'tvshow' if it['type'] == 'Serie' else 'movie',
                                   contentTitle = title,
                                   contentSerieName = title if it['type'] == 'Serie' else '',
                                   action = 'episodios' if it['type'] == 'Serie' else 'findvideos',
                                   plot = it['storyline'],
                                   year = it['startDate'].split('-')[0],
                                   thumbnail = thumb,
                                   videolibrary= True
                                   ))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    support.nextPage(itemlist, item.clone(page = page + 1))
    return itemlist



def get_thumbnail(data, key = 'medium', prop = 'verticalImages'):
    """
    " Returns the vertical image as per given key
    " possibile values are:
    " - small
    " - full
    " - blurred
    " - medium
    """
    value = None
    verticalImages = data[prop]
    if verticalImages:
        first = verticalImages[0]
        if first:
            value = first[ 'image' + key.capitalize() ]
    return value


def episodios(item):
    support.info(item)

    support.dbg()

    url = '{}/{}'.format(host, item.url)

    jsonDataStr = httptools.downloadpage(url, CF=False ).data
    json = jsontools.load( jsonDataStr )

    itemlist = []

    if 'seasons' in json and len(json['seasons']) > 0:
        seasons = json['seasons']

        seasons.sort(key=lambda s: s['episodeStart'])
        
        for it in seasons:
            title = it['name'] # .split('(')[0].strip()

            itemlist.append(
                item.clone(title = title,
                    id= it['id'],
                    url= 'api/anime/{}/season/{}'.format(it['animeId'], it['id']),
                    fulltitle = it['name'],
                    show = json['title'],
                    contentType = 'season',
                    contentTitle = title,
                    contentSerieName = json['title'],
                    action = 'episodios',
                    plot = json['storyline'],
                    year = it['yearStart']
                )
            )

    elif ('episodes' in json and len(json['episodes']) > 0) or len(json) > 0:
        episodes = json['episodes'] if 'episodes' in json else json

        episodes.sort(key=lambda ep: int(ep['episodeNumber']))
        
        for it in episodes:
            title = it['title'] # .split('(')[0].strip()

            itemlist.append(
                item.clone(title = title,
                    id= it['id'],
                    url= 'api/episode/{}'.format(it['id']),
                    fulltitle = title,
                    #    contentLanguage = lang,
                    contentType = 'episode',
                    contentTitle = title,
                    action = 'findvideos',
                    year = it['airingDate'].split('-')[0]
                )
            )

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    
    return itemlist

# Questa def è utilizzata per generare i menu del canale
# per genere, per anno, per lettera, per qualità ecc ecc
@support.scrape
def genres(item):
    support.info(item)
    #support.dbg()

    action = ''
    blacklist = ['']
    patron = r''
    patronBlock = r''
    patronNext = ''
    pagination = ''

    #debug = True
    return locals()

############## Fine ordine obbligato
## Def ulteriori

# per quei casi dove il sito non differenzia film e/o serie e/o anime
# e la ricerca porta i titoli mischiati senza poterli distinguere tra loro
# andranno modificate anche le def peliculas e episodios ove occorre
def select(item):
    support.info('select --->', item)
    #support.dbg()
    data = httptools.downloadpage(item.url, headers=headers).data
    # pulizia di data, in caso commentare le prossime 2 righe
    data = re.sub('\n|\t', ' ', data)
    data = re.sub(r'>\s+<', '> <', data)
    block = scrapertools.find_single_match(data, r'')
    if re.findall('', data, re.IGNORECASE):
        support.info('select = ### è una serie ###')
        return episodios(Item(channel=item.channel,
                              title=item.title,
                              fulltitle=item.fulltitle,
                              url=item.url,
                              args='serie',
                              contentType='tvshow',
                              #data1 = data decommentando portiamo data nella def senza doverla riscaricare
                            ))

############## Fondo Pagina
# da adattare al canale
def search(item, text):
    support.info('search', item)
    itemlist = []
    text = text.replace(' ', '+')
    item.url = host + '/index.php?do=search&story=%s&subaction=search' % (text)
    # bisogna inserire item.contentType per la ricerca globale
    # se il canale è solo film, si può omettere, altrimenti bisgona aggiungerlo e discriminare.
    item.contentType = item.contentType
    try:
        return peliculas(item)
    # Se captura la excepcion, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            info('search log:', line)
        return []


# da adattare al canale
# inserire newest solo se il sito ha la pagina con le ultime novità/aggiunte
# altrimenti NON inserirlo
def newest(categoria):
    support.info('newest ->', categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = host
            item.action = 'peliculas'
            itemlist = peliculas(item)

            if itemlist[-1].action == 'peliculas':
                itemlist.pop()
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.info('newest log: ', {0}.format(line))
        return []

    return itemlist

# da adattare...
# consultare il wiki sia per support.server che ha vari parametri,
# sia per i siti con hdpass
#support.server(item, data='', itemlist=[], headers='', AutoPlay=True, CheckLinks=True)
def findvideos(item):
    support.info('findvideos ->', item)
    support.dbg()

    urlpath = item.url

    url = '{}/{}'.format(host, urlpath)

    jsonDataStr = httptools.downloadpage(url, CF=False ).data
    json = jsontools.load( jsonDataStr )

    videourl = json['episodeVideo']

    itemlist = [
        item.clone(
            url=videourl,
            server='directo'
        )
    ]
    return support.server(item, itemlist=itemlist)



def make_itemlist(itemlist, item, data):
    search = item.search if item.search else ''
    infoLabels = {}
    for key in data['data']:
        if search.lower() in encode(key['title']).lower():
            title = encode(key['title'])
            fulltitle=title.split('-')[0].strip()
            infoLabels['year'] = key['date_published']
            infoLabels['title'] = fulltitle
            if item.contentType != 'movie': infoLabels['tvshowtitle'] = fulltitle
            itemlist.append(
                item.clone(title = support.typo(title, 'bold'),
                           fulltitle= title,
                           show= title,
                           url= main_host + str(key['show_id']) + '/seasons/',
                           action= 'findvideos' if item.contentType == 'movie' else 'episodios',
                           contentType = item.contentType,
                           contentSerieName= fulltitle if item.contentType != 'movie' else '',
                           contentTitle= fulltitle if item.contentType == 'movie' else '',
                           infoLabels=infoLabels,
                           videolibrary=False))
    return itemlist