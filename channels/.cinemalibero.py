# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per 'cinemalibero'

"""
    Questi sono commenti per i beta-tester.

    Su questo canale, nelle categorie:
    -'Ricerca Globale'
    - Novità, voce interna al canale
    - Nella lista anime
    non saranno presenti le voci:
    - 'Aggiungi alla Videoteca'
    - 'Scarica Film'/'Scarica Serie',
    Inoltre nella lista Anime non è presente la voce rinumerazione!
    dunque, la loro assenza, nel Test, NON dovrà essere segnalata come ERRORE.


    Novità ( globale ), presenti solo i film:
       - film ( 20 titoli ) della pagina https://www.cinemalibero.best/category/film/

    Avvisi:
        - Eventuali avvisi per i tester

    Ulteriori info:

"""

import re

# per l'uso dei decoratori, per i log, e funzioni per siti particolari
from core import support
# se non si fa uso di findhost()
from platformcode import config

# in caso di necessità
from core import scrapertoolsV2, httptools#, servertools
from core.item import Item # per newest
#from lib import unshortenit

# se necessaria la variabile __channel__
# da cancellare se non utilizzata
__channel__ = "cinemalibero"
# da cancellare se si utilizza findhost()
host = config.get_channel_url('cinemalibero')
headers = [['Referer', host]]

list_servers = ['akstream', 'wstream', 'openload', 'streamango']
list_quality = ['default']

### fine variabili

#### Inizio delle def principali ###

@support.menu
def mainlist(item):
    support.log(item)

    film = ['/category/film/',
            ('Generi', ['', 'genres', 'genres']),
            ]

    # Voce SERIE, puoi solo impostare l'url
    tvshow = ['/category/serie-tv/',
              ('Novità', ['/aggiornamenti-serie-tv/', 'peliculas', 'update'])
        ]
    # Voce ANIME, puoi solo impostare l'url
    Anime = [('Anime', ['/category/anime-giapponesi/', 'peliculas', 'anime', 'tvshow']), # url per la voce Anime, se possibile la pagina con titoli di anime
##        #Voce Menu,['url','action','args',contentType]
##        ('Novità', ['', '', '']),
##        ('In Corso',['', '', '', '']),
##        ('Ultimi Episodi',['', '', '', '']),
##        ('Ultime Serie',['', '', '', ''])
        ]


    search = ''

    return locals()


