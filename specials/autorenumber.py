# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# autorenumber - Rinomina Automaticamente gli Episodi
# --------------------------------------------------------------------------------

'''
USO:
1) utilizzare autorenumber.renumber(itemlist) nelle le funzioni peliculas e similari per aggiungere il menu contestuale
2) utilizzare autorenumber.renumber(itemlist, item, typography) nella funzione episodios

3) Aggiungere le seguinti stringhe nel json del canale (per attivare la configurazione di autonumerazione del canale)
{
    "id": "autorenumber",
    "type": "bool",
    "label": "@70712",
    "default": false,
    "enabled": true,
    "visible": true
},
{
    "id": "autorenumber_mode",
    "type": "bool",
    "label": "@70688",
    "default": false,
    "enabled": true,
    "visible": "eq(-1,true)"
}
'''

try:
    import xbmcgui
except:
    xbmcgui = None
import xbmc
import re, base64, json, os, inspect
from core import jsontools, tvdb, scrapertoolsV2
from core.support import typo, log, dbg
from platformcode import config, platformtools,  logger
from platformcode.config import get_setting

TAG_TVSHOW_RENUMERATE = "TVSHOW_AUTORENUMBER"
TAG_ID = "ID"
TAG_SEASON = "Season"
TAG_EPISODE = "Episode"
TAG_SPECIAL = "Special"
TAG_MODE = "Mode"
TAG_EPLIST = "EpList"
TAG_CHECK = "ReCheck"
TAG_SPLIST = "SpList"
TAG_TYPE = "Type"

__channel__ = "autorenumber"

def access():
    allow = False

    if config.is_xbmc():
        allow = True

    return allow

def context(exist):
    if access():
        modify = config.get_localized_string(70714) if exist else ''
        _context = [{"title": typo(modify + config.get_localized_string(70585), 'bold'),
                     "action": "select_type",
                     "channel": "autorenumber",}]

    return _context

def select_type(item):
    select = platformtools.dialog_select(config.get_localized_string(70730),[typo(config.get_localized_string(70731),'bold'), typo(config.get_localized_string(70732),'bold')])
    if select == 0: semiautomatic_config_item(item)
    else: manual_renumeration(item)

def manual_renumeration(item, modify=False):
    log()
    _list = []
    if item.from_channel: item.channel = item.from_channel
    title = item.show if item.show else item.fulltitle

    dict_series = jsontools.get_node_from_file(item.channel, TAG_TVSHOW_RENUMERATE)
    if not dict_series.has_key(title): dict_series[title] = {}

    if dict_series[title].has_key(TAG_EPISODE) and dict_series[title][TAG_EPISODE]:
        EpisodeDict = json.loads(base64.b64decode(dict_series[title][TAG_EPISODE]))
        del dict_series[title][TAG_EPISODE]
    else: EpisodeDict = {}

    if dict_series[title].has_key(TAG_EPLIST): del dict_series[title][TAG_EPLIST]
    if dict_series[title].has_key(TAG_MODE): del dict_series[title][TAG_MODE]
    if dict_series[title].has_key(TAG_CHECK): del dict_series[title][TAG_CHECK]
    if dict_series[title].has_key(TAG_SEASON): del dict_series[title][TAG_SEASON]
    if dict_series[title].has_key(TAG_SPECIAL): del dict_series[title][TAG_SPECIAL]
    dict_series[title][TAG_TYPE] = 'manual'

    jsontools.update_node(dict_series, item.channel, TAG_TVSHOW_RENUMERATE)[0]
    if not dict_series[title].has_key(TAG_ID) or (dict_series[title].has_key(TAG_ID) and not dict_series[title][TAG_ID]):
        tvdb.find_and_set_infoLabels(item)

        # Trova l'ID della serie
        while not item.infoLabels['tvdb_id']:
            try:
                item.show = platformtools.dialog_input(default=item.show, heading=config.get_localized_string(30112)) # <- Enter title to search
                tvdb.find_and_set_infoLabels(item)
            except:
                heading = config.get_localized_string(70704) # <- TMDB ID (0 to cancel)
                info = platformtools.dialog_numeric(0, heading)
                item.infoLabels['tvdb_id'] = '0' if info == '' else info

        if item.infoLabels['tvdb_id']:
            ID = item.infoLabels['tvdb_id']
            dict_renumerate = {TAG_ID: ID}
            dict_series[title] = dict_renumerate

    # channel = __import__('channels.' + item.channel, fromlist=["channels.%s" % item.channel])
    itemlist = find_episodes(item)
    for item in itemlist:
        Title = re.sub(r'\d+x\d+ - ', '', item.title)
        if modify == True:
            ep = int(scrapertoolsV2.find_single_match(Title, r'(\d+)'))
            if item.action == 'findvideos' and not EpisodeDict.has_key(str(ep)):
                _list.append(Title)
        else:
            if item.action == 'findvideos':
                _list.append(Title)

    count = 1
    preselect = platformtools.dialog_select(config.get_localized_string(70732),[typo(config.get_localized_string(70518),'bold'),typo(config.get_localized_string(70519),'bold')])
    selection = []
    if preselect == 0:
        for i in _list:
            selection.append(_list.index(i))
    while len(_list) > 0:
        selected = platformtools.dialog_multiselect(config.get_localized_string(70734), _list, preselect=selection)
        if selected == None: break
        season = ''
        while not season:
            season = platformtools.dialog_numeric(0, config.get_localized_string(70733))
        for select in selected:
            ep = int(scrapertoolsV2.find_single_match(_list[select], r'(\d+)'))
            if season == '0':
                episode = ''
                while not episode:
                    episode = platformtools.dialog_numeric(0, config.get_localized_string(70735) % _list[select] )
                EpisodeDict[str(ep)] = '%sx%s' %(season, episode.zfill(2))
            else:
                EpisodeDict[str(ep)] = '%sx%s' %(season, str(count).zfill(2))
                count += 1

        for select in reversed(selected):
            del _list[select]


    dict_series[title][TAG_TYPE] = 'manual'
    EpisodeDict = base64.b64encode(json.dumps(EpisodeDict))
    dict_series[title][TAG_EPISODE] = EpisodeDict
    jsontools.update_node(dict_series, item.channel, TAG_TVSHOW_RENUMERATE)[0]
    xbmc.executebuiltin("Container.Refresh")
    if modify == True:
        return json.loads(base64.b64decode(EpisodeDict))


