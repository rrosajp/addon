# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per AnimeUnity
# ------------------------------------------------------------

from core import support
from lib import cloudscraper
import requests, json

host = support.config.get_channel_url()
response = cloudscraper.create_scraper().get(host + '/archivio')
csrf_token = support.match(response.text, patron= 'name="csrf-token" content="([^"]+)"').match
headers = {'content-type': 'application/json;charset=UTF-8',
           'x-csrf-token': csrf_token,
           'Cookie' : '; '.join([x.name + '=' + x.value for x in response.cookies])}


@support.menu
def mainlist(item):
    top =  [('Ultimi Episodi', ['', 'news'])]

    menu = [('Film {bullet bold}',['', 'peliculas', {'type':'Movie'}]),
                ('ITA {submenu} {film}',['', 'peliculas', {'type':'Movie', 'title': '(ita)'}]),
                ('Genere {submenu} {film}',['', 'genres', {'type':'Movie'}]),
                ('Anno {submenu} {film}',['', 'years', {'type':'Movie'}]),
            ('TV {bullet bold}',['', 'peliculas', {'type':'TV'}, 'tvshow']),
                ('ITA {submenu} {tv}',['', 'peliculas', {'type':'TV', 'title': '(ita)'}, 'tvshow']),
                ('Genere {submenu} {tv}',['', 'genres', {'type':'TV'}, 'tvshow']),
                ('Anno {submenu} {tv}',['', 'years', {'type':'TV'}, 'tvshow']),
            ('OVA {bullet bold} {tv}',['', 'peliculas', ['type','OVA'], 'tvshow']),
                ('ITA {submenu} {tv}',['', 'peliculas', {'type':'OVA', 'title': '(ita)'}, 'tvshow']),
                ('Genere {submenu} {tv}',['', 'genres', {'type':'OVA'}, 'tvshow']),
                ('Anno {submenu} {tv}',['', 'years', {'type':'OVA'}, 'tvshow']),
            ('ONA {bullet bold} {tv}',['', 'peliculas', ['type','ONA'], 'tvshow']),
                ('ITA {submenu} {tv}',['', 'peliculas', {'type':'ONA', 'title': '(ita)'}, 'tvshow']),
                ('Genere {submenu} {tv}',['', 'genres', {'type':'ONA'}, 'tvshow']),
                ('Anno {submenu} {tv}',['', 'years', {'type':'ONA'}, 'tvshow']),
            ('Special {bullet bold} {tv}',['', 'peliculas', ['type','Special'], 'tvshow']),
                ('ITA {submenu} {tv}',['', 'peliculas', {'type':'Special', 'title': '(ita)'}, 'tvshow']),
                ('Genere {submenu} {tv}',['', 'genres', {'type':'Special'}, 'tvshow']),
                ('Anno {submenu} {tv}',['', 'years', {'type':'Special'}, 'tvshow']),
            ('Cerca... ', ['', 'search'])
    ]
    return locals()

def genres(item):
    support.log()
    itemlist = []

    genres = json.loads(support.match(response.text, patron='genres="([^"]+)').match.replace('&quot;','"'))

    for genre in genres:
        item.args['genre']=genre
        itemlist.append(item.clone(title=support.typo(genre,'bold'), action='peliculas'))
    return support.thumb(itemlist)

def years(item):
    support.log()
    itemlist = []

    from datetime import datetime
    current_year = datetime.today().year
    oldest_year = int(support.match(response.text, patron='anime_oldest_date="([^"]+)').match)

    for year in list(reversed(range(oldest_year, current_year + 1))):
        item.args['year']=year
        itemlist.append(item.clone(title=support.typo(year,'bold'), action='peliculas'))
    return itemlist


def search(item, text):
    support.log('search', item)
    item.args = {'title':text}
    item.search = text

    try:
        return peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.log('search log:', line)
        return []


def newest(categoria):
    support.log(categoria)
    itemlist = []
    item = support.Item()
    item.url = host

    try:
        itemlist = news(item)

        if itemlist[-1].action == 'news':
            itemlist.pop()
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.log(line)
        return []

    return itemlist

def news(item):
    support.log()
    item.contentType = 'tvshow'
    itemlist = []

    fullJs = json.loads(support.match(item, headers=headers, patron=r'items-json="([^"]+)"').match.replace('&quot;','"'))
    js = fullJs['data']

    for it in js:
        itemlist.append(
            item.clone(title= support.typo(it['anime']['title'] + ' - EP. ' + it['number'], 'bold'),
                    server='directo',
                    thumbnail=it['anime']['imageurl'],
                    forcethumb = True,
                    url=it['link'],
                    plot=it['anime']['plot'],
                    action='play')
        )
    if 'next_page_url' in fullJs:
        itemlist.append(item.clone(title=support.typo(support.config.get_localized_string(30992), 'color kod bold'),thumbnail=support.thumb(), url=fullJs['next_page_url']))
    return itemlist

def peliculas(item):
    support.log()
    itemlist = []

    page = item.page if item.page else 0
    item.args['offset'] = page * 30

    order = support.config.get_setting('order', item.channel)
    if order:
        order_list = [ "Standard", "Lista A-Z", "Lista Z-A", "Popolarità", "Valutazione" ]
        item.args['order'] = order_list[order]

    payload = json.dumps(item.args)
    records = requests.post(host + '/archivio/get-animes', headers=headers, data=payload).json()['records']
    js = []
    for record in records:
        js += record

    for it in js:
        lang = support.match(it['title'], patron=r'\(([It][Tt][Aa])\)').match
        title = support.re.sub(r'\s*\([^\)]+\)', '', it['title'])

        if 'ita' in lang.lower(): language = 'ITA'
        else: language = 'Sub-ITA'

        itm = item.clone(title=support.typo(title,'bold') + support.typo(language,'_ [] color kod') + (support.typo(it['title_eng'],'_ ()') if it['title_eng'] else ''))
        itm.contentLanguage = language
        itm.type = it['type']
        itm.thumbnail = it['imageurl']
        itm.plot = it['plot']

        if it['episodes_count'] == 1:
            itm.contentType = 'movie'
            itm.fulltitle = itm.show = itm.contentTitle = title
            itm.contentSerieName = ''
            itm.action = 'findvideos'
            itm.url = it['episodes'][0]['link']

        else:
            itm.contentType = 'tvshow'
            itm.contentTitle = ''
            itm.fulltitle = itm.show = itm.contentSerieName = title
            itm.action = 'episodios'
            itm.episodes = it['episodes'] if 'episodes' in it else it['link']
            itm.url = ''
            itm.contentType == 'episodios'

        itemlist.append(itm)

    if len(itemlist) >= 30:
        itemlist.append(item.clone(title=support.typo(support.config.get_localized_string(30992), 'color kod bold'),thumbnail=support.thumb(),page=page + 1))

    return itemlist

def episodios(item):
    support.log()
    itemlist = []
    title = 'Parte ' if item.type.lower() == 'movie' else 'Episodio'
    for it in item.episodes:
        itemlist.append(item.clone(title=support.typo(title + it['number'], 'bold'), action='findvideos', url=it['link']))
    return itemlist

def findvideos(item):
    support.log()
    return support.server(item,itemlist=[item.clone(title='Diretto', server='directo', action='play')])