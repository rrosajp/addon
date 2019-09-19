# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per 'idcanale nel json'
# ------------------------------------------------------------
# Rev: 0.2
# Update 18-09-2019
# fix:
# 1. aggiunto pagination e sistemate alcune voci

# Questo vuole solo essere uno scheletro per velocizzare la scrittura di un canale.
# I commenti sono più un promemoria... che una vera e propria spiegazione!
# Niente di più.
# Ulteriori informazioni sono reperibili nel wiki:
# https://github.com/kodiondemand/addon/wiki/decoratori
"""

    Problemi noti che non superano il test del canale:
       - indicare i problemi

    Avvisi:
        - Eventuali avvisi per i tester

    Ulteriori info:


"""
# CANCELLARE Ciò CHE NON SERVE per il canale, lascia il codice commentato
# ma fare PULIZIA quando si è finito di testarlo

# Qui gli import
#import re

# per l'uso dei decoratori, per i log, e funzioni per siti particolari
from core import support
# se non si fa uso di findhost()
from platformcode import config

# in caso di necessità
#from core import scrapertoolsV2, httptools, servertools, tmdb
#from core.item import Item
#from lib import unshortenit

##### fine import

# impostazioni variabili o def findhost()

# se necessaria la variabile __channel__
# da cancellare se non utilizzata
__channel__ = "id nel json"
# da cancellare se si utilizza findhost()
host = config.get_channel_url('id nel json OR '__channel__) # <-- ATTENZIONE
headers = [['Referer', host]]

# Inizio findhost() - da cancellare se usato l'altro metodo
#impostati dinamicamente da findhost()
host = ""
headers = ""

def findhost():
    global host, headers
    # da adattare alla bisogna...
    permUrl = httptools.downloadpage('INSERIRE-URL-QUI', follow_redirects=False).headers
    host = 'https://www.'+permUrl['location'].replace('https://www.google.it/search?q=site:', '')
    # cancellare host non utilizzato
    host = scrapertoolsV2.find_single_match(data, r'<div class="elementor-button-wrapper"> <a href="([^"]+)"')
    headers = [['Referer', host]]

findhost() # così le imposta una volta per tutte
### fine findhost

# server di esempio...
list_servers = ['supervideo', 'streamcherry','rapidvideo', 'streamango', 'openload']
# quality di esempio
list_quality = ['default', 'HD', '3D', '4K', 'DVD', 'SD']

### fine variabili

#### Inizio delle def principali ###

@support.menu
def mainlist(item):
    support.log(item)

    # Ordine delle voci
    # Voce FILM, puoi solo impostare l'url
    film = ['',
        #'url', # url per la voce FILM, se possibile la pagina principale con le ultime novità
        #Voce Menu,['url','action','args',contentType]
        ('Al Cinema', ['', 'peliculas', '']),
        ('Generi', ['', 'genres', 'genres']),
        ('Per Lettera', ['', 'genres', 'letters']),
        ('Anni', ['', 'genres', 'years']),
        ('Qualità', ['', 'genres', 'quality']),
        ('Mi sento fortunato', ['', 'genres', 'lucky']),
        ('Popolari', ['', 'peliculas', '']),
        ('Sub-ITA', ['', 'peliculas', ''])
        ]

    # Voce SERIE, puoi solo impostare l'url
    tvshow = ['',
        #'url', # url per la voce Serie, se possibile la pagina principale con le ultime novità
        #Voce Menu,['url','action','args',contentType]
        ('Per Lettera', ['', 'genres', 'letters']),
        ('Per Genere', ['', 'genres', 'genres']),
        ('Per anno', ['', 'genres', 'years'])

    # Voce ANIME, puoi solo impostare l'url
    anime = ['',
        #'url', # url per la voce Anime, se possibile la pagina principale con le ultime novità
        #Voce Menu,['url','action','args',contentType]
        ('In Corso',['', '', '', '']),
        ('Ultimi Episodi',['', '', '', '']),
        ('Ultime Serie',['', '', '', ''])
        ]

    """
        Eventuali Menu per voci non contemplate!
    """

    # se questa voce non è presente il menu genera una voce
    # search per ogni voce del menu. Es. Cerca Film...
    search = '' # se alla funzione search non serve altro

    # VOCE CHE APPARIRA' come prima voce nel menu di KOD!
    # [Voce Menu,['url','action','args',contentType]
    top = [ '' ['', '', '', ''])

    # Se vuoi creare un menu personalizzato o perchè gli altri non
    # ti soddisfano
    # [Voce Menu,['url','action','args',contentType]
    nome = [( '' ['', '', '', ''])
    return locals()

# riepilogo key per il match nei patron
# known_keys = ['url', 'title', 'title2', 'season', 'episode', 'thumb', 'quality',
#                'year', 'plot', 'duration', 'genere', 'rating', 'type', 'lang']
# url = link relativo o assoluto
# title = titolo Film/Serie/Anime/Altro
# title2 = titolo dell'episodio Serie/Anime/Altro
# season = stagione in formato numerico
# episode = numero episodio, in formato numerico. Se il sito ha stagionexepisodio potete omettere season
# thumb = locandina Film/Serie/Anime/Altro
# quality = qualità indicata del video
# year = anno in formato numerico (4 cifre)
# duration = durata del Film/Serie/Anime/Altro
# genere = genere del Film/Serie/Anime/Altro. Es: avventura, commedia
# rating = punteggio/voto in formato numerico
# type = tipo del video. Es. movie per film o tvshow per le serie. Di solito sono discrimanti usati dal sito
# lang = lingua del video. Es: ITA, Sub-ITA, Sub, SUB ITA. Se non appare 'ITA' è di default


@support.scrape
def peliculas(item):
    support.log(item)
    #dbg # decommentare per attivare web_pdb

    action = ''
    blacklist = ['']
    patron = r''
    patronBlock = r''
    patronNext = ''
    pagination = 0

    debug = False  # True per testare le regex sul sito
    return locals()

@support.scrape
def episodios(item):
    support.log(item)
    #dbg

    action = ''
    blacklist = ['']
    patron = r''
    patronBlock = r''
    patronNext = ''
    pagination = 0

    debug = False
    return locals()

# Questa def è utilizzata per generare i menu del canale
# per genere, per anno, per lettera, per qualità ecc ecc
@support.scrape
def genres(item):
    support.log(item)
    #dbg

    action = ''
    blacklist = ['']
    patron = r''
    patronBlock = r''
    patronNext = ''
    pagination = 0

    debug = False
    return locals()

############## Fine ordine obbligato
## Def ulteriori

############## Fondo Pagina
# da adattare al canale
def search(item, text):
    support.log('search', item)
    itemlist = []
    text = text.replace(' ', '+')
    item.url = '/index.php?do=search&story=%s&subaction=search' % (text)
    # bisogna inserire item.contentType per la ricerca globale
    # se il canale è solo film, si può omettere, altrimenti bisgona aggiungerlo e discriminare.
    item.contentType = item.contentType
    try:
        return peliculas(item)
    # Se captura la excepcion, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            log('search log:', line)
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
            item.url = host
            item.action = 'peliculas'
            itemlist = peliculas(item)

            if itemlist[-1].action == 'peliculas':
                itemlist.pop()
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            log('newest log: ', {0}.format(line))
        return []

    return itemlist

# da adattare... ( support.server ha vari parametri )
#support.server(item, data='', itemlist=[], headers='', AutoPlay=True, CheckLinks=True)
def findvideos(item):
    support.log('findvideos ->', item)
    return support.server(item, headers=headers)

