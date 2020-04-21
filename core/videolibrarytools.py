# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Common Library Tools
# ------------------------------------------------------------

#from builtins import str
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import errno
import math
import traceback
import re
import os

from core import filetools
from core import scraper
from core import scrapertools
from core.item import Item
from lib import generictools
from platformcode import config, logger
from platformcode import platformtools

FOLDER_MOVIES = config.get_setting("folder_movies")
FOLDER_TVSHOWS = config.get_setting("folder_tvshows")
VIDEOLIBRARY_PATH = config.get_videolibrary_path()
MOVIES_PATH = filetools.join(VIDEOLIBRARY_PATH, FOLDER_MOVIES)
TVSHOWS_PATH = filetools.join(VIDEOLIBRARY_PATH, FOLDER_TVSHOWS)

if not FOLDER_MOVIES or not FOLDER_TVSHOWS or not VIDEOLIBRARY_PATH \
        or not filetools.exists(MOVIES_PATH) or not filetools.exists(TVSHOWS_PATH):
    config.verify_directories_created()

addon_name = "plugin://plugin.video.%s/" % config.PLUGIN_NAME


def read_nfo(path_nfo, item=None):
    """
    Metodo para leer archivos nfo.
        Los arcivos nfo tienen la siguiente extructura: url_scraper | xml + item_json
        [url_scraper] y [xml] son opcionales, pero solo uno de ellos ha de existir siempre.
    @param path_nfo: ruta absoluta al archivo nfo
    @type path_nfo: str
    @param item: Si se pasa este parametro el item devuelto sera una copia de este con
        los valores de 'infoLabels', 'library_playcounts' y 'path' leidos del nfo
    @type: Item
    @return: Una tupla formada por la cabecera (head_nfo ='url_scraper'|'xml') y el objeto 'item_json'
    @rtype: tuple (str, Item)
    """
    head_nfo = ""
    it = None

    data = filetools.read(path_nfo)

    if data:
        head_nfo = data.splitlines()[0] + "\n"
        data = "\n".join(data.splitlines()[1:])

        it_nfo = Item().fromjson(data)

        if item:
            it = item.clone()
            it.infoLabels = it_nfo.infoLabels
            if 'library_playcounts' in it_nfo:
                it.library_playcounts = it_nfo.library_playcounts
            if it_nfo.path:
                it.path = it_nfo.path
        else:
            it = it_nfo

        if 'fanart' in it.infoLabels:
            it.fanart = it.infoLabels['fanart']

    return head_nfo, it


def save_movie(item, silent=False):
    """
    guarda en la libreria de peliculas el elemento item, con los valores que contiene.
    @type item: item
    @param item: elemento que se va a guardar.
    @rtype insertados: int
    @return:  el número de elementos insertados
    @rtype sobreescritos: int
    @return:  el número de elementos sobreescritos
    @rtype fallidos: int
    @return:  el número de elementos fallidos o -1 si ha fallado todo
    """
    logger.info()
    # logger.debug(item.tostring('\n'))
    insertados = 0
    sobreescritos = 0
    fallidos = 0
    path = ""

    # Itentamos obtener el titulo correcto:
    # 1. contentTitle: Este deberia ser el sitio correcto, ya que title suele contener "Añadir a la videoteca..."
    # 2. fulltitle
    # 3. title
    # if item.contentTitle: item.title = item.contentTitle
    # elif item.fulltitle: item.title = item.fulltitle

    if not item.contentTitle:
        # Colocamos el titulo correcto en su sitio para que scraper lo localize
        if item.fulltitle:
            item.contentTitle = item.fulltitle
        else:
            item.contentTitle = item.title

    # Si llegados a este punto no tenemos titulo, salimos
    if not item.contentTitle or not item.channel:
        logger.debug("contentTitle NOT FOUND")
        return 0, 0, -1  # Salimos sin guardar

    scraper_return = scraper.find_and_set_infoLabels(item)

    # Llegados a este punto podemos tener:
    #  scraper_return = True: Un item con infoLabels con la información actualizada de la peli
    #  scraper_return = False: Un item sin información de la peli (se ha dado a cancelar en la ventana)
    #  item.infoLabels['code'] == "" : No se ha encontrado el identificador de IMDB necesario para continuar, salimos
    if not scraper_return or not item.infoLabels['code']:
        # TODO de momento si no hay resultado no añadimos nada,
        # aunq podriamos abrir un cuadro para introducir el identificador/nombre a mano
        logger.debug("NOT FOUND IN SCRAPER OR DO NOT HAVE code")
        return 0, 0, -1

    _id = item.infoLabels['code'][0]

    # progress dialog
    if not silent:
        p_dialog = platformtools.dialog_progress(config.get_localized_string(20000), config.get_localized_string(60062))

    if config.get_setting("original_title_folder", "videolibrary") and item.infoLabels['originaltitle']:
        base_name = item.infoLabels['originaltitle']
    else:
        base_name = item.contentTitle

    if not PY3:
        base_name = unicode(filetools.validate_path(base_name.replace('/', '-')), "utf8").encode("utf8")
    else:
        base_name = filetools.validate_path(base_name.replace('/', '-'))

    if config.get_setting("lowerize_title", "videolibrary"):
        base_name = base_name.lower()

    for raiz, subcarpetas, ficheros in filetools.walk(MOVIES_PATH):
        for c in subcarpetas:
            code = scrapertools.find_single_match(c, '\[(.*?)\]')
            if code and code in item.infoLabels['code']:
                path = filetools.join(raiz, c)
                _id = code
                break

    if not path:
        # Crear carpeta
        path = filetools.join(MOVIES_PATH, ("%s [%s]" % (base_name, _id)).strip())
        logger.info("Creating movie directory:" + path)
        if not filetools.mkdir(path):
            logger.debug("Could not create directory")
            return 0, 0, -1

    nfo_path = filetools.join(path, "%s [%s].nfo" % (base_name, _id))
    strm_path = filetools.join(path, "%s.strm" % base_name)
    json_path = filetools.join(path, ("%s [%s].json" % (base_name, item.channel.lower())))

    nfo_exists = filetools.exists(nfo_path)
    strm_exists = filetools.exists(strm_path)
    json_exists = filetools.exists(json_path)

    if not nfo_exists:
        # Creamos .nfo si no existe
        logger.info("Creating .nfo: " + nfo_path)
        head_nfo = scraper.get_nfo(item)

        item_nfo = Item(title=item.contentTitle, channel="videolibrary", action='findvideos',
                        library_playcounts={"%s [%s]" % (base_name, _id): 0}, infoLabels=item.infoLabels,
                        library_urls={})

    else:
        # Si existe .nfo, pero estamos añadiendo un nuevo canal lo abrimos
        head_nfo, item_nfo = read_nfo(nfo_path)

    if not strm_exists:
        # Crear base_name.strm si no existe
        item_strm = Item(channel='videolibrary', action='play_from_library',
                         strm_path=strm_path.replace(MOVIES_PATH, ""), contentType='movie',
                         contentTitle=item.contentTitle)
        strm_exists = filetools.write(strm_path, '%s?%s' % (addon_name, item_strm.tourl()))
        item_nfo.strm_path = strm_path.replace(MOVIES_PATH, "")

    # Solo si existen item_nfo y .strm continuamos
    if item_nfo and strm_exists:

        if json_exists:
            logger.info("The file exists. Is overwritten")
            sobreescritos += 1
        else:
            insertados += 1

        # Si se ha marcado la opción de url de emergencia, se añade ésta a la película después de haber ejecutado Findvideos del canal
        try:
            headers = {}
            if item.headers:
                headers = item.headers
            channel = generictools.verify_channel(item.channel)
            if config.get_setting("emergency_urls", channel) in [1, 3]:
                item = emergency_urls(item, None, json_path, headers=headers)
                if item_nfo.emergency_urls and not isinstance(item_nfo.emergency_urls, dict):
                    del item_nfo.emergency_urls
                if not item_nfo.emergency_urls:
                    item_nfo.emergency_urls = dict()
                item_nfo.emergency_urls.update({item.channel: True})
        except:
            logger.error("Unable to save %s emergency urls in the video library" % item.contentTitle)
            logger.error(traceback.format_exc())

        if filetools.write(json_path, item.tojson()):
            if not silent: p_dialog.update(100, config.get_localized_string(60062), item.contentTitle)
            item_nfo.library_urls[item.channel] = item.url

            if filetools.write(nfo_path, head_nfo + item_nfo.tojson()):
                #logger.info("FOLDER_MOVIES : %s" % FOLDER_MOVIES)
                # actualizamos la videoteca de Kodi con la pelicula
                if config.is_xbmc() and config.get_setting("videolibrary_kodi") and not silent:
                    from platformcode import xbmc_videolibrary
                    xbmc_videolibrary.update()

                if not silent: p_dialog.close()
                return insertados, sobreescritos, fallidos

    # Si llegamos a este punto es por q algo ha fallado
    logger.error("Could not save %s in the video library" % item.contentTitle)
    if not silent:
        p_dialog.update(100, config.get_localized_string(60063), item.contentTitle)
        p_dialog.close()
    return 0, 0, -1