def semiautomatic_config_item(item):
    log()
    # Configurazione Semi Automatica, utile in caso la numerazione automatica fallisca

    tvdb.find_and_set_infoLabels(item)
    item.channel = item.from_channel
    dict_series = jsontools.get_node_from_file(item.channel, TAG_TVSHOW_RENUMERATE)
    title = item.show

    # Trova l'ID della serie
    while not item.infoLabels['tvdb_id']:
        try:
            item.show = platformtools.dialog_input(default=item.show, heading=config.get_localized_string(30112)) # <- Enter title to search
            tvdb.find_and_set_infoLabels(item)
        except:
            heading = config.get_localized_string(70704) # <- TMDB ID (0 to cancel)
            info = platformtools.dialog_numeric(0, heading)
            item.infoLabels['tvdb_id'] = '0' if info == '' else info


    if item.infoLabels['tvdb_id']:
        ID = item.infoLabels['tvdb_id']
        dict_renumerate = {TAG_ID: ID}
        dict_series[title] = dict_renumerate
        # Trova la Stagione
        if any( word in title.lower() for word in ['specials', 'speciali'] ):
            heading = config.get_localized_string(70686) # <- Enter the number of the starting season (for specials)
            season = platformtools.dialog_numeric(0, heading, '0')
            dict_renumerate[TAG_SEASON] = season
        elif RepresentsInt(title.split()[-1]):
            heading = config.get_localized_string(70686) # <- Enter the number of the starting season (for season > 1)
            season = platformtools.dialog_numeric(0, heading, title.split()[-1])
            dict_renumerate[TAG_SEASON] = season
        else:
            heading = config.get_localized_string(70686) # <- Enter the number of the starting season (for season 1)
            season = platformtools.dialog_numeric(0, heading, '1')
            dict_renumerate[TAG_SEASON] = season


        mode = platformtools.dialog_yesno(config.get_localized_string(70687), config.get_localized_string(70688), nolabel=config.get_localized_string(30023), yeslabel=config.get_localized_string(30022))
        if mode == True:
            dict_renumerate[TAG_MODE] = False
            if dict_series[title].has_key(TAG_SPECIAL):
                specials = dict_renumerate[TAG_SPECIAL]
            else:
                specials = []
            jsontools.update_node(dict_series, item.channel, TAG_TVSHOW_RENUMERATE)[0]
            _list = []
            # channel = __import__('channels.' + item.channel, fromlist=["channels.%s" % item.channel])
            itemlist = find_episodes(item)
            for item in itemlist:
                Title = re.sub(r'\d+x\d+ - ', '', item.title)
                if item.action == 'findvideos':
                    _list.append(Title)

            selected = platformtools.dialog_multiselect(config.get_localized_string(70734), _list)
            # if len(selected) > 0:
            for select in selected:
                specials.append(int(scrapertoolsV2.find_single_match(_list[select],r'(\d+)')))
            dict_renumerate[TAG_SPECIAL] = specials

            # stop = False
            # while not stop:
            #     heading = config.get_localized_string(70718) + str(specials)
            #     special = platformtools.dialog_numeric(0, heading, '')
            #     if special:
            #         specials.append(int(special))
            #         dict_renumerate[TAG_SPECIAL] = specials
            #     else: stop = True
        dict_renumerate[TAG_MODE] = False

        dict_renumerate[TAG_TYPE] = 'auto'
        # Imposta la voce Episode
        dict_renumerate[TAG_EPISODE] = ''
        # Scrive nel json
        jsontools.update_node(dict_series, item.channel, TAG_TVSHOW_RENUMERATE)[0]
        xbmc.executebuiltin("Container.Refresh")

    else:
        message = config.get_localized_string(60444)
        heading = item.show.strip()
        platformtools.dialog_notification(heading, message)