@support.scrape
def peliculas(item):
    support.log(item)
    #support.dbg() # decommentare per attivare web_pdb

    if item.args == 'search':
        patron = r'href="(?P<url>[^"]+)".+?url\((?P<thumb>[^\)]+)\)">.+?class="titolo">(?P<title>[^<]+)<'
        patronBlock = r'style="color: #2C3549 !important;" class="fon my-3"><small>.+?</small></h1>(?P<block>.*?)<div class="bg-dark ">'
        action = 'select'
    else:
        if item.contentType == 'tvshow':
            if item.args == 'update':
                patron = r'<div class="card-body p-0">\s<a href="(?P<url>[^"]+)".+?url\((?P<thumb>.+?)\)">\s<div class="titolo">(?P<title>.+?)(?: &#8211; Serie TV)?(?:\([sSuUbBiItTaA\-]+\))?[ ]?(?P<year>\d{4})?</div>[ ]<div class="genere">(?:[\w]+?\.?\s?[\s|S]?[\dx\-S]+?\s\(?(?P<lang>[iItTaA]+|[sSuUbBiItTaA\-]+)\)?\s?(?P<quality>[HD]+)?|.+?\(?(?P<lang2>[sSuUbBiItTaA\-]+)?\)?</div>)'
                action = 'select'

                def itemHook(item):
                    if item.lang2:
                        if len(item.lang2) <3:
                            item.lang2 = 'ITA'
                        item.contentLanguage = item.lang2
                        item.title += support.typo(item.lang2, '_ [] color kod')
                    return item

            elif item.args == 'anime':# or 'anime' in item.url:
                patron = r'<div class="card-body p-0"> <a href="(?P<url>[^"]+)".+?url\((?P<thumb>.+?)\)">[^>]+>[^>]+>[^>]+>(?:[ ](?P<rating>\d+.\d+))?[^>]+>[^>]+>(?P<title>.+?)(?:\([sSuUbBiItTaA\-]+\))?\s?(?:(?P<year>\d{4}|\(\d{4}\)|)?)?<[^>]+>(?:<div class="genere">.+?(?:\()?(?P<lang>ITA|iTA|Sub)(?:\))?)?'
                action = 'select'
            else:
                patron = r'<div class="card-body p-0">\s?<a href="(?P<url>[^"]+)".+?url\((?P<thumb>.+?)\)">[^>]+>[^>]+>[^>]+>[^>]+>[^>]+>(?P<title>[^<]+)</div>(?:<div class="genere">(?:[ |\w]+?(?:[\dx\-]+)?[ ](?:\()?(?P<lang>[sSuUbB]+|[iItTaA]+)(?:\))?\s?(?P<quality>[\w]+)?\s?|[\s|S]?[\dx\-]+\s[|]?\s?(?:[\w]+)?\s?\(?(\4[sSuUbB]+)?\)?)?.+?</div>)?'
                action = 'episodios'

        elif item.contentType == 'movie':
            action = 'findvideos'
            patron = r'href="(?P<url>[^"]+)".+?url\((?P<thumb>.+?)\)">[^>]+>[^>]+>[^>]+>(?:[ ](?P<rating>\d+.\d+))?[^>]+>[^>]+>(?P<title>.+?)(?:\[(?P<lang>Sub-iTA|Sub-ITA|Sub)\])?[ ]\((?P<year>\d+)\)</div>(?:<div class="genere">(?P<quality>[^<]+)<)?'

        patronBlock = r'<h1(?: style="color: #2C3549 !important; text-transform: uppercase;"| style="text-transform: uppercase; color: #2C3549 !important;"| style="color: #2C3549 !important; text-transform: uppercase;" style="text-shadow: 1px 1px 1px #FF8C00; color:#FF8C00;"| style="text-shadow: 1px 1px 1px #0f0f0f;" class="darkorange"| style="color:#2C3549 !important;")>.+?</h1>(?P<block>.*?)<div class=(?:"container"|"bg-dark ")>'

    patronNext = '<a class="next page-numbers".*?href="([^"]+)">'

##    debug = True  # True per testare le regex sul sito
    return locals()

@support.scrape
def episodios(item):
    support.log(item)
    #support.dbg()

    data = item.data1
    if item.args == 'anime':
        item.contentType = 'tvshow'
        blacklist = ['Clipwatching', 'Verystream', 'Easybytez']
        patron = r'(?:href="[ ]?(?P<url>[^"]+)"[^>]+>(?P<title>[^<]+)<|(?P<episode>\d+(?:&#215;|×)?\d+\-\d+|\d+(?:&#215;|×)\d+)[;]?(?:(\4[^<]+)(\2.*?)|(\2[ ])(?:<(\3.*?)))(?:</a><br />|</a></p>))'
        #patron = r'<a target=.+?href="(?P<url>[^"]+)"[^>]+>(?P<title>(Epis|).+?(?P<episode>\d+)?)(?:\((?P<lang>Sub ITA)\))?</a>(?:<br />)?'
        patronBlock = r'(?:class="txt_dow">Streaming:(?P<block>.*?)at-below-post)'
    else:
        patron = r'(?P<episode>\d+(?:&#215;|×)?\d+\-\d+|\d+(?:&#215;|×)\d+)[;]?[ ]?(?:(?P<title>[^<]+)(?P<url>.*?)|(\2[ ])(?:<(\3.*?)))(?:</a><br />|</a></p>)'