def update_renumber_options(item, head_nfo, path):
    from core import jsontools
    # from core.support import dbg;dbg()
    tvshow_path = filetools.join(path, 'tvshow.nfo')
    if filetools.isfile(tvshow_path) and item.channel_prefs:
        for channel in item.channel_prefs:
            filename = filetools.join(config.get_data_path(), "settings_channels", channel + '_data.json')

            json_file = jsontools.load(filetools.read(filename))
            if 'TVSHOW_AUTORENUMBER' in json_file:
                json = json_file['TVSHOW_AUTORENUMBER']
                if item.fulltitle in json:
                    item.channel_prefs[channel]['TVSHOW_AUTORENUMBER'] = json[item.fulltitle]
                    logger.info('UPDATED=\n' + str(item.channel_prefs))
                    filetools.write(tvshow_path, head_nfo + item.tojson())

def add_renumber_options(item, head_nfo, path):
    from core import jsontools
    # from core.support import dbg;dbg()
    ret = None
    filename = filetools.join(config.get_data_path(), "settings_channels", item.channel + '_data.json')
    json_file = jsontools.load(filetools.read(filename))
    if 'TVSHOW_AUTORENUMBER' in json_file:
        json = json_file['TVSHOW_AUTORENUMBER']
        if item.fulltitle in json:
            ret = json[item.fulltitle]
    return ret

def check_renumber_options(item):
    from specials.autorenumber import load, write
    for key in item.channel_prefs:
        if 'TVSHOW_AUTORENUMBER' in item.channel_prefs[key]:
            item.channel = key
            json = load(item)
            if not json or item.fulltitle not in json:
                json[item.fulltitle] = item.channel_prefs[key]['TVSHOW_AUTORENUMBER']
                write(item, json)

    # head_nfo, tvshow_item = read_nfo(filetools.join(item.context[0]['nfo']))
    # if tvshow_item['channel_prefs'][item.fullti]