def config_item(item, itemlist=[], typography='', active=False):
    log()
    # Configurazione Automatica, Tenta la numerazione Automatica degli episodi
    title = item.fulltitle

    dict_series = jsontools.get_node_from_file(item.channel, TAG_TVSHOW_RENUMERATE)
    try: ID = dict_series[item.show.rstrip()][TAG_ID]
    except: ID = ''

    # Pulizia del Titolo
    if any( word in title.lower() for word in ['specials', 'speciali']):
        item.show = re.sub(r'\sspecials|\sspeciali', '', item.show.lower())
        tvdb.find_and_set_infoLabels(item)
    elif not item.infoLabels['tvdb_id']:
            item.show = title.rstrip('123456789 ')
            tvdb.find_and_set_infoLabels(item)

    if not ID and active:
        if item.infoLabels['tvdb_id']:
            ID = item.infoLabels['tvdb_id']
            dict_renumerate = {TAG_ID: ID}
            dict_series[title] = dict_renumerate
            # Trova La Stagione
            if any( word in title.lower() for word in ['specials', 'speciali']):
                dict_renumerate[TAG_SEASON] = '0'
            elif RepresentsInt(title.split()[-1]):
                dict_renumerate[TAG_SEASON] = title.split()[-1]
            else: dict_renumerate[TAG_SEASON] = '1'
            dict_renumerate[TAG_EPISODE] = ''
            settings_node = jsontools.get_node_from_file(item.channel, 'settings')
            dict_renumerate[TAG_MODE] = settings_node['autorenumber_mode']
            jsontools.update_node(dict_series, item.channel, TAG_TVSHOW_RENUMERATE)[0]
            return renumber(itemlist, item, typography)
        else:
            return itemlist

    else:
        return renumber(itemlist, item, typography)


def renumber(itemlist, item='', typography=''):
    log()
    # dbg()
    # Carica Impostazioni
    if itemlist:
        settings_node = jsontools.get_node_from_file(itemlist[0].channel, 'settings')
    else:
        settings_node = {}
    try: dict_series = jsontools.get_node_from_file(itemlist[0].channel, TAG_TVSHOW_RENUMERATE)
    except: dict_series = {}
    log('CHANNEL', itemlist[0])

    # Seleziona la funzione Adatta, Menu Contestuale o Rinumerazione
    if item:
        item.channel = item.from_channel if item.from_channel else item.channel
        # Controlla se la Serie è già stata rinumerata
        TITLE = item.fulltitle.rstrip() if item.fulltitle else item.contentTitle
        log('dict', dict_series)
        log('TITLE ', TITLE)
        log('TITLE EXIST? ', TITLE in dict_series)
        log('HAS ID? ',dict_series[TITLE].has_key(TAG_ID))
        if inspect.stack()[2][3] == 'find_episodes':
            log('PRENDO ITEMLIST ',inspect.stack()[2][3])
            return itemlist
        
        elif dict_series.has_key(TITLE) and dict_series[TITLE].has_key(TAG_ID):
            ID = dict_series[TITLE][TAG_ID]
            EPISODE = dict_series[TITLE][TAG_EPISODE]

            if dict_series[TITLE].has_key(TAG_SEASON): SEASON = dict_series[TITLE][TAG_SEASON]
            else: SEASON = ''
            
            if dict_series[TITLE].has_key(TAG_MODE): MODE = dict_series[TITLE][TAG_MODE]
            else: MODE = False

            if dict_series[TITLE].has_key(TAG_TYPE):
                TYPE = dict_series[TITLE][TAG_TYPE]
            else:
                TYPE = 'auto'
                dict_series[TITLE][TAG_TYPE] = TYPE
                jsontools.update_node(dict_series, item.channel, TAG_TVSHOW_RENUMERATE)[0]

            renumeration(itemlist, item, typography, dict_series, ID, SEASON, EPISODE, MODE, TITLE, TYPE)

        else:
            # se non è stata rinumerata controlla se è attiva la rinumerazione automatica
            if 'autorenumber' not in settings_node:
                return itemlist
            if settings_node['autorenumber'] == True:
                config_item(item, itemlist, typography, True)

    else:
        for item in itemlist:
            TITLE = item.show.rstrip()
            if dict_series.has_key(TITLE) and dict_series[TITLE].has_key(TAG_ID):
                ID = dict_series[TITLE][TAG_ID]
                exist = True
            else:
                exist = False

            if item.contentType != 'movie':
                if item.context:
                    context2 = item.context
                    item.show = TITLE
                    item.context = context(exist) + context2
                else:
                    item.show = TITLE
                    item.context = context(exist)