##        patron = r'<a target=.+?href="(?P<url>[^"]+)"[^>]+>(?P<title>Epis.+?(\d+)?)(?:\((?P<lang>Sub ITA)\))?</a><br />'
        patronBlock = r'<p><strong>(?P<block>(?:.+?[Ss]tagione.+?(?P<lang>iTA|ITA|Sub-ITA|Sub-iTA))?(?:|.+?|</strong>)(/?:</span>)?</p>.*?</p>)'
        item.contentType = 'tvshow'

    action = 'findvideos'

    debug = True
    return locals()


@support.scrape
def genres(item):
    support.log(item)
    #support.dbg()

    action = 'peliculas'
    #blacklist = ['']
    patron = r'<a class="dropdown-item" href="(?P<url>[^"]+)" title="(?P<title>[A-z]+)"'

    return locals()

############## Fine ordine obbligato
## Def ulteriori

def select(item):
    support.log('select --->', item)
    #support.dbg()
    data = httptools.downloadpage(item.url, headers=headers).data
    block = scrapertoolsV2.find_single_match(data, r'<div class="col-md-8 bg-white rounded-left p-5"><div>(.*?)<div style="margin-left: 0.5%; color: #FFF;">')
    if re.findall('rel="category tag">serie', data, re.IGNORECASE):
        support.log('select = ### è una serie ###')
        return episodios(Item(channel=item.channel,
                              title=item.title,
                              fulltitle=item.fulltitle,
                              url=item.url,
                              args='serie',
                              contentType='tvshow',
                              data1 = data
                              ))
    elif re.findall('rel="category tag">anime', data, re.IGNORECASE):
        if re.findall('episodio', block, re.IGNORECASE) or re.findall('stagione', data, re.IGNORECASE) or re.findall('numero stagioni', data, re.IGNORECASE):
            support.log('select = ### è un anime ###')
            return episodios(Item(channel=item.channel,
                                title=item.title,
                                fulltitle=item.fulltitle,
                                url=item.url,
                                args='anime',
                                contentType='tvshow',
                                data1 = data
                                  ))
        else:
            support.log('select = ### è un film ###')
            return findvideos(Item(channel=item.channel,
                                    title=item.title,
                                    fulltitle=item.fulltitle,
                                    url=item.url,
                                    args = '',
                                    contentType='movie',
                                    #data = data
                                   ))
    else:
        support.log('select = ### è un film ###')
        return findvideos(Item(channel=item.channel,
                              title=item.title,
                              fulltitle=item.fulltitle,
                              url=item.url,
                              contentType='movie',
                              #data = data
                               ))

############## Fondo Pagina
# da adattare al canale
def search(item, text):
    support.log('search', item)
    itemlist = []
    text = text.replace(' ', '+')
    item.url = host + "/?s=" + text
    item.contentType = item.contentType
    try:
        item.args = 'search'
        item.contentType = 'episode' # non fa uscire le voci nel context menu
        return peliculas(item)
    # Se captura la excepcion, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            support.log('search log:', line)
        return []


# da adattare al canale
# inserire newest solo se il sito ha la pagina con le ultime novità/aggiunte
# altrimenti NON inserirlo
def newest(categoria):
    support.log('newest ->', categoria)
    itemlist = []
    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = host+'/category/film/'
            item.contentType = 'movie'
##            item.action = 'peliculas'
##            itemlist = peliculas(item)
        elif categoria == 'series':
            item.contentType = 'tvshow'
            item.args = 'update'
            item.url = host+'/aggiornamenti-serie-tv/'
        item.action = 'peliculas'
        itemlist = peliculas(item)

        if itemlist[-1].action == 'peliculas':
            itemlist.pop()
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            support.log('newest log: ', {0}.format(line))
        return []

    return itemlist


#support.server(item, data='', itemlist=[], headers='', AutoPlay=True, CheckLinks=True)
def findvideos(item):
    support.log('findvideos ->', item)
    #return support.server(item, headers=headers)
    support.log(item)
    if item.contentType == 'movie':
        return support.server(item)
    else:
        return support.server(item, data= item.url)