def filter_list(episodelist, action=None, path=None):
    # if path: path = path.decode('utf8')
    # import xbmc
    # if xbmc.getCondVisibility('system.platform.windows') > 0: path = path.replace('smb:','').replace('/','\\')
    channel_prefs = {}
    lang_sel = quality_sel = show_title = channel =''
    # from core.support import dbg;dbg()
    if action:
        tvshow_path = filetools.join(path, "tvshow.nfo")
        head_nfo, tvshow_item = read_nfo(tvshow_path)
        channel = episodelist[0].channel
        show_title = tvshow_item.infoLabels['tvshowtitle']
        if not tvshow_item.channel_prefs:
            tvshow_item.channel_prefs={channel:{}}
            list_item = filetools.listdir(path)
            for File in list_item:
                if (File.endswith('.strm') or File.endswith('.json') or File.endswith('.nfo')):
                    filetools.remove(filetools.join(path, File))
        if channel not in tvshow_item.channel_prefs:
            tvshow_item.channel_prefs[channel] = {}

        channel_prefs = tvshow_item.channel_prefs[channel]

        renumber = add_renumber_options(episodelist[0], head_nfo, tvshow_path)
        if renumber:
            channel_prefs['TVSHOW_AUTORENUMBER'] = renumber

        if action == 'get_seasons':
            if 'favourite_language' not in channel_prefs:
                channel_prefs['favourite_language'] = ''
            if 'favourite_quality' not in channel_prefs:
                channel_prefs['favourite_quality'] = ''
            if channel_prefs['favourite_language']:
                lang_sel = channel_prefs['favourite_language']
            if channel_prefs['favourite_quality']:
                quality_sel = channel_prefs['favourite_quality']
    # if Download
        if not show_title: show_title = episodelist[0].fulltitle
        if not channel: channel= episodelist[0].channel
    # SELECT EISODE BY LANG AND QUALITY
    quality_dict = {'N/A': ['n/a'],
                    'BLURAY': ['br', 'bluray'],
                    'FULLHD': ['fullhd', 'fullhd 1080', 'fullhd 1080p', 'full hd', 'full hd 1080', 'full hd 1080p', 'hd1080', 'hd1080p', 'hd 1080', 'hd 1080p', '1080', '1080p'],
                    'HD': ['hd', 'hd720', 'hd720p', 'hd 720', 'hd 720p', '720', '720p', 'hdtv'],
                    '480P': ['sd', '480p', '480'],
                    '360P': ['360p', '360'],
                    '240P': ['240p', '240'],
                    'MAX':['MAX']}
    quality_order = ['N/A', '240P', '360P','480P', 'HD', 'FULLHD', 'BLURAY', 'MAX']


    lang_list = []
    sub_list = []
    quality_list = ['MAX']

    # Make Language List
    for episode in episodelist:
        if type(episode.contentLanguage) == list and episode.contentLanguage not in lang_list:
           #lang_list = episode.contentLanguage
           pass
        else:
            if episode.contentLanguage and episode.contentLanguage not in lang_list:
                # Make list of subtitled languages
                if 'sub' in episode.contentLanguage.lower():
                    sub = re.sub('Sub-','', episode.contentLanguage)
                    if sub not in sub_list: sub_list.append(sub)
                else:
                    lang_list.append(episode.contentLanguage)
    # add to Language List subtitled languages
    if sub_list:
        for sub in sub_list:
            if sub in lang_list:
                lang_list.insert(lang_list.index(sub) + 1, 'Sub-' + sub)
                lang_list.insert(lang_list.index(sub) + 2, sub + ' + Sub-' + sub)
            else:
                lang_list.append('Sub-' + sub)

    # Make Quality List
    for episode in episodelist:
        for name, var in quality_dict.items():
            if not episode.quality and 'N/A' not in quality_list:
                quality_list.append('N/A')
            if episode.quality.lower() in var and name not in quality_list:
                quality_list.append(name)
    quality_list = sorted(quality_list, key=lambda x:quality_order.index(x))

    # if more than one language
    if len(lang_list) > 1:
        selection = lang_list.index(lang_sel) if lang_sel else platformtools.dialog_select(config.get_localized_string(70725) % (show_title, channel),lang_list)
        if action: lang_sel = channel_prefs['favourite_language'] = lang_list[selection]
        langs = lang_list[selection].split(' + ')

        ep_list = []
        count = 0
        stop = False
        while not stop:
            for episode in episodelist:
                title = scrapertools.find_single_match(episode.title, '(\d+x\d+)')
                if not any(title in word for word in ep_list) and episode.contentLanguage == langs[count]:
                    ep_list.append(episode.title)
            if count < len(langs)-1: count += 1
            else: stop = True
        it = []
        for episode in episodelist:
            if episode.title in ep_list:
                it.append(episode)
        episodelist = it

    else: channel_prefs['favourite_language'] = ''

    # if more than one quality
    if len(quality_list) > 2:
        if config.get_setting('videolibrary_max_quality'): selection = favourite_quality_selection = len(quality_list)-1
        else: selection = favourite_quality_selection = quality_list.index(quality_sel) if quality_sel else platformtools.dialog_select(config.get_localized_string(70726) % (show_title, channel) ,quality_list)

        ep_list = []
        stop = False
        while not stop:
            for episode in episodelist:
                title = scrapertools.find_single_match(episode.title, '(\d+x\d+)')
                if not any(title in word for word in ep_list) and episode.quality.lower() in quality_dict[quality_list[selection]]:
                    ep_list.append(episode.title)
            if selection != 0: selection = selection - 1
            else: stop = True
            if quality_list[selection] == 'N/A':
                for episode in episodelist:
                    title = scrapertools.find_single_match(episode.title, '(\d+x\d+)')
                    if not any(title in word for word in ep_list):
                        ep_list.append(episode.title)

        it = []
        for episode in episodelist:
            if episode.title in ep_list:
                if action: channel_prefs['favourite_quality'] = quality_list[favourite_quality_selection]
                it.append(episode)
        episodelist = it

    else:channel_prefs['favourite_quality'] = ''

    if action: filetools.write(tvshow_path, head_nfo + tvshow_item.tojson())

    return episodelist