def renumeration (itemlist, item, typography, dict_series, ID, SEASON, EPISODE, MODE, TITLE, TYPE):
    
    # Se ID è 0 salta la rinumerazione
    if ID == '0':
        return itemlist

    # Numerazione per gli Speciali
    elif SEASON == '0':
        EpisodeDict = {}
        for item in itemlist:
            if config.get_localized_string(30992) not in item.title:
                number = scrapertoolsV2.find_single_match(item.title, r'\d+')
                item.title = typo('0x' + number + ' - ', typography) + item.title


    # Usa la lista degli Episodi se esiste nel Json

    elif EPISODE:
        EpisodeDict = json.loads(base64.b64decode(EPISODE))

        # Controlla che la lista egli Episodi sia della stessa lunghezza di Itemlist
        if EpisodeDict == 'none':
            return error(itemlist)
        if TYPE == 'manual' and len(EpisodeDict) < len(itemlist): 
            EpisodeDict = manual_renumeration(item, True)
        if len(EpisodeDict) >= len(itemlist) and EpisodeDict.has_key(scrapertoolsV2.find_single_match(itemlist[0].title, r'\d+')):
            for item in itemlist:
                if config.get_localized_string(30992) not in item.title:
                    number = scrapertoolsV2.find_single_match(item.title, r'\d+')
                    number = int(number) # if number !='0': number.lstrip('0')
                    item.title = typo(EpisodeDict[str(number)] + ' - ', typography) + item.title
        else:
            make_list(itemlist, item, typography, dict_series, ID, SEASON, EPISODE, MODE, TITLE)

    else:
        make_list(itemlist, item, typography, dict_series, ID, SEASON, EPISODE, MODE, TITLE)