def save_tvshow(item, episodelist, silent=False):
    """
    guarda en la libreria de series la serie con todos los capitulos incluidos en la lista episodelist
    @type item: item
    @param item: item que representa la serie a guardar
    @type episodelist: list
    @param episodelist: listado de items que representan los episodios que se van a guardar.
    @rtype insertados: int
    @return:  el número de episodios insertados
    @rtype sobreescritos: int
    @return:  el número de episodios sobreescritos
    @rtype fallidos: int
    @return:  el número de episodios fallidos o -1 si ha fallado toda la serie
    @rtype path: str
    @return:  directorio serie
    """
    logger.info()
    # logger.debug(item.tostring('\n'))
    path = ""

    # Si llegados a este punto no tenemos titulo o code, salimos
    if not (item.contentSerieName or item.infoLabels['code']) or not item.channel:
        logger.debug("NOT FOUND contentSerieName or code")
        return 0, 0, -1, path  # Salimos sin guardar

    scraper_return = scraper.find_and_set_infoLabels(item)
    # Llegados a este punto podemos tener:
    #  scraper_return = True: Un item con infoLabels con la información actualizada de la serie
    #  scraper_return = False: Un item sin información de la peli (se ha dado a cancelar en la ventana)
    #  item.infoLabels['code'] == "" : No se ha encontrado el identificador de IMDB necesario para continuar, salimos
    if not scraper_return or not item.infoLabels['code']:
        # TODO de momento si no hay resultado no añadimos nada,
        # aunq podriamos abrir un cuadro para introducir el identificador/nombre a mano
        logger.debug("NOT FOUND IN SCRAPER OR DO NOT HAVE code")
        return 0, 0, -1, path

    _id = item.infoLabels['code'][0]
    if not item.infoLabels['code'][0] or item.infoLabels['code'][0] == 'None': 
        if item.infoLabels['code'][1] and item.infoLabels['code'][1] != 'None':
            _id = item.infoLabels['code'][1]
        elif item.infoLabels['code'][2] and item.infoLabels['code'][2] != 'None':
            _id = item.infoLabels['code'][2]
        else:
            logger.error("NO ENCONTRADO EN SCRAPER O NO TIENE code: " + item.url 
                        + ' / ' + item.infoLabels['code'])
            return 0, 0, -1, path

    if config.get_setting("original_title_folder", "videolibrary") and item.infoLabels['originaltitle']:
        base_name = item.infoLabels['originaltitle']
    elif item.infoLabels['tvshowtitle']:
        base_name = item.infoLabels['tvshowtitle']
    elif item.infoLabels['title']:
        base_name = item.infoLabels['title']
    else:
        base_name = item.contentSerieName

    if not PY3:
        base_name = unicode(filetools.validate_path(base_name.replace('/', '-')), "utf8").encode("utf8")
    else:
        base_name = filetools.validate_path(base_name.replace('/', '-'))

    if config.get_setting("lowerize_title", "videolibrary"):
        base_name = base_name.lower()

    for raiz, subcarpetas, ficheros in filetools.walk(TVSHOWS_PATH):
        for c in subcarpetas:
            code = scrapertools.find_single_match(c, '\[(.*?)\]')
            if code and code != 'None' and code in item.infoLabels['code']:
                path = filetools.join(raiz, c)
                _id = code
                break

    if not path:
        path = filetools.join(TVSHOWS_PATH, ("%s [%s]" % (base_name, _id)).strip())
        logger.info("Creating series directory: " + path)
        try:
            filetools.mkdir(path)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

    tvshow_path = filetools.join(path, "tvshow.nfo")
    if not filetools.exists(tvshow_path):
        # Creamos tvshow.nfo, si no existe, con la head_nfo, info de la serie y marcas de episodios vistos
        logger.info("Creating tvshow.nfo: " + tvshow_path)
        head_nfo = scraper.get_nfo(item)
        item.infoLabels['mediatype'] = "tvshow"
        item.infoLabels['title'] = item.contentSerieName
        item_tvshow = Item(title=item.contentSerieName, channel="videolibrary", action="get_seasons",
                           fanart=item.infoLabels['fanart'], thumbnail=item.infoLabels['thumbnail'],
                           infoLabels=item.infoLabels, path=path.replace(TVSHOWS_PATH, ""), fulltitle=item.fulltitle)
        item_tvshow.library_playcounts = {}
        item_tvshow.library_urls = {item.channel: item.url}

    else:
        # Si existe tvshow.nfo, pero estamos añadiendo un nuevo canal actualizamos el listado de urls
        head_nfo, item_tvshow = read_nfo(tvshow_path)
        item_tvshow.fulltitle = item.fulltitle
        item_tvshow.channel = "videolibrary"
        item_tvshow.action = "get_seasons"
        item_tvshow.library_urls[item.channel] = item.url

    # FILTERTOOLS
    # si el canal tiene filtro de idiomas, añadimos el canal y el show
    if episodelist and "list_language" in episodelist[0]:
        # si ya hemos añadido un canal previamente con filtro, añadimos o actualizamos el canal y show
        if "library_filter_show" in item_tvshow:
            if item.title_from_channel:
                item_tvshow.library_filter_show[item.channel] = item.title_from_channel
            else:
                item_tvshow.library_filter_show[item.channel] = item.show
        # no habia ningún canal con filtro y lo generamos por primera vez
        else:
            if item.title_from_channel:
                item_tvshow.library_filter_show = {item.channel: item.title_from_channel}
            else:
                item_tvshow.library_filter_show = {item.channel: item.show}

    if item.channel != "downloads":
        item_tvshow.active = 1  # para que se actualice a diario cuando se llame a service

    filetools.write(tvshow_path, head_nfo + item_tvshow.tojson())

    if not episodelist:
        # La lista de episodios esta vacia
        return 0, 0, 0, path

    # Guardar los episodios
    '''import time
    start_time = time.time()'''
    insertados, sobreescritos, fallidos = save_episodes(path, episodelist, item, silent=silent)
    '''msg = "Insertados: %d | Sobreescritos: %d | Fallidos: %d | Tiempo: %2.2f segundos" % \
          (insertados, sobreescritos, fallidos, time.time() - start_time)
    logger.debug(msg)'''

    return insertados, sobreescritos, fallidos, path


def save_episodes(path, episodelist, serie, silent=False, overwrite=True):
    """
    guarda en la ruta indicada todos los capitulos incluidos en la lista episodelist
    @type path: str
    @param path: ruta donde guardar los episodios
    @type episodelist: list
    @param episodelist: listado de items que representan los episodios que se van a guardar.
    @type serie: item
    @param serie: serie de la que se van a guardar los episodios
    @type silent: bool
    @param silent: establece si se muestra la notificación
    @param overwrite: permite sobreescribir los ficheros existentes
    @type overwrite: bool
    @rtype insertados: int
    @return:  el número de episodios insertados
    @rtype sobreescritos: int
    @return:  el número de episodios sobreescritos
    @rtype fallidos: int
    @return:  el número de episodios fallidos
    """
    logger.info()
    episodelist = filter_list(episodelist, serie.action, path)
    # No hay lista de episodios, no hay nada que guardar
    if not len(episodelist):
        logger.info("There is no episode list, we go out without creating strm")
        return 0, 0, 0

    insertados = 0
    sobreescritos = 0
    fallidos = 0
    news_in_playcounts = {}
    # Listamos todos los ficheros de la serie, asi evitamos tener que comprobar si existe uno por uno
    raiz, carpetas_series, ficheros = next(filetools.walk(path))
    ficheros = [filetools.join(path, f) for f in ficheros]

    # Silent es para no mostrar progreso (para service)
    if not silent:
        # progress dialog
        p_dialog = platformtools.dialog_progress(config.get_localized_string(20000), config.get_localized_string(60064))
        p_dialog.update(0, config.get_localized_string(60065))

    channel_alt = generictools.verify_channel(serie.channel)            #Preparamos para añadir las urls de emergencia
    emergency_urls_stat = config.get_setting("emergency_urls", channel_alt)         #El canal quiere urls de emergencia?
    emergency_urls_succ = False
    try: channel = __import__('specials.%s' % channel_alt, fromlist=["specials.%s" % channel_alt])
    except: channel = __import__('channels.%s' % channel_alt, fromlist=["channels.%s" % channel_alt])
    if serie.torrent_caching_fail:                              #Si el proceso de conversión ha fallado, no se cachean
        emergency_urls_stat = 0
        del serie.torrent_caching_fail

    new_episodelist = []
    # Obtenemos el numero de temporada y episodio y descartamos los q no lo sean

    for e in episodelist:
        headers = {}
        if e.headers:
            headers = e.headers

        try:
            season_episode = scrapertools.get_season_and_episode(e.title)

            # Si se ha marcado la opción de url de emergencia, se añade ésta a cada episodio después de haber ejecutado Findvideos del canal
            if e.emergency_urls and isinstance(e.emergency_urls, dict): del e.emergency_urls    #Borramos trazas anteriores
            json_path = filetools.join(path, ("%s [%s].json" % (season_episode, e.channel)).lower())    #Path del .json del episodio
            if emergency_urls_stat == 1 and not e.emergency_urls and e.contentType == 'episode':     #Guardamos urls de emergencia?
                if not silent:
                    p_dialog.update(0, 'Cacheando enlaces y archivos .torrent...', e.title)     #progress dialog
                if json_path in ficheros:                                   #Si existe el .json sacamos de ahí las urls
                    if overwrite:                                           #pero solo si se se sobrescriben los .json
                        json_epi = Item().fromjson(filetools.read(json_path))                   #Leemos el .json
                        if json_epi.emergency_urls:                         #si existen las urls de emergencia...
                            e.emergency_urls = json_epi.emergency_urls      #... las copiamos
                        else:                                               #y si no...
                            e = emergency_urls(e, channel, json_path, headers=headers)  #... las generamos
                else:
                    e = emergency_urls(e, channel, json_path, headers=headers)  #Si el episodio no existe, generamos las urls
                if e.emergency_urls:                                        #Si ya tenemos urls...
                    emergency_urls_succ = True                              #... es un éxito y vamos a marcar el .nfo
            elif emergency_urls_stat == 2 and e.contentType == 'episode':   #Borramos urls de emergencia?
                if e.emergency_urls: del e.emergency_urls
                emergency_urls_succ = True                                  #... es un éxito y vamos a marcar el .nfo
            elif emergency_urls_stat == 3 and e.contentType == 'episode':   #Actualizamos urls de emergencia?
                if not silent:
                    p_dialog.update(0, 'Cacheando enlaces y archivos .torrent...', e.title)     #progress dialog
                e = emergency_urls(e, channel, json_path, headers=headers)  #generamos las urls
                if e.emergency_urls:                                        #Si ya tenemos urls...
                    emergency_urls_succ = True                              #... es un éxito y vamos a marcar el .nfo

            if not e.infoLabels["tmdb_id"] or (serie.infoLabels["tmdb_id"] and e.infoLabels["tmdb_id"] != serie.infoLabels["tmdb_id"]):                                                    #en series multicanal, prevalece el infolabels...
                e.infoLabels = serie.infoLabels                             #... del canal actual y no el del original
            e.contentSeason, e.contentEpisodeNumber = season_episode.split("x")
            if e.videolibray_emergency_urls:
                del e.videolibray_emergency_urls
            if e.channel_redir:
                del e.channel_redir                                         #... y se borran las marcas de redirecciones
            new_episodelist.append(e)
        except:
            if e.contentType == 'episode':
                logger.error("Unable to save %s emergency urls in the video library" % e.contentTitle)
            continue

    # No hay lista de episodios, no hay nada que guardar
    if not len(new_episodelist):
        logger.info("There is no episode list, we go out without creating strm")
        return 0, 0, 0

    # fix float porque la division se hace mal en python 2.x
    try:
        t = float(100) / len(new_episodelist)
    except:
        t = 0

    local_episodelist = get_local_content(path)

    last_season_episode = ''
    for i, e in enumerate(scraper.sort_episode_list(new_episodelist)):
        if not silent:
            p_dialog.update(int(math.ceil((i + 1) * t)), config.get_localized_string(60064), e.title)

        high_sea = e.contentSeason
        high_epi = e.contentEpisodeNumber
        if scrapertools.find_single_match(e.title, '[a|A][l|L]\s*(\d+)'):
            high_epi = int(scrapertools.find_single_match(e.title, 'al\s*(\d+)'))
        max_sea = e.infoLabels["number_of_seasons"]
        max_epi = 0
        if e.infoLabels["number_of_seasons"] and (e.infoLabels["temporada_num_episodios"] or e.infoLabels["number_of_seasons"] == 1):
            if e.infoLabels["number_of_seasons"] == 1 and e.infoLabels["number_of_episodes"]:
                max_epi = e.infoLabels["number_of_episodes"]
            else:
                max_epi = e.infoLabels["temporada_num_episodios"]

        season_episode = "%sx%s" % (e.contentSeason, str(e.contentEpisodeNumber).zfill(2))
        strm_path = filetools.join(path, "%s.strm" % season_episode)
        nfo_path = filetools.join(path, "%s.nfo" % season_episode)
        json_path = filetools.join(path, ("%s [%s].json" % (season_episode, e.channel)).lower())

        if season_episode in local_episodelist:
            logger.info('Skipped: Serie ' + serie.contentSerieName + ' ' + season_episode + ' available as local content')
            continue
        strm_exists = strm_path in ficheros
        nfo_exists = nfo_path in ficheros
        json_exists = json_path in ficheros

        if not strm_exists:
            # Si no existe season_episode.strm añadirlo
            item_strm = Item(action='play_from_library', channel='videolibrary',
                             strm_path=strm_path.replace(TVSHOWS_PATH, ""), infoLabels={})
            item_strm.contentSeason = e.contentSeason
            item_strm.contentEpisodeNumber = e.contentEpisodeNumber
            item_strm.contentType = e.contentType
            item_strm.contentTitle = season_episode

            # FILTERTOOLS
            if item_strm.list_language:
                # si tvshow.nfo tiene filtro se le pasa al item_strm que se va a generar
                if "library_filter_show" in serie:
                    item_strm.library_filter_show = serie.library_filter_show

                if item_strm.library_filter_show == "":
                    logger.error("There was an error getting the name of the series to filter")

            # logger.debug("item_strm" + item_strm.tostring('\n'))
            # logger.debug("serie " + serie.tostring('\n'))
            strm_exists = filetools.write(strm_path, '%s?%s' % (addon_name, item_strm.tourl()))

        item_nfo = None
        if not nfo_exists and e.infoLabels["code"]:
            # Si no existe season_episode.nfo añadirlo
            scraper.find_and_set_infoLabels(e)
            head_nfo = scraper.get_nfo(e)

            item_nfo = e.clone(channel="videolibrary", url="", action='findvideos',
                               strm_path=strm_path.replace(TVSHOWS_PATH, ""))
            if item_nfo.emergency_urls:
                del item_nfo.emergency_urls                     #Solo se mantiene en el .json del episodio

            nfo_exists = filetools.write(nfo_path, head_nfo + item_nfo.tojson())

        # Solo si existen season_episode.nfo y season_episode.strm continuamos
        if nfo_exists and strm_exists:
            if not json_exists or overwrite:
                # Obtenemos infoLabel del episodio
                if not item_nfo:
                    head_nfo, item_nfo = read_nfo(nfo_path)

                # En series multicanal, prevalece el infolabels del canal actual y no el del original
                if not e.infoLabels["tmdb_id"] or (item_nfo.infoLabels["tmdb_id"] \
                            and e.infoLabels["tmdb_id"] != item_nfo.infoLabels["tmdb_id"]): 
                    e.infoLabels = item_nfo.infoLabels

                if filetools.write(json_path, e.tojson()):
                    if not json_exists:
                        logger.info("Inserted: %s" % json_path)
                        insertados += 1
                        # Marcamos episodio como no visto
                        news_in_playcounts[season_episode] = 0
                        # Marcamos la temporada como no vista
                        news_in_playcounts["season %s" % e.contentSeason] = 0
                        # Marcamos la serie como no vista
                        # logger.debug("serie " + serie.tostring('\n'))
                        news_in_playcounts[serie.contentSerieName] = 0

                    else:
                        logger.info("Overwritten: %s" % json_path)
                        sobreescritos += 1
                else:
                    logger.info("Failed: %s" % json_path)
                    fallidos += 1

        else:
            logger.info("Failed: %s" % json_path)
            fallidos += 1

        if not silent and p_dialog.iscanceled():
            break

    #logger.debug('high_sea x high_epi: %sx%s' % (str(high_sea), str(high_epi)))
    #logger.debug('max_sea x max_epi: %sx%s' % (str(max_sea), str(max_epi)))
    if not silent:
        p_dialog.close()

    if news_in_playcounts or emergency_urls_succ or serie.infoLabels["status"] == "Ended" or serie.infoLabels["status"] == "Canceled":
        # Si hay nuevos episodios los marcamos como no vistos en tvshow.nfo ...
        tvshow_path = filetools.join(path, "tvshow.nfo")
        try:
            import datetime
            head_nfo, tvshow_item = read_nfo(tvshow_path)
            tvshow_item.library_playcounts.update(news_in_playcounts)

            #Si la operación de insertar/borrar urls de emergencia en los .jsons de los episodios ha tenido éxito, se marca el .nfo
            if emergency_urls_succ:
                if tvshow_item.emergency_urls and not isinstance(tvshow_item.emergency_urls, dict):
                    del tvshow_item.emergency_urls
                if emergency_urls_stat in [1, 3]:                               #Operación de guardar/actualizar enlaces
                    if not tvshow_item.emergency_urls:
                        tvshow_item.emergency_urls = dict()
                    if tvshow_item.library_urls.get(serie.channel, False):
                        tvshow_item.emergency_urls.update({serie.channel: True})
                elif emergency_urls_stat == 2:                                  #Operación de Borrar enlaces
                    if tvshow_item.emergency_urls and tvshow_item.emergency_urls.get(serie.channel, False):
                        tvshow_item.emergency_urls.pop(serie.channel, None)     #borramos la entrada del .nfo

            if tvshow_item.active == 30:
                tvshow_item.active = 1
            if tvshow_item.infoLabels["tmdb_id"] == serie.infoLabels["tmdb_id"]:
                tvshow_item.infoLabels = serie.infoLabels
                tvshow_item.infoLabels["title"] = tvshow_item.infoLabels["tvshowtitle"] 

            if max_sea == high_sea and max_epi == high_epi and (tvshow_item.infoLabels["status"] == "Ended" 
                            or tvshow_item.infoLabels["status"] == "Canceled") and insertados == 0 and fallidos == 0:
                tvshow_item.active = 0                                          # ... no la actualizaremos más
                logger.debug("%s [%s]: serie 'Terminada' o 'Cancelada'.  Se desactiva la actualización periódica" % \
                            (serie.contentSerieName, serie.channel))

            update_last = datetime.date.today()
            tvshow_item.update_last = update_last.strftime('%Y-%m-%d')
            update_next = datetime.date.today() + datetime.timedelta(days=int(tvshow_item.active))
            tvshow_item.update_next = update_next.strftime('%Y-%m-%d')

            filetools.write(tvshow_path, head_nfo + tvshow_item.tojson())
        except:
            logger.error("Error updating tvshow.nfo")
            logger.error("Unable to save %s emergency urls in the video library" % tvshow_item.contentSerieName)
            logger.error(traceback.format_exc())
            fallidos = -1
        else:
            # ... si ha sido correcto actualizamos la videoteca de Kodi
            if config.is_xbmc() and config.get_setting("videolibrary_kodi") and not silent:
                from platformcode import xbmc_videolibrary
                xbmc_videolibrary.update()

    if fallidos == len(episodelist):
        fallidos = -1

    logger.debug("%s [%s]: inserted= %s, overwritten= %s, failed= %s" %
                 (serie.contentSerieName, serie.channel, insertados, sobreescritos, fallidos))
    return insertados, sobreescritos, fallidos


def get_local_content(path):
    logger.info()

    local_episodelist = []
    for root, folders, files in filetools.walk(path):
        for file in files:
            season_episode = scrapertools.get_season_and_episode(file)
            if season_episode == "" or filetools.exists(filetools.join(path, "%s.strm" % season_episode)):
                continue
            local_episodelist.append(season_episode)
    local_episodelist = sorted(set(local_episodelist))

    return local_episodelist


def add_movie(item):
    """
        guarda una pelicula en la libreria de cine. La pelicula puede ser un enlace dentro de un canal o un video
        descargado previamente.

        Para añadir episodios descargados en local, el item debe tener exclusivamente:
            - contentTitle: titulo de la pelicula
            - title: titulo a mostrar junto al listado de enlaces -findvideos- ("Reproducir video local HD")
            - infoLabels["tmdb_id"] o infoLabels["imdb_id"]
            - contentType == "movie"
            - channel = "downloads"
            - url : ruta local al video

        @type item: item
        @param item: elemento que se va a guardar.
    """
    logger.info()

    #Para desambiguar títulos, se provoca que TMDB pregunte por el título realmente deseado
    #El usuario puede seleccionar el título entre los ofrecidos en la primera pantalla
    #o puede cancelar e introducir un nuevo título en la segunda pantalla
    #Si lo hace en "Introducir otro nombre", TMDB buscará automáticamente el nuevo título
    #Si lo hace en "Completar Información", cambia parcialmente al nuevo título, pero no busca en TMDB.  Hay que hacerlo
    #Si se cancela la segunda pantalla, la variable "scraper_return" estará en False.  El usuario no quiere seguir

    item = generictools.update_title(item) #Llamamos al método que actualiza el título con tmdb.find_and_set_infoLabels
    #if item.tmdb_stat:
    #    del item.tmdb_stat          #Limpiamos el status para que no se grabe en la Videoteca

    new_item = item.clone(action="findvideos")
    insertados, sobreescritos, fallidos = save_movie(new_item)

    if fallidos == 0:
        platformtools.dialog_ok(config.get_localized_string(30131),
                                config.get_localized_string(30135) % new_item.contentTitle)  # 'se ha añadido a la videoteca'
    else:
        platformtools.dialog_ok(config.get_localized_string(30131),
                                config.get_localized_string(60066) % new_item.contentTitle)  #"ERROR, la pelicula NO se ha añadido a la videoteca")