def make_list(itemlist, item, typography, dict_series, ID, SEASON, EPISODE, MODE, TITLE):
    log()
    exist = True
    item.infoLabels['tvdb_id'] = ID
    tvdb.set_infoLabels_item(item)
    FirstOfSeason= 0

    if EPISODE: EpisodeDict = json.loads(base64.b64decode(EPISODE))
    else: EpisodeDict = {}
    try: SPECIAL = dict_series[TITLE][TAG_SPECIAL]
    except: SPECIAL = []
    try: EpList = json.loads(base64.b64decode(dict_series[TITLE][TAG_EPLIST]))
    except: EpList = []
    try: Pages = dict_series[TITLE][TAG_CHECK]
    except: Pages = [1]

    # Ricava Informazioni da TVDB
    checkpages = []
    check = True
    Page = Pages[-1]

    while exist:
        if check:
            for page in Pages:
                data = tvdb.otvdb_global.get_list_episodes(ID,page)
                for episodes in data['data']:
                    if episodes['firstAired'] and [episodes['firstAired'], episodes['airedSeason'], episodes['airedEpisodeNumber']] not in EpList:
                        EpList.append([episodes['firstAired'], episodes['airedSeason'], episodes['airedEpisodeNumber']])
                    else:
                        if page not in checkpages:
                            checkpages.append(page)
        check = False

        data = tvdb.otvdb_global.get_list_episodes(ID,Page)
        if data:
            Page = Page + 1
            for episodes in data['data']:
                if episodes['firstAired'] and [episodes['firstAired'], episodes['airedSeason'], episodes['airedEpisodeNumber']] not in EpList:
                    EpList.append([episodes['firstAired'], episodes['airedSeason'], episodes['airedEpisodeNumber']])
        else:
            if page not in checkpages:
                checkpages.append(Page -1)
            exist = False

    EpList.sort()

    dict_series[TITLE][TAG_CHECK] = checkpages
    EpList = base64.b64encode(json.dumps(EpList))
    dict_series[TITLE][TAG_EPLIST] = EpList
    jsontools.update_node(dict_series, item.channel, TAG_TVSHOW_RENUMERATE)[0]

    # Crea Dizionari per la numerazione
    if EpList:
        EpList = json.loads(base64.b64decode(dict_series[TITLE][TAG_EPLIST]))
        specials = []
        regular = {}
        complete = {}
        allep = 1
        ep = 1
        specialep = 0
        for episode in EpList:
            complete[allep] = [str(episode[1]) + 'x' + str(episode[2]), episode[0]]
            if episode[1] == 0:
                specials.append(allep)
                specialep = specialep + 1
            else:
                regular[ep] = [str(episode[1]) + 'x' + str(episode[2]), str(episode[0]), allep - 1]
                ep = ep + 1
            allep = allep + 1

        # seleziona l'Episodio di partenza
        if int(SEASON) > 1:
            for numbers, data in regular.items():
                if data[0] == SEASON + 'x1':
                    FirstOfSeason = numbers - 1

        if MODE == True: SPECIAL = specials

        addiction = 0
        for item in itemlist:
            # Otiene Numerazione Episodi
            if config.get_localized_string(30992) not in item.title:
                episode = int(scrapertoolsV2.find_single_match(item.title, r'\d+'))
                number = episode + FirstOfSeason - addiction
                count = number + addiction
                # Crea Dizionario Episodi

                if episode == 0:
                    EpisodeDict[str(episode)] = str(complete[regular[FirstOfSeason+1][2]][0])
                elif addiction < len(SPECIAL):
                    if episode in SPECIAL:
                        try:
                            season = complete[regular[count][2]][0]
                            EpisodeDict[str(episode)] = str(complete[regular[count][2]][0]) if season.startswith( '0' ) else '0x' + platformtools.dialog_numeric(0, item.title + '?', '')

                        except:
                            EpisodeDict[str(episode)] = '0x' + platformtools.dialog_numeric(0, item.title + '?', '')
                        addiction = addiction + 1
                    elif number <= len(regular):
                        EpisodeDict[str(episode)] = str(regular[number][0])
                    else:
                        try: EpisodeDict[str(episode)] = str(complete[regular[number+2][2]][0])
                        except: EpisodeDict[str(episode)] = '0x0'
                elif number <= len(regular) and regular.has_key(number):
                    EpisodeDict[str(episode)] = str(regular[number][0])
                else:
                    try: EpisodeDict[str(episode)] = str(complete[regular[number+2][2]][0])
                    except: EpisodeDict[str(episode)] = '0x0'

                # Aggiunge numerazione agli Episodi

                item.title = typo(EpisodeDict[str(episode)] + ' - ', typography) + item.title

        # Scrive Dizionario Episodi sul json
        EpisodeDict = base64.b64encode(json.dumps(EpisodeDict))
        dict_series[TITLE][TAG_EPISODE] = EpisodeDict
        jsontools.update_node(dict_series, item.channel, TAG_TVSHOW_RENUMERATE)[0]

    else:
        heading = config.get_localized_string(70704)
        ID = platformtools.dialog_numeric(0, heading)
        dict_series[TITLE][TAG_ID] = ID
        jsontools.update_node(dict_series, item.channel, TAG_TVSHOW_RENUMERATE)[0]
        if ID == '0':
            return itemlist
        else:
            return make_list(itemlist, item, typography, dict_series, ID, SEASON, EPISODE, MODE, TITLE)

    # return itemlist



def RepresentsInt(s):
    # Controllo Numro Stagione
    log()
    try:
        int(s)
        return True
    except ValueError:
        return False

def error(itemlist):
    message = config.get_localized_string(70713)
    heading = itemlist[0].fulltitle.strip()
    platformtools.dialog_notification(heading, message)
    return itemlist

def check(item):
    try:
        dict_series = jsontools.get_node_from_file(item.channel, TAG_TVSHOW_RENUMERATE)
        TITLE = item.fulltitle.rstrip()
        dict_series[TITLE][TAG_ID]
        dict_series[TITLE][TAG_EPISODE]
        exist = True
    except:
        exist = False
    return exist

def find_episodes(item):
    log()
    ch = __import__('channels.' + item.channel, fromlist=["channels.%s" % item.channel])
    itemlist = ch.episodios(item)
    return itemlist