def add_tvshow(item, channel=None):
    """
        Guarda contenido en la libreria de series. Este contenido puede ser uno de estos dos:
            - La serie con todos los capitulos incluidos en la lista episodelist.
            - Un solo capitulo descargado previamente en local.

        Para añadir episodios descargados en local, el item debe tener exclusivamente:
            - contentSerieName (o show): Titulo de la serie
            - contentTitle: titulo del episodio para extraer season_and_episode ("1x01 Piloto")
            - title: titulo a mostrar junto al listado de enlaces -findvideos- ("Reproducir video local")
            - infoLabels["tmdb_id"] o infoLabels["imdb_id"]
            - contentType != "movie"
            - channel = "downloads"
            - url : ruta local al video

        @type item: item
        @param item: item que representa la serie a guardar
        @type channel: modulo
        @param channel: canal desde el que se guardara la serie.
            Por defecto se importara item.from_channel o item.channel

    """
    logger.info("show=#" + item.show + "#")

    if item.channel == "downloads":
        itemlist = [item.clone()]

    else:
        # Esta marca es porque el item tiene algo más aparte en el atributo "extra"
        item.action = item.extra if item.extra else item.action
        if isinstance(item.extra, str) and "###" in item.extra:
            item.action = item.extra.split("###")[0]
            item.extra = item.extra.split("###")[1]

        if item.from_action:
            item.__dict__["action"] = item.__dict__.pop("from_action")
        if item.from_channel:
            item.__dict__["channel"] = item.__dict__.pop("from_channel")

        if not channel:
            try:
                # channel = __import__('channels.%s' % item.channel, fromlist=["channels.%s" % item.channel])
                channel = __import__('specials.%s' % channel_alt, fromlist=["specials.%s" % channel_alt])
            except ImportError:
                exec("import channels." + item.channel + " as channel")

        #Para desambiguar títulos, se provoca que TMDB pregunte por el título realmente deseado
        #El usuario puede seleccionar el título entre los ofrecidos en la primera pantalla
        #o puede cancelar e introducir un nuevo título en la segunda pantalla
        #Si lo hace en "Introducir otro nombre", TMDB buscará automáticamente el nuevo título
        #Si lo hace en "Completar Información", cambia parcialmente al nuevo título, pero no busca en TMDB.  Hay que hacerlo
        #Si se cancela la segunda pantalla, la variable "scraper_return" estará en False.  El usuario no quiere seguir

        item = generictools.update_title(item) #Llamamos al método que actualiza el título con tmdb.find_and_set_infoLabels
        #if item.tmdb_stat:
        #    del item.tmdb_stat          #Limpiamos el status para que no se grabe en la Videoteca

        # Obtiene el listado de episodios

        itemlist = getattr(channel, item.action)(item)
        if itemlist and not scrapertools.find_single_match(itemlist[0].title, r'(\d+.\d+)'):
            from specials.autorenumber import select_type, renumber, check
            if not check(item):
                action = item.action
                select_type(item)
                item.action = action
                return add_tvshow(item, channel)
            else:
                itemlist = renumber(itemlist)

    global magnet_caching
    magnet_caching = False
    insertados, sobreescritos, fallidos, path = save_tvshow(item, itemlist)

    if not insertados and not sobreescritos and not fallidos:
        platformtools.dialog_ok(config.get_localized_string(30131), config.get_localized_string(60067) % item.show)
        logger.error("La serie %s no se ha podido añadir a la videoteca. No se ha podido obtener ningun episodio" % item.show)

    elif fallidos == -1:
        platformtools.dialog_ok(config.get_localized_string(30131), config.get_localized_string(60068) % item.show)
        logger.error("La serie %s no se ha podido añadir a la videoteca" % item.show)

    elif fallidos > 0:
        platformtools.dialog_ok(config.get_localized_string(30131), config.get_localized_string(60069) % item.show)
        logger.error("No se han podido añadir %s episodios de la serie %s a la videoteca" % (fallidos, item.show))

    else:
        platformtools.dialog_ok(config.get_localized_string(30131), config.get_localized_string(60070) % item.show)
        logger.info("Se han añadido %s episodios de la serie %s a la videoteca" % (insertados, item.show))
        if config.is_xbmc():
            if config.get_setting("sync_trakt_new_tvshow", "videolibrary"):
                import xbmc
                from platformcode import xbmc_videolibrary
                if config.get_setting("sync_trakt_new_tvshow_wait", "videolibrary"):
                    # Comprobar que no se esta buscando contenido en la videoteca de Kodi
                    while xbmc.getCondVisibility('Library.IsScanningVideo()'):
                        xbmc.sleep(1000)
                # Se lanza la sincronizacion para la videoteca de Kodi
                xbmc_videolibrary.sync_trakt_kodi()
                # Se lanza la sincronización para la videoteca del addon
                xbmc_videolibrary.sync_trakt_addon(path)


def emergency_urls(item, channel=None, path=None, headers={}):
    logger.info()
    import re
    from servers import torrent
    try:
        magnet_caching_e = magnet_caching
    except:
        magnet_caching_e = True
    
    """ 
    Llamamos a Findvideos del canal con la variable "item.videolibray_emergency_urls = True" para obtener la variable
    "item.emergency_urls" con la lista de listas de tuplas de los enlaces torrent y de servidores directos para ese episodio o película
    En la lista [0] siempre deben ir los enlaces torrents, si los hay.  Si se desea cachear los .torrents, la búsqueda va contra esa lista.
    En la lista dos irán los enlaces de servidores directos, pero también pueden ir enlaces magnet (que no son cacheables)
    """
    #lanazamos un "lookup" en el "findvideos" del canal para obtener los enlaces de emergencia
    try:
        if channel == None:                             #Si el llamador no ha aportado la estructura de channel, se crea
            channel = generictools.verify_channel(item.channel)             #Se verifica si es un clon, que devuelva "newpct1"
            #channel = __import__('channels.%s' % channel, fromlist=["channels.%s" % channel])
            channel = __import__('specials.%s' % channel_alt, fromlist=["specials.%s" % channel_alt])
        if hasattr(channel, 'findvideos'):                                  #Si el canal tiene "findvideos"...
            item.videolibray_emergency_urls = True                          #... se marca como "lookup"
            channel_save = item.channel                 #... guarda el canal original por si hay fail-over en Newpct1
            category_save = item.category               #... guarda la categoría original por si hay fail-over o redirección en Newpct1
            if item.channel_redir:                      #... si hay un redir, se restaura temporamente el canal alternativo
                item.channel = scrapertools.find_single_match(item.url, 'http.?\:\/\/(?:www.)?(\w+)\.\w+\/').lower()
                item.category = scrapertools.find_single_match(item.url, 'http.?\:\/\/(?:www.)?(\w+)\.\w+\/').capitalize()
            item_res = getattr(channel, 'findvideos')(item)                 #... se procesa Findvideos
            item_res.channel = channel_save             #... restaura el canal original por si hay fail-over en Newpct1
            item_res.category = category_save           #... restaura la categoría original por si hay fail-over o redirección en Newpct1
            item.category = category_save               #... restaura la categoría original por si hay fail-over o redirección en Newpct1
            del item_res.videolibray_emergency_urls                         #... y se borra la marca de lookup
            if item.videolibray_emergency_urls:
                del item.videolibray_emergency_urls                         #... y se borra la marca de lookup original
    except:
        logger.error('ERROR when processing the title in Findvideos del Canal: ' + item.channel + ' / ' + item.title)
        logger.error(traceback.format_exc())
        item.channel = channel_save                     #... restaura el canal original por si hay fail-over o redirección en Newpct1
        item.category = category_save                   #... restaura la categoría original por si hay fail-over o redirección en Newpct1
        item_res = item.clone()                         #Si ha habido un error, se devuelve el Item original
        if item_res.videolibray_emergency_urls:
            del item_res.videolibray_emergency_urls                         #... y se borra la marca de lookup
        if item.videolibray_emergency_urls:
            del item.videolibray_emergency_urls                             #... y se borra la marca de lookup original
    
    #Si el usuario ha activado la opción "emergency_urls_torrents", se descargarán los archivos .torrent de cada título
    else:                                                                   #Si se han cacheado con éxito los enlaces...
        try:
            referer = None
            post = None
            channel_bis = generictools.verify_channel(item.channel)
            if config.get_setting("emergency_urls_torrents", channel_bis) and item_res.emergency_urls and path != None:
                videolibrary_path = config.get_videolibrary_path()          #detectamos el path absoluto del título
                movies = config.get_setting("folder_movies")
                series = config.get_setting("folder_tvshows")
                if movies in path:
                    folder = movies
                else:
                    folder = series
                videolibrary_path = filetools.join(videolibrary_path, folder)
                i = 1
                if item_res.referer: referer = item_res.referer
                if item_res.post: post = item_res.post
                for url in item_res.emergency_urls[0]:                      #Recorremos las urls de emergencia...
                    torrents_path = re.sub(r'(?:\.\w+$)', '_%s.torrent' % str(i).zfill(2), path)
                    path_real = ''
                    if magnet_caching_e or not url.startswith('magnet'):
                        path_real = torrent.caching_torrents(url, referer, post, torrents_path=torrents_path, headers=headers)  #...  para descargar los .torrents
                    if path_real:                                           #Si ha tenido éxito...
                        item_res.emergency_urls[0][i-1] = path_real.replace(videolibrary_path, '')  #se guarda el "path" relativo
                    i += 1

                #Restauramos variables originales
                if item.referer:
                    item_res.referer = item.referer
                elif item_res.referer:
                    del item_res.referer
                if item.referer:
                    item_res.referer = item.referer
                elif item_res.referer:
                    del item_res.referer
                item_res.url = item.url

        except:
            logger.error('ERROR when caching the .torrent of: ' + item.channel + ' / ' + item.title)
            logger.error(traceback.format_exc())
            item_res = item.clone()                             #Si ha habido un error, se devuelve el Item original

    #logger.debug(item_res.emergency_urls)
    return item_res                                             #Devolvemos el Item actualizado con los enlaces de emergencia
