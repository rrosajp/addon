# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# platformtools
# ------------------------------------------------------------
# Herramientas responsables de adaptar los diferentes
# cuadros de dialogo a una plataforma en concreto,
# en este caso Kodi.
# version 2.0
# ------------------------------------------------------------

from __future__ import division
from __future__ import absolute_import
from past.utils import old_div
#from builtins import str
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    #from future import standard_library
    #standard_library.install_aliases()
    import urllib.parse as urllib                               # Es muy lento en PY2.  En PY3 es nativo
else:
    import urllib                                               # Usamos el nativo de PY2 que es más rápido

import os

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

from channelselector import get_thumb
from core import channeltools
from core import trakt_tools, scrapertools
from core.item import Item
from platformcode import logger
from platformcode import config
from platformcode import unify


class XBMCPlayer(xbmc.Player):

    def __init__(self, *args):
        pass


xbmc_player = XBMCPlayer()

def makeMessage(line1, line2, line3):
    message = line1
    if line2:
        message += '\n' + line2
    if line3:
        message += '\n' + line3
    return message

def dialog_ok(heading, line1, line2="", line3=""):
    dialog = xbmcgui.Dialog()
    return dialog.ok(heading, makeMessage(line1, line2, line3))


def dialog_notification(heading, message, icon=0, time=5000, sound=True):
    dialog = xbmcgui.Dialog()
    try:
        l_icono = xbmcgui.NOTIFICATION_INFO, xbmcgui.NOTIFICATION_WARNING, xbmcgui.NOTIFICATION_ERROR
        dialog.notification(heading, message, l_icono[icon], time, sound)
    except:
        dialog_ok(heading, message)


def dialog_yesno(heading, line1, line2="", line3="", nolabel="No", yeslabel="Si", autoclose=0, customlabel=None):
    # customlabel only on kodi 19
    dialog = xbmcgui.Dialog()
    if config.get_platform() == 'kodi-matrix':
        if autoclose:
            return dialog.yesno(heading, makeMessage(line1, line2, line3), nolabel=nolabel, yeslabel=yeslabel, customlabel=customlabel, autoclose=autoclose)
        else:
            return dialog.yesno(heading, makeMessage(line1, line2, line3), nolabel=nolabel, yeslabel=yeslabel, customlabel=customlabel)
    else:
        if autoclose:
            return dialog.yesno(heading, makeMessage(line1, line2, line3), nolabel=nolabel, yeslabel=yeslabel, autoclose=autoclose)
        else:
            return dialog.yesno(heading, makeMessage(line1, line2, line3), nolabel=nolabel, yeslabel=yeslabel)


def dialog_select(heading, _list):
    return xbmcgui.Dialog().select(heading, _list)


def dialog_multiselect(heading, _list, autoclose=0, preselect=[], useDetails=False):
    return xbmcgui.Dialog().multiselect(heading, _list, autoclose=autoclose, preselect=preselect, useDetails=useDetails)


def dialog_progress(heading, line1, line2=" ", line3=" "):
    dialog = xbmcgui.DialogProgress()
    dialog.create(heading, makeMessage(line1, line2, line3))
    return dialog


def dialog_progress_bg(heading, message=""):
    try:
        dialog = xbmcgui.DialogProgressBG()
        dialog.create(heading, message)
        return dialog
    except:
        return dialog_progress(heading, message)


def dialog_input(default="", heading="", hidden=False):
    keyboard = xbmc.Keyboard(default, heading, hidden)
    keyboard.doModal()
    if keyboard.isConfirmed():
        return keyboard.getText()
    else:
        return None


def dialog_numeric(_type, heading, default=""):
    dialog = xbmcgui.Dialog()
    d = dialog.numeric(_type, heading, default)
    return d


def dialog_textviewer(heading, text):  # disponible a partir de kodi 16
    return xbmcgui.Dialog().textviewer(heading, text)


def dialog_browse(_type, heading, default=""):
    dialog = xbmcgui.Dialog()
    d = dialog.browse(_type, heading, 'files')
    return d


def itemlist_refresh():
    xbmc.executebuiltin("Container.Refresh")


def itemlist_update(item, replace=False):
    if replace:  # reset the path history
        xbmc.executebuiltin("Container.Update(" + sys.argv[0] + "?" + item.tourl() + ", replace)")
    else:
        xbmc.executebuiltin("Container.Update(" + sys.argv[0] + "?" + item.tourl() + ")")


def render_items(itemlist, parent_item):
    """
    Function used to render itemlist on kodi
    """
    logger.info('START render_items')
    thumb_type = config.get_setting('video_thumbnail_type')
    from specials import shortcuts
    from core import httptools
    _handle = int(sys.argv[1])
    default_fanart = config.get_fanart()
    def_context_commands = shortcuts.context()

    # for adding extendedinfo to contextual menu, if it's used
    has_extendedinfo = xbmc.getCondVisibility('System.HasAddon(script.extendedinfo)')
    # for adding superfavourites to contextual menu, if it's used
    sf_file_path = xbmc.translatePath("special://home/addons/plugin.program.super.favourites/LaunchSFMenu.py")
    check_sf = os.path.exists(sf_file_path)
    superfavourites = check_sf and xbmc.getCondVisibility('System.HasAddon("plugin.program.super.favourites")')

    # if it's not a list, do nothing
    if not isinstance(itemlist, list):
        return
    # if there's no item, add "no elements" item
    if not len(itemlist):
        itemlist.append(Item(title=config.get_localized_string(60347), thumbnail=get_thumb('nofolder.png')))

    for item in itemlist:
        item_url = item.tourl()

        if item.category == "":
            item.category = parent_item.category
        if not item.title:
            item.title = ''
        # Si no hay action o es findvideos/play, folder=False porque no se va a devolver ningún listado
        if item.action in ['play', '']:
            item.folder = False
        if item.fanart == "":
            item.fanart = parent_item.fanart
        if item.action == 'play' and thumb_type == 1 and not item.forcethumb:
            item.thumbnail = "https://github.com/kodiondemand/media/raw/master/resources/servers/" + item.server.lower() + '.png'

        # if cloudflare, cookies are needed to display images taken from site
        # before checking domain (time consuming), checking if tmdb failed (so, images scraped from website are used)
        if item.action in ['findvideos'] and not item.infoLabels['tmdb_id'] and item.channel in httptools.channelsCF:
            item.thumbnail = httptools.get_url_headers(item.thumbnail)
            item.fanart = httptools.get_url_headers(item.fanart)

        icon_image = "DefaultFolder.png" if item.folder else "DefaultVideo.png"
        listitem = xbmcgui.ListItem(item.title)
        listitem.setArt({'icon': icon_image, 'thumb': item.thumbnail, 'poster': item.thumbnail,
                         'fanart': item.fanart if item.fanart else default_fanart})

        if config.get_setting("player_mode") == 1 and item.action == "play":
            listitem.setProperty('IsPlayable', 'true')

        set_infolabels(listitem, item)

        # context menu
        if parent_item.channel != 'special':
            context_commands = def_context_commands + set_context_commands(item, item_url, parent_item, has_extendedinfo=has_extendedinfo,
                                                    superfavourites=superfavourites)
        else:
            context_commands = def_context_commands
        listitem.addContextMenuItems(context_commands)

        xbmcplugin.addDirectoryItem(_handle, '%s?%s' % (sys.argv[0], item_url), listitem, item.folder)

    if parent_item.list_type == '':
        breadcrumb = parent_item.category.capitalize()
    else:
        if 'similar' in parent_item.list_type:
            if parent_item.contentTitle != '':
                breadcrumb = config.get_localized_string(70693) + parent_item.contentTitle
            else:
                breadcrumb = config.get_localized_string(70693) + parent_item.contentSerieName
        else:
            breadcrumb = config.get_localized_string(70693)

    xbmcplugin.setPluginCategory(handle=_handle, category=breadcrumb)

    set_view_mode(item, parent_item)

    xbmcplugin.endOfDirectory(_handle)
    logger.info('END render_items')


def set_view_mode(item, parent_item):
    def mode(content, Type):
        mode = int(config.get_setting('view_mode_%s' % content).split(',')[-1])
        if mode == 0:
            logger.info('default mode')
            mode = 55
        xbmcplugin.setContent(handle=int(sys.argv[1]), content=Type)
        xbmc.executebuiltin('Container.SetViewMode(%s)' % mode)
        logger.info('TYPE: ' + Type + ' - ' + 'CONTENT: ' + content)

    def reset_view_mode():
        for mode in ['addon','channel','movie','tvshow','season','episode','server']:
            config.set_setting('skin_name', xbmc.getSkinDir())
            config.set_setting('view_mode_%s' % mode, config.get_localized_string(70003) + ' , 0')

    if xbmc.getSkinDir() != config.get_setting('skin_name') or not config.get_setting('skin_name'):
        reset_view_mode()
        xbmcplugin.setContent(handle=int(sys.argv[1]), content='')
        xbmc.executebuiltin('Container.SetViewMode(%s)' % 55)

    elif (item.contentType in ['movie'] and parent_item.action in ['peliculas']) \
        or (item.channel in ['videolibrary'] and parent_item.action in ['list_movies']) \
        or parent_item.action in ['now_on_tv', 'now_on_misc', 'now_on_misc_film']:
        mode('movie', 'movies')

    elif (item.contentType in ['tvshow'] and parent_item.action in ['peliculas']) \
         or (item.channel in ['videolibrary'] and parent_item.action in ['list_tvshows']):
         mode('tvshow', 'tvshows')

    elif parent_item.action in ['get_seasons']:
        mode('season', 'tvshows')

    elif parent_item.action in ['episodios', 'get_episodes']:
        mode('episode', 'tvshows')

    elif parent_item.action == 'findvideos':
        mode('server', 'addons')

    elif parent_item.action == 'mainlist':
        mode('channel', 'addons')

    else:
        mode('addon', 'addons')


def render_items_old(itemlist, parent_item):
    """
    Función encargada de mostrar el itemlist en kodi, se pasa como parametros el itemlist y el item del que procede
    @type itemlist: list
    @param itemlist: lista de elementos a mostrar

    @type parent_item: item
    @param parent_item: elemento padre
    """
    logger.info('INICIO render_items')
    from core import httptools

    # Si el itemlist no es un list salimos
    if not isinstance(itemlist, list):
        return

    if parent_item.start:
        menu_icon = get_thumb('menu.png')
        menu = Item(channel="channelselector", action="getmainlist", viewmode="movie", thumbnail=menu_icon,
                    title='Menu')
        itemlist.insert(0, menu)

    # Si no hay ningun item, mostramos un aviso
    if not len(itemlist):
        itemlist.append(Item(title=config.get_localized_string(60347), thumbnail=get_thumb('nofolder.png')))

    genre = False
    if 'nero' in parent_item.title:
        genre = True
        anime = False
        if 'anime' in channeltools.get_channel_parameters(parent_item.channel)['categories']:
            anime = True
    # try:
    #     force_unify = channeltools.get_channel_parameters(parent_item.channel)['force_unify']
    # except:
    force_unify = False

    unify_enabled = False

    has_extendedinfo = xbmc.getCondVisibility('System.HasAddon(script.extendedinfo)')

    # Añadir SuperFavourites al menu contextual (1.0.53 o superior necesario)
    sf_file_path = xbmc.translatePath("special://home/addons/plugin.program.super.favourites/LaunchSFMenu.py")
    check_sf = os.path.exists(sf_file_path)
    superfavourites = check_sf and xbmc.getCondVisibility('System.HasAddon("plugin.program.super.favourites")')
    # try:
    #     if channeltools.get_channel_parameters(parent_item.channel)['adult']:
    #         unify_enabled = False
    # except:
    #     pass
    # logger.debug('unify_enabled: %s' % unify_enabled)

    # Recorremos el itemlist
    for item in itemlist:
        # logger.debug(item)
        # Si el item no contiene categoria, le ponemos la del item padre
        item_url = item.tourl()
        if item.category == "":
            item.category = parent_item.category

        # Si title no existe, lo iniciamos como str, para evitar errones "NoType"
        if not item.title:
            item.title = ''

        # Si no hay action o es findvideos/play, folder=False porque no se va a devolver ningún listado
        if item.action in ['play', '']:
            item.folder = False

        # Si el item no contiene fanart, le ponemos el del item padre
        if item.fanart == "":
            item.fanart = parent_item.fanart

        if genre:
            valid_genre = True
            thumb = get_thumb(item.title, auto=True)
            if thumb != '':
                item.thumbnail = thumb
                valid_genre = True
            elif anime:
                valid_genre = True
        elif (('siguiente' in item.title.lower() and '>' in item.title) or ('pagina:' in item.title.lower())):
            item.thumbnail = get_thumb("next.png")
        elif 'add' in item.action:
            if 'pelicula' in item.action:
                item.thumbnail = get_thumb("add_to_videolibrary.png")
            elif 'serie' in item.action:
                item.thumbnail = get_thumb("add_to_videolibrary.png")

        if (unify_enabled or force_unify) and parent_item.channel not in ['kodfavourites']:
            # Formatear titulo con unify
            item = unify.title_format(item)
        else:
            # Formatear titulo metodo old school
            if item.text_color:
                item.title = '[COLOR %s]%s[/COLOR]' % (item.text_color, item.title)
            if item.text_bold:
                item.title = '[B]%s[/B]' % item.title
            if item.text_italic:
                item.title = '[I]%s[/I]' % item.title

        # Añade headers a las imagenes si estan en un servidor con cloudflare
        if item.action == 'play':
            item.thumbnail = unify.thumbnail_type(item)
        else:
            item.thumbnail = httptools.get_url_headers(item.thumbnail)
        item.fanart = httptools.get_url_headers(item.fanart)

        # IconImage para folder y video
        if item.folder:
            icon_image = "DefaultFolder.png"
        else:
            icon_image = "DefaultVideo.png"

        # Ponemos el fanart
        if item.fanart:
            fanart = item.fanart
        else:
            fanart = config.get_fanart()

        # Creamos el listitem
        listitem = xbmcgui.ListItem(item.title)

        # values icon, thumb or poster are skin dependent.. so we set all to avoid problems
        # if not exists thumb it's used icon value
        if config.get_platform(True)['num_version'] >= 16.0:
            listitem.setArt({'icon': icon_image, 'thumb': item.thumbnail, 'poster': item.thumbnail,
                             'fanart': fanart})
        else:
            listitem.setIconImage(icon_image)
            listitem.setThumbnailImage(item.thumbnail)
            listitem.setProperty('fanart_image', fanart)

        # No need it, use fanart instead
        # xbmcplugin.setPluginFanart(int(sys.argv[1]), os.path.join(config.get_runtime_path(), "fanart.jpg"))

        # Esta opcion es para poder utilizar el xbmcplugin.setResolvedUrl()
        # if item.isPlayable == True or (config.get_setting("player_mode") == 1 and item.action == "play"):
        if config.get_setting("player_mode") == 1 and item.action == "play":
            listitem.setProperty('IsPlayable', 'true')

        # Añadimos los infoLabels
        set_infolabels(listitem, item)

        # No arrastrar plot si no es una peli/serie/temporada/episodio
        if item.plot and item.contentType not in ['movie', 'tvshow', 'season', 'episode']:
            item.__dict__['infoLabels'].pop('plot')

        # Montamos el menu contextual
        if parent_item.channel != 'special':
            context_commands = set_context_commands(item, item_url, parent_item, has_extendedinfo=has_extendedinfo, superfavourites=superfavourites)
        else:
            context_commands = []
        # Añadimos el menu contextual
        if config.get_platform(True)['num_version'] >= 17.0 and parent_item.list_type == '':
            listitem.addContextMenuItems(context_commands)
        elif parent_item.list_type == '':
            listitem.addContextMenuItems(context_commands, replaceItems=True)

        from specials import shortcuts
        context_commands += shortcuts.context()

        if not item.totalItems:
            item.totalItems = 0
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url='%s?%s' % (sys.argv[0], item_url),
                                    listitem=listitem, isFolder=item.folder,
                                    totalItems=item.totalItems)

    # Fijar los tipos de vistas...
    if config.get_setting("forceview"):                                         # ...forzamos segun el viewcontent
        xbmcplugin.setContent(int(sys.argv[1]), parent_item.viewcontent)

    elif parent_item.channel not in ["channelselector", "", "kodfavourites"]:     # ... o segun el canal
        xbmcplugin.setContent(int(sys.argv[1]), "movies")

    elif parent_item.channel == "kodfavourites" and parent_item.action == 'mostrar_perfil':
        xbmcplugin.setContent(int(sys.argv[1]), "movies")

    # Fijamos el "breadcrumb"
    if parent_item.list_type == '':
        breadcrumb = parent_item.category.capitalize()
    else:
        if 'similar' in parent_item.list_type:
            if parent_item.contentTitle != '':
                breadcrumb = config.get_localized_string(70693) + parent_item.contentTitle
            else:
                breadcrumb = config.get_localized_string(70693) + parent_item.contentSerieName
        else:
            breadcrumb = config.get_localized_string(70693)

    xbmcplugin.setPluginCategory(handle=int(sys.argv[1]), category=breadcrumb)

    # No ordenar items
    xbmcplugin.addSortMethod(handle=int(sys.argv[1]), sortMethod=xbmcplugin.SORT_METHOD_NONE)

    # Cerramos el directorio
    xbmcplugin.endOfDirectory(handle=int(sys.argv[1]), succeeded=True)

    # Fijar la vista
    # if config.get_setting("forceview"):
    #     viewmode_id = get_viewmode_id(parent_item)
    #     xbmc.executebuiltin("Container.SetViewMode(%s)" % viewmode_id)
    # if parent_item.mode in ['silent', 'get_cached', 'set_cache', 'finish']:
    #     xbmc.executebuiltin("Container.SetViewMode(500)")

    logger.info('END render_items')


def get_viewmode_id(parent_item):
    # viewmode_json habria q guardarlo en un archivo y crear un metodo para q el user fije sus preferencias en:
    # user_files, user_movies, user_tvshows, user_season y user_episodes.
    viewmode_json = {'skin.confluence': {'default_files': 50,
                                         'default_movies': 515,
                                         'default_tvshows': 508,
                                         'default_seasons': 503,
                                         'default_episodes': 504,
                                         'view_list': 50,
                                         'view_thumbnails': 500,
                                         'view_movie_with_plot': 503},
                     'skin.estuary': {'default_files': 50,
                                      'default_movies': 54,
                                      'default_tvshows': 502,
                                      'default_seasons': 500,
                                      'default_episodes': 53,
                                      'view_list': 50,
                                      'view_thumbnails': 500,
                                      'view_movie_with_plot': 54}}

    # Si el parent_item tenia fijado un viewmode usamos esa vista...
    if parent_item.viewmode == 'movie':
        # Remplazamos el antiguo viewmode 'movie' por 'thumbnails'
        parent_item.viewmode = 'thumbnails'

    if parent_item.viewmode in ["list", "movie_with_plot", "thumbnails"]:
        view_name = "view_" + parent_item.viewmode

        '''elif isinstance(parent_item.viewmode, int):
            # only for debug
            viewName = parent_item.viewmode'''

    # ...sino ponemos la vista por defecto en funcion del viewcontent
    else:
        view_name = "default_" + parent_item.viewcontent

    skin_name = xbmc.getSkinDir()
    if skin_name not in viewmode_json:
        skin_name = 'skin.confluence'
    view_skin = viewmode_json[skin_name]
    return view_skin.get(view_name, 50)


def set_infolabels(listitem, item, player=False):
    """
    Metodo para pasar la informacion al listitem (ver tmdb.set_InfoLabels() )
    item.infoLabels es un dicionario con los pares de clave/valor descritos en:
    http://mirrors.xbmc.org/docs/python-docs/14.x-helix/xbmcgui.html#ListItem-setInfo
    https://kodi.wiki/view/InfoLabels
    @param listitem: objeto xbmcgui.ListItem
    @type listitem: xbmcgui.ListItem
    @param item: objeto Item que representa a una pelicula, serie o capitulo
    @type item: item
    """

    infoLabels_dict = {'aired': 'aired', 'album': 'album', 'artist': 'artist', 'cast': 'cast',
                       'castandrole': 'castandrole', 'tmdb_id': 'code', 'code': 'code', 'country': 'country',
                       'credits': 'credits', 'release_date': 'dateadded', 'dateadded': 'dateadded', 'dbid': 'dbid',
                       'director': 'director', 'duration': 'duration', 'episode': 'episode',
                       'episodio_sinopsis': 'episodeguide', 'episodio_air_date': 'None', 'episodio_imagen': 'None',
                       'episodio_titulo': 'title', 'episodio_vote_average': 'rating', 'episodio_vote_count': 'votes',
                       'fanart': 'None', 'genre': 'genre', 'homepage': 'None', 'imdb_id': 'imdbnumber',
                       'imdbnumber': 'imdbnumber', 'in_production': 'None', 'last_air_date': 'lastplayed',
                       'mediatype': 'mediatype', 'mpaa': 'mpaa', 'number_of_episodes': 'None',
                       'number_of_seasons': 'None', 'original_language': 'None', 'originaltitle': 'originaltitle',
                       'overlay': 'overlay', 'poster_path': 'path', 'popularity': 'None', 'playcount': 'playcount',
                       'plot': 'plot', 'plotoutline': 'plotoutline', 'premiered': 'premiered', 'quality': 'None',
                       'rating': 'rating', 'season': 'season', 'set': 'set', 'setid': 'setid',
                       'setoverview': 'setoverview', 'showlink': 'showlink', 'sortepisode': 'sortepisode',
                       'sortseason': 'sortseason', 'sorttitle': 'sorttitle', 'status': 'status', 'studio': 'studio',
                       'tag': 'tag', 'tagline': 'tagline', 'temporada_air_date': 'None', 'temporada_nombre': 'None',
                       'temporada_num_episodios': 'None', 'temporada_poster': 'None', 'title': 'title',
                       'top250': 'top250', 'tracknumber': 'tracknumber', 'trailer': 'trailer', 'thumbnail': 'None',
                       'tvdb_id': 'None', 'tvshowtitle': 'tvshowtitle', 'type': 'None', 'userrating': 'userrating',
                       'url_scraper': 'None', 'votes': 'votes', 'writer': 'writer', 'year': 'year'}
    if item.infoLabels:
        try:
            infoLabels_kodi = {infoLabels_dict[label_tag]: item.infoLabels[label_tag] for label_tag, label_value in list(item.infoLabels.items()) if infoLabels_dict[label_tag] != 'None'}
            listitem.setInfo("video", infoLabels_kodi)
        except:
            listitem.setInfo("video", item.infoLabels)
            logger.error(item.infoLabels)

    # if item.infoLabels:
    #     if 'mediatype' not in item.infoLabels:
    #         item.infoLabels['mediatype'] = item.contentType
    #
    #     try:
    #         for label_tag, label_value in list(item.infoLabels.items()):
    #             try:
    #                 # logger.debug(str(label_tag) + ': ' + str(infoLabels_dict[label_tag]))
    #                 if infoLabels_dict[label_tag] != 'None':
    #                     infoLabels_kodi.update({infoLabels_dict[label_tag]: item.infoLabels[label_tag]})
    #             except:
    #                 continue
    #
    #         listitem.setInfo("video", infoLabels_kodi)
    #
    #     except:
    #         listitem.setInfo("video", item.infoLabels)
    #         logger.error(item.infoLabels)
    #         logger.error(infoLabels_kodi)
    #
    # if player and not item.contentTitle:
    #     listitem.setInfo("video", {"Title": item.title})
    #
    # elif not player:
    #     listitem.setInfo("video", {"Title": item.title})


def set_context_commands(item, item_url, parent_item, **kwargs):
    """
    Función para generar los menus contextuales.
        1. Partiendo de los datos de item.context
             a. Metodo antiguo item.context tipo str separando las opciones por "|" (ejemplo: item.context = "1|2|3")
                (solo predefinidos)
            b. Metodo list: item.context es un list con las diferentes opciones del menu:
                - Predefinidos: Se cargara una opcion predefinida con un nombre.
                    item.context = ["1","2","3"]

                - dict(): Se cargara el item actual modificando los campos que se incluyan en el dict() en caso de
                    modificar los campos channel y action estos serán guardados en from_channel y from_action.
                    item.context = [{"title":"Nombre del menu", "action": "action del menu",
                                        "channel":"channel del menu"}, {...}]

        2. Añadiendo opciones segun criterios
            Se pueden añadir opciones al menu contextual a items que cumplan ciertas condiciones.


        3. Añadiendo opciones a todos los items
            Se pueden añadir opciones al menu contextual para todos los items

        4. Se pueden deshabilitar las opciones del menu contextual añadiendo un comando 'no_context' al item.context.
            Las opciones que Kodi, el skin u otro añadido añada al menu contextual no se pueden deshabilitar.

    @param item: elemento que contiene los menu contextuales
    @type item: item
    @param parent_item:
    @type parent_item: item
    """
    context_commands = []
    # num_version_xbmc = config.get_platform(True)['num_version']

    # Creamos un list con las diferentes opciones incluidas en item.context
    if isinstance(item.context, str):
        context = item.context.split("|")
    elif isinstance(item.context, list):
        context = item.context
    else:
        context = []

    # Opciones segun item.context
    for command in context:
        # Predefinidos
        if isinstance(command, str):
            if command == "no_context":
                return []

        # Formato dict
        if isinstance(command, dict):
            # Los parametros del dict, se sobreescriben al nuevo context_item en caso de sobreescribir "action" y
            # "channel", los datos originales se guardan en "from_action" y "from_channel"
            if "action" in command:
                command["from_action"] = item.action
            if "channel" in command:
                command["from_channel"] = item.channel

            # Si no se está dentro de Alfavoritos y hay los contextos de alfavoritos, descartarlos.
            # (pasa al ir a un enlace de alfavoritos, si este se clona en el canal)
            if parent_item.channel != 'kodfavorites' and 'i_perfil' in command and 'i_enlace' in command:
                continue

            if "goto" in command:
                context_commands.append((command["title"], "XBMC.Container.Refresh (%s?%s)" %
                                         (sys.argv[0], item.clone(**command).tourl())))
            else:
                context_commands.append(
                    (command["title"], "XBMC.RunPlugin(%s?%s)" % (sys.argv[0], item.clone(**command).tourl())))
    # No añadir más opciones predefinidas si se está dentro de Alfavoritos
    if parent_item.channel == 'kodfavorites':
        return context_commands
        # Opciones segun criterios, solo si el item no es un tag (etiqueta), ni es "Añadir a la videoteca", etc...
    if item.action and item.action not in ["add_pelicula_to_library", "add_serie_to_library", "buscartrailer", "actualizar_titulos"]:
        # Mostrar informacion: si el item tiene plot suponemos q es una serie, temporada, capitulo o pelicula
        # if item.infoLabels['plot'] and (num_version_xbmc < 17.0 or item.contentType == 'season'):
        #     context_commands.append((config.get_localized_string(60348), "XBMC.Action(Info)"))

        # ExtendedInfo: Si está instalado el addon y se cumplen una serie de condiciones
        if kwargs.get('has_extendedinfo') \
                and config.get_setting("extended_info") == True:
            if item.contentType == "episode" and item.contentEpisodeNumber and item.contentSeason \
                    and (item.infoLabels['tmdb_id'] or item.contentSerieName):
                param = "tvshow_id =%s, tvshow=%s, season=%s, episode=%s" \
                        % (item.infoLabels['tmdb_id'], item.contentSerieName, item.contentSeason,
                           item.contentEpisodeNumber)
                context_commands.append(("ExtendedInfo",
                                         "XBMC.RunScript(script.extendedinfo,info=extendedepisodeinfo,%s)" % param))

            elif item.contentType == "season" and item.contentSeason \
                    and (item.infoLabels['tmdb_id'] or item.contentSerieName):
                param = "tvshow_id =%s,tvshow=%s, season=%s" \
                        % (item.infoLabels['tmdb_id'], item.contentSerieName, item.contentSeason)
                context_commands.append(("ExtendedInfo",
                                         "XBMC.RunScript(script.extendedinfo,info=seasoninfo,%s)" % param))

            elif item.contentType == "tvshow" and (item.infoLabels['tmdb_id'] or item.infoLabels['tvdb_id'] or
                                                   item.infoLabels['imdb_id'] or item.contentSerieName):
                param = "id =%s,tvdb_id=%s,imdb_id=%s,name=%s" \
                        % (item.infoLabels['tmdb_id'], item.infoLabels['tvdb_id'], item.infoLabels['imdb_id'],
                           item.contentSerieName)
                context_commands.append(("ExtendedInfo",
                                         "XBMC.RunScript(script.extendedinfo,info=extendedtvinfo,%s)" % param))

            elif item.contentType == "movie" and (item.infoLabels['tmdb_id'] or item.infoLabels['imdb_id'] or
                                                  item.contentTitle):
                param = "id =%s,imdb_id=%s,name=%s" \
                        % (item.infoLabels['tmdb_id'], item.infoLabels['imdb_id'], item.contentTitle)

                context_commands.append(("ExtendedInfo",
                                         "XBMC.RunScript(script.extendedinfo,info=extendedinfo,%s)" % param))
                # InfoPlus
        if config.get_setting("infoplus"):
            #if item.infoLabels['tmdb_id'] or item.infoLabels['imdb_id'] or item.infoLabels['tvdb_id'] or \
            #        (item.contentTitle and item.infoLabels["year"]) or item.contentSerieName:
            if item.infoLabels['tmdb_id'] or item.infoLabels['imdb_id'] or item.infoLabels['tvdb_id']:
                context_commands.append(("InfoPlus", "XBMC.RunPlugin(%s?%s&%s)" % (sys.argv[0], item_url,
                            'channel=infoplus&action=start&from_channel=' + item.channel)))

        # Ir al Menu Principal (channel.mainlist)
        if parent_item.channel not in ["news", "channelselector", "downloads"] and item.action != "mainlist" \
                and parent_item.action != "mainlist":
            context_commands.insert(0, (config.get_localized_string(60349), "XBMC.Container.Refresh (%s?%s)" %
                                        (sys.argv[0], Item(channel=item.channel, action="mainlist").tourl())))
            context_commands.insert(1, (config.get_localized_string(70739),
                                        "XBMC.Container.Update (%s?%s)" % (sys.argv[0], Item(action="open_browser",
                                                                                             url=item.url).tourl())))

        # Añadir a Favoritos
        # if num_version_xbmc < 17.0 and \
        #         ((item.channel not in ["favorites", "videolibrary", "help", ""]
        #           or item.action in ["update_videolibrary"]) and parent_item.channel != "favorites"):
        #     context_commands.append((config.get_localized_string(30155), "XBMC.RunPlugin(%s?%s&%s)" %
        #                              (sys.argv[0], item_url, 'channel=favorites&action=addFavourite&from_channel=' + item.channel + '&from_action=' + item.action)))

        # Añadir a Alfavoritos (Mis enlaces)
        if item.channel not in ["favorites", "videolibrary", "help", ""] and parent_item.channel != "favorites":
            context_commands.append(
                (config.get_localized_string(70557), "XBMC.RunPlugin(%s?%s&%s)" %
                 (sys.argv[0], item_url, urllib.urlencode({'channel': "kodfavourites", 'action': "addFavourite",
                                          'from_channel': item.channel,
                                          'from_action': item.action}))))
                # Buscar en otros canales
        if item.contentType in ['movie', 'tvshow'] and item.channel != 'search' and item.action not in ['play'] and parent_item.action != 'mainlist':

            # Buscar en otros canales
            if item.contentSerieName != '':
                item.wanted = item.contentSerieName
            else:
                item.wanted = item.contentTitle

            if item.contentType == 'tvshow':
                mediatype = 'tv'
            else:
                mediatype = item.contentType

            context_commands.append((config.get_localized_string(60350),
                                     "XBMC.Container.Update (%s?%s&%s)" % (sys.argv[0],
                                                    item_url, urllib.urlencode({'channel': 'search',
                                                                                'action': "from_context",
                                                                                   'from_channel': item.channel,
                                                                                   'contextual': True,
                                                                                   'text': item.wanted}))))

            context_commands.append(
                (config.get_localized_string(70561), "XBMC.Container.Update (%s?%s&%s)" % (
                    sys.argv[0], item_url, 'channel=search&action=from_context&search_type=list&page=1&list_type=%s/%s/similar' % (mediatype, item.infoLabels['tmdb_id']))))
                # Definir como Pagina de inicio
        if config.get_setting('start_page'):
            if item.action not in ['episodios', 'seasons', 'findvideos', 'play']:
                context_commands.insert(0, (config.get_localized_string(60351),
                                            "XBMC.RunPlugin(%s?%s)" % (
                                                sys.argv[0], Item(channel='side_menu',
                                                                  action="set_custom_start",
                                                                  parent=item.tourl()).tourl())))

        if (item.channel != "videolibrary" and not config.get_localized_string(70585) in str(item.context)) \
            or (item.channel != "videolibrary" and config.get_localized_string(70585) in str(item.context) and config.get_localized_string(70714) in str(item.context)):
            # Añadir Serie a la videoteca
            if item.action in ["episodios", "get_episodios", "get_seasons"] and item.contentSerieName:
                context_commands.append((config.get_localized_string(60352), "XBMC.RunPlugin(%s?%s&%s)" %
                                         (sys.argv[0], item_url, 'action=add_serie_to_library&from_action=' + item.action)))
            # Añadir Pelicula a videoteca
            elif item.action in ["detail", "findvideos"] and item.contentType == 'movie' and item.contentTitle:
                context_commands.append((config.get_localized_string(60353), "XBMC.RunPlugin(%s?%s&%s)" %
                                         (sys.argv[0], item_url, 'action=add_pelicula_to_library&from_action=' + item.action)))
        
        if item.channel not in ["downloads"] and item.server != 'torrent' and parent_item.action != 'mainlist' and config.get_setting('downloadenabled'):
            # Descargar pelicula
            if item.contentType == "movie":
                context_commands.append((config.get_localized_string(60354), "XBMC.RunPlugin(%s?%s&%s)" %
                                         (sys.argv[0], item_url, 'channel=downloads&action=save_download&from_channel=' + item.channel + '&from_action=' + item.action)))

            elif item.contentSerieName:
                # Descargar serie
                if item.contentType == "tvshow":
                    context_commands.append((config.get_localized_string(60355), "XBMC.RunPlugin(%s?%s&%s)" %
                                             (sys.argv[0], item_url, 'channel=downloads&action=save_download&from_channel=' + item.channel + '&from_action=' + item.action)))
                    context_commands.append((config.get_localized_string(60357), "XBMC.RunPlugin(%s?%s&%s)" %
                                             (sys.argv[0], item_url, 'channel=downloads&action=save_download&download=season&from_channel=' + item.channel + '&from_action=' + item.action)))
                # Descargar episodio
                elif item.contentType == "episode":
                    context_commands.append((config.get_localized_string(60356), "XBMC.RunPlugin(%s?%s&%s)" %
                                             (sys.argv[0], item_url, 'channel=downloads&action=save_download&from_channel=' + item.channel + '&from_action=' + item.action)))
                # Descargar temporada
                elif item.contentType == "season":
                    context_commands.append((config.get_localized_string(60357), "XBMC.RunPlugin(%s?%s&%s)" %
                                             (sys.argv[0], item_url, 'channel=downloads&action=save_download&download=season&from_channel=' + item.channel + '&from_action=' + item.action)))

        # # Abrir configuración
        # if parent_item.channel not in ["setting", "news", "search"] and item.action == "play":
        #     context_commands.append((config.get_localized_string(60358), "XBMC.Container.Update(%s?%s)" %
        #                              (sys.argv[0], Item(channel="setting", action="mainlist").tourl())))

        # Buscar Trailer
        if item.action in ["findvideos", 'episodios', 'check'] or "buscar_trailer" in context:
            context_commands.append(
                (config.get_localized_string(60359), "XBMC.RunPlugin(%s?%s)" % (sys.argv[0], urllib.urlencode({
                    'channel': "trailertools", 'action': "buscartrailer", 'search_title': item.fulltitle if item.fulltitle else item.contentTitle, 'contextual': True}))))

        if kwargs.get('superfavourites'):
            context_commands.append((config.get_localized_string(60361),
                                 "XBMC.RunScript(special://home/addons/plugin.program.super.favourites/LaunchSFMenu.py)"))

    # context_commands = sorted(context_commands, key=lambda comand: comand[0])

    # Menu Rapido
    # context_commands.insert(0, (config.get_localized_string(60360),
    #                             "XBMC.Container.Update (%s?%s)" % (sys.argv[0], Item(channel='side_menu',
    #                                                                                  action="open_menu",
    #                                                                                  parent=parent_item.tourl()).tourl(
    #                             ))))
    if config.dev_mode():
        context_commands.insert(0, ("item info",
                "XBMC.Container.Update (%s?%s)" % (sys.argv[0], Item(action="itemInfo", parent=item.tojson()).tourl())))
    return context_commands


def is_playing():
    return xbmc_player.isPlaying()


def play_video(item, strm=False, force_direct=False, autoplay=False):
    logger.info()
    # logger.debug(item.tostring('\n'))
    logger.debug('item play: %s' % item)
    xbmc_player = XBMCPlayer()
    if item.channel == 'downloads':
        logger.info("Reproducir video local: %s [%s]" % (item.title, item.url))
        xlistitem = xbmcgui.ListItem(path=item.url)
        if config.get_platform(True)['num_version'] >= 16.0:
            xlistitem.setArt({"thumb": item.thumbnail})
        else:
            xlistitem.setThumbnailImage(item.thumbnail)

        set_infolabels(xlistitem, item, True)
        set_player(item, xlistitem, item.url, True, None) # Fix Play From Download Section
        # xbmc_player.play(item.url, xlistitem)
        return

    default_action = config.get_setting("default_action")
    logger.info("default_action=%s" % default_action)

    # Abre el diálogo de selección para ver las opciones disponibles
    opciones, video_urls, seleccion, salir = get_dialogo_opciones(item, default_action, strm, autoplay)
    if salir:
        return

    # se obtienen la opción predeterminada de la configuración del addon
    seleccion = get_seleccion(default_action, opciones, seleccion, video_urls)
    if seleccion < 0:  # Cuadro cancelado
        return

    logger.info("seleccion=%d" % seleccion)
    logger.info("seleccion=%s" % opciones[seleccion])

    # se ejecuta la opcion disponible, jdwonloader, descarga, favoritos, añadir a la videoteca... SI NO ES PLAY
    salir = set_opcion(item, seleccion, opciones, video_urls)
    if salir:
        return

    # obtenemos el video seleccionado
    mediaurl, view, mpd = get_video_seleccionado(item, seleccion, video_urls)
    if mediaurl == "":
        return
    # # no certificate verification
    # mediaurl = mediaurl.replace('https://', 'http://')

    # se obtiene la información del video.
    if not item.contentThumbnail:
        thumb = item.thumbnail
    else:
        thumb = item.contentThumbnail

    xlistitem = xbmcgui.ListItem(path=item.url)
    if config.get_platform(True)['num_version'] >= 16.0:
        xlistitem.setArt({"thumb": thumb})
    else:
        xlistitem.setThumbnailImage(thumb)

    set_infolabels(xlistitem, item, True)

    # si se trata de un vídeo en formato mpd, se configura el listitem para reproducirlo
    # con el addon inpustreamaddon implementado en Kodi 17
    if mpd:
        xlistitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
        xlistitem.setProperty('inputstream.adaptive.manifest_type', 'mpd')

    # se lanza el reproductor
    if force_direct:  # cuando viene de una ventana y no directamente de la base del addon
        # Añadimos el listitem a una lista de reproducción (playlist)
        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playlist.clear()
        playlist.add(mediaurl, xlistitem)

        # Reproduce
        xbmc_player.play(playlist, xlistitem)
    else:
        set_player(item, xlistitem, mediaurl, view, strm)


def stop_video():
    xbmc_player.stop()


def get_seleccion(default_action, opciones, seleccion, video_urls):
    fixpri = False
    # para conocer en que prioridad se trabaja
    priority = int(config.get_setting("resolve_priority"))
    # se usara para comprobar si hay links premium o de debriders
    check = []
    # Comprueba si resolve stop esta desactivado
    if config.get_setting("resolve_stop") == False:
        fixpri = True
    # preguntar
    if default_action == 0:
        # "Elige una opción"
        seleccion = dialog_select(config.get_localized_string(30163), opciones)
    # Ver en calidad baja
    elif default_action == 1:
        resolutions = []
        for url in video_urls:
            if "debrid]" in url[0] or "Premium)" in url[0]:
                check.append(True)
            res = calcResolution(url[0])
            if res:
                resolutions.append(res)
        if resolutions:
            if (fixpri == True and
                    check and
                    priority == 2):
                seleccion = 0
            else:
                seleccion = resolutions.index(min(resolutions))
        else:
            seleccion = 0
    # Ver en alta calidad
    elif default_action == 2:
        resolutions = []
        for url in video_urls:
            if "debrid]" in url[0] or "Premium)" in url[0]:
                check.append(True)
            res = calcResolution(url[0])
            if res:
                resolutions.append(res)

        if resolutions:
            if (fixpri == True and
                    check and
                    priority == 2):
                seleccion = 0
            else:
                seleccion = resolutions.index(max(resolutions))
        else:
            if fixpri == True and check:
                seleccion = 0
            else:
                seleccion = len(video_urls) - 1
    else:
        seleccion = 0
    return seleccion


def calcResolution(option):
    match = scrapertools.find_single_match(option, '([0-9]{2,4})x([0-9]{2,4})')
    resolution = False
    if match:
        resolution = int(match[0]) * int(match[1])
    else:
        if '240p' in option:
            resolution = 320 * 240
        elif '360p' in option:
            resolution = 480 * 360
        elif ('480p' in option) or ('480i' in option):
            resolution = 720 * 480
        elif ('576p' in option) or ('576p' in option):
            resolution = 720 * 576
        elif ('720p' in option) or ('HD' in option):
            resolution = 1280 * 720
        elif ('1080p' in option) or ('1080i' in option) or ('Full HD' in option):
            resolution = 1920 * 1080

    return resolution


def show_channel_settings(**kwargs):
    """
    Muestra un cuadro de configuracion personalizado para cada canal y guarda los datos al cerrarlo.

    Los parámetros que se le pasan se puede ver en la el método al que se llama

    @return: devuelve la ventana con los elementos
    @rtype: SettingsWindow
    """
    from platformcode.xbmc_config_menu import SettingsWindow
    return SettingsWindow("ChannelSettings.xml", config.get_runtime_path()).start(**kwargs)


def show_video_info(*args, **kwargs):
    """
    Muestra una ventana con la info del vídeo.

    Los parámetros que se le pasan se puede ver en la el método al que se llama

    @return: devuelve la ventana con los elementos
    @rtype: InfoWindow
    """

    from platformcode.xbmc_info_window import InfoWindow
    return InfoWindow("InfoWindow.xml", config.get_runtime_path()).start(*args, **kwargs)


def show_recaptcha(key, referer):
    from platformcode.recaptcha import Recaptcha
    return Recaptcha("Recaptcha.xml", config.get_runtime_path()).Start(key, referer)


def alert_no_disponible_server(server):
    # 'El vídeo ya no está en %s' , 'Prueba en otro servidor o en otro canal'
    dialog_ok(config.get_localized_string(30055), (config.get_localized_string(30057) % server),
              config.get_localized_string(30058))


def alert_unsopported_server():
    # 'Servidor no soportado o desconocido' , 'Prueba en otro servidor o en otro canal'
    dialog_ok(config.get_localized_string(30065), config.get_localized_string(30058))


def handle_wait(time_to_wait, title, text):
    logger.info("handle_wait(time_to_wait=%d)" % time_to_wait)
    espera = dialog_progress(' ' + title, "")

    secs = 0
    increment = int(old_div(100, time_to_wait))

    cancelled = False
    while secs < time_to_wait:
        secs += 1
        percent = increment * secs
        secs_left = str((time_to_wait - secs))
        remaining_display = config.get_localized_string(70176) + secs_left + config.get_localized_string(70177)
        espera.update(percent, ' ' + text, remaining_display)
        xbmc.sleep(1000)
        if espera.iscanceled():
            cancelled = True
            break

    if cancelled:
        logger.info('Espera cancelada')
        return False
    else:
        logger.info('Espera finalizada')
        return True


def get_dialogo_opciones(item, default_action, strm, autoplay):
    logger.info()
    # logger.debug(item.tostring('\n'))
    from core import servertools

    opciones = []
    error = False

    try:
        item.server = item.server.lower()
    except AttributeError:
        item.server = ""

    if item.server == "":
        item.server = "directo"

    # Si no es el modo normal, no muestra el diálogo porque cuelga XBMC
    muestra_dialogo = (config.get_setting("player_mode") == 0 and not strm)

    # Extrae las URL de los vídeos, y si no puedes verlo te dice el motivo
    # Permitir varias calidades para server "directo"

    if item.video_urls:
        video_urls, puedes, motivo = item.video_urls, True, ""
    else:
        video_urls, puedes, motivo = servertools.resolve_video_urls_for_playing(
            item.server, item.url, item.password, muestra_dialogo)

    seleccion = 0
    # Si puedes ver el vídeo, presenta las opciones
    if puedes:
        for video_url in video_urls:
            opciones.append(config.get_localized_string(60221) + " " + video_url[0])

        if item.server == "local":
            opciones.append(config.get_localized_string(30164))
        else:
            # "Descargar"
            import xbmcaddon
            addon = xbmcaddon.Addon('plugin.video.kod')
            downloadenabled = addon.getSetting('downloadenabled')
            if downloadenabled != "false":
                opcion = config.get_localized_string(30153)
                opciones.append(opcion)

            if item.isFavourite:
                # "Quitar de favoritos"
                opciones.append(config.get_localized_string(30154))
            else:
                # "Añadir a favoritos"
                opciones.append(config.get_localized_string(30155))

            if not strm and item.contentType == 'movie':
                # "Añadir a videoteca"
                opciones.append(config.get_localized_string(30161))

        if default_action == 3:
            seleccion = len(opciones) - 1

        # Busqueda de trailers en youtube
        if item.channel not in ["Trailer", "ecarteleratrailers"]:
            # "Buscar Trailer"
            opciones.append(config.get_localized_string(30162))

    # Si no puedes ver el vídeo te informa
    else:
        if not autoplay:
            if item.server != "":
                if "<br/>" in motivo:
                    ret = dialog_yesno(config.get_localized_string(60362), motivo.split("<br/>")[0], motivo.split("<br/>")[1],
                              item.url, nolabel='ok', yeslabel=config.get_localized_string(70739))
                else:
                    ret = dialog_yesno(config.get_localized_string(60362), motivo, item.url, nolabel='ok', yeslabel=config.get_localized_string(70739))
            else:
                ret = dialog_yesno(config.get_localized_string(60362), config.get_localized_string(60363),
                          config.get_localized_string(60364), item.url, nolabel='ok', yeslabel=config.get_localized_string(70739))
            if ret:
                xbmc.executebuiltin("XBMC.Container.Update (%s?%s)" % (sys.argv[0], Item(action="open_browser",
                                                                                             url=item.url).tourl()))
            if item.channel == "favorites":
                # "Quitar de favoritos"
                opciones.append(config.get_localized_string(30154))

            if len(opciones) == 0:
                error = True

    return opciones, video_urls, seleccion, error


def set_opcion(item, seleccion, opciones, video_urls):
    logger.info()
    # logger.debug(item.tostring('\n'))
    salir = False
    # No ha elegido nada, lo más probable porque haya dado al ESC

    if seleccion == -1:
        # Para evitar el error "Uno o más elementos fallaron" al cancelar la selección desde fichero strm
        listitem = xbmcgui.ListItem(item.title)

        if config.get_platform(True)['num_version'] >= 16.0:
            listitem.setArt({'icon': "DefaultVideo.png", 'thumb': item.thumbnail})
        else:
            listitem.setIconImage("DefaultVideo.png")
            listitem.setThumbnailImage(item.thumbnail)

        xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, listitem)

    # "Descargar"
    elif opciones[seleccion] == config.get_localized_string(30153):
        from specials import downloads
        downloads.show_disclaimer()

        if item.contentType == "list" or item.contentType == "tvshow":
            item.contentType = "video"
        item.play_menu = True
        downloads.save_download(item)
        salir = True

    # "Quitar de favoritos"
    elif opciones[seleccion] == config.get_localized_string(30154):
        from specials import favorites
        favorites.delFavourite(item)
        salir = True

    # "Añadir a favoritos":
    elif opciones[seleccion] == config.get_localized_string(30155):
        from specials import favorites
        item.from_channel = "favorites"
        favorites.addFavourite(item)
        salir = True

    # "Buscar Trailer":
    elif opciones[seleccion] == config.get_localized_string(30162):
        config.set_setting("subtitulo", False)
        xbmc.executebuiltin("XBMC.RunPlugin(%s?%s)" %
                            (sys.argv[0], item.clone(channel="trailertools", action="buscartrailer",
                                                     contextual=True).tourl()))
        salir = True

    return salir


def get_video_seleccionado(item, seleccion, video_urls):
    logger.info()
    mediaurl = ""
    view = False
    wait_time = 0
    mpd = False

    # Ha elegido uno de los vídeos
    if seleccion < len(video_urls):
        mediaurl = video_urls[seleccion][1]
        if len(video_urls[seleccion]) > 4:
            wait_time = video_urls[seleccion][2]
            if not item.subtitle:
                item.subtitle = video_urls[seleccion][3]
            mpd = True
        elif len(video_urls[seleccion]) > 3:
            wait_time = video_urls[seleccion][2]
            if not item.subtitle:
                item.subtitle = video_urls[seleccion][3]
        elif len(video_urls[seleccion]) > 2:
            wait_time = video_urls[seleccion][2]
        view = True

    # Si no hay mediaurl es porque el vídeo no está :)
    logger.info("mediaurl=" + mediaurl)
    if mediaurl == "":
        if item.server == "unknown":
            alert_unsopported_server()
        else:
            alert_no_disponible_server(item.server)

    # Si hay un tiempo de espera (como en megaupload), lo impone ahora
    if wait_time > 0:
        continuar = handle_wait(wait_time, item.server, config.get_localized_string(60365))
        if not continuar:
            mediaurl = ""

    return mediaurl, view, mpd


def set_player(item, xlistitem, mediaurl, view, strm):
    logger.info()
    logger.debug("item:\n" + item.tostring('\n'))
    # Movido del conector "torrent" aqui
    if item.server == "torrent":
        play_torrent(item, xlistitem, mediaurl)
        return

    # Si es un fichero strm no hace falta el play
    elif strm:
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xlistitem)
        if item.subtitle != "":
            xbmc.sleep(2000)
            xbmc_player.setSubtitles(item.subtitle)

    else:
        logger.info("player_mode=%s" % config.get_setting("player_mode"))
        logger.info("mediaurl=" + mediaurl)
        if config.get_setting("player_mode") == 3 or "megacrypter.com" in mediaurl:
            from platformcode import download_and_play
            download_and_play.download_and_play(mediaurl, "download_and_play.tmp", config.get_setting("downloadpath"))
            return

        elif config.get_setting("player_mode") == 0 or item.play_from == 'window' or \
                (config.get_setting("player_mode") == 3 and mediaurl.startswith("rtmp")):
            # Añadimos el listitem a una lista de reproducción (playlist)
            playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
            playlist.clear()
            playlist.add(mediaurl, xlistitem)

            # Reproduce
            # xbmc_player = xbmc_player
            xbmc_player.play(playlist, xlistitem)
            if config.get_setting('trakt_sync'):
                trakt_tools.wait_for_update_trakt()

        # elif config.get_setting("player_mode") == 1 or item.isPlayable:
        elif config.get_setting("player_mode") == 1:
            logger.info("Tras setResolvedUrl")
            # si es un archivo de la videoteca enviar a marcar como visto

            if strm or item.strm_path:
                from platformcode import xbmc_videolibrary
                xbmc_videolibrary.mark_auto_as_watched(item)
            logger.debug(item)
            xlistitem.setPath(mediaurl)
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, xlistitem)
            xbmc.sleep(2500)

        elif config.get_setting("player_mode") == 2:
            xbmc.executebuiltin("PlayMedia(" + mediaurl + ")")

    # TODO MIRAR DE QUITAR VIEW
    if item.subtitle != "" and view:
        logger.info("Subtítulos externos: " + item.subtitle)
        xbmc.sleep(2000)
        xbmc_player.setSubtitles(item.subtitle)

    # si es un archivo de la videoteca enviar a marcar como visto
    if strm or item.strm_path:
        from platformcode import xbmc_videolibrary
        xbmc_videolibrary.mark_auto_as_watched(item)


def torrent_client_installed(show_tuple=False):
    # Plugins externos se encuentra en servers/torrent.json nodo clients
    from core import filetools
    from core import jsontools
    torrent_clients = jsontools.get_node_from_file("torrent.json", "clients", filetools.join(config.get_runtime_path(),"servers"))
    torrent_options = []
    for client in torrent_clients:
        if xbmc.getCondVisibility('System.HasAddon("%s")' % client["id"]):
            if show_tuple:
                torrent_options.append([config.get_localized_string(60366) % client["name"], client["url"]])
            else:
                torrent_options.append(config.get_localized_string(60366) % client["name"])
    return torrent_options


def play_torrent(item, xlistitem, mediaurl):
    logger.info()
    import time
    import traceback

    from core import filetools
    from core import httptools
    from lib import generictools
    from servers import torrent


    # Si Libtorrent ha dado error de inicialización, no se pueden usar los clientes internos
    UNRAR = config.get_setting("unrar_path", server="torrent", default="")
    LIBTORRENT = config.get_setting("libtorrent_path", server="torrent", default='')
    size_rar = 2
    rar_files = []
    if item.password:
        size_rar = 3


    # Opciones disponibles para Reproducir torrents
    torrent_options = list()
    torrent_options.append([config.get_localized_string(30033)])
    torrent_options.append([config.get_localized_string(30033) + ' MCT'])

    torrent_options.extend(torrent_client_installed(show_tuple=True))

    torrent_client = config.get_setting("torrent_client", server="torrent")

    # Si es Libtorrent y no está soportado, se ofrecen alternativas, si las hay...
    if not LIBTORRENT and len(torrent_options) < 3:
        from specials import quasar_download
        if dialog_yesno(config.get_localized_string(70784), config.get_localized_string(70782)):
            quasar_download.download()

    if torrent_client and torrent_client - 1 <= len(torrent_options):
        if torrent_client == 0:
            seleccion = dialog_select(config.get_localized_string(70193), [opcion[0] for opcion in torrent_options])
        else:
            seleccion = torrent_client - 1
    else:
        if len(torrent_options) > 1:
            seleccion = dialog_select(config.get_localized_string(70193), [opcion[0] for opcion in torrent_options])
        else:
            seleccion = 0

    if seleccion < 2 and not LIBTORRENT:
        dialog_ok(config.get_localized_string(30033), config.get_localized_string(70774), \
                  config.get_localized_string(70775) % config.get_setting("libtorrent_error", server="torrent", default=''), \
                  config.get_localized_string(70776))
        if len(torrent_options) > 2:
            seleccion = dialog_select(config.get_localized_string(70193), [opcion[0] for opcion in torrent_options])
            if seleccion < 2:
                return
        else:
            return
    # Si es Torrenter o Elementum con opción de Memoria, se ofrece la posibilidad ee usar Libtorrent temporalemente
    elif seleccion > 1 and LIBTORRENT and UNRAR and 'RAR-' in item.torrent_info and (
            "torrenter" in torrent_options[seleccion][0] \
            or ("elementum" in torrent_options[seleccion][0] and xbmcaddon.Addon(id="plugin.video.%s"  % torrent_options[seleccion][0].replace('Plugin externo: ','')).getSetting('download_storage') == '1')):
        if dialog_yesno(torrent_options[seleccion][0], config.get_localized_string(70777), config.get_localized_string(70778), config.get_localized_string(70779) % size_rar):
            seleccion = 1
        else:
            return
    # Si es Elementum pero con opción de Memoria, se muestras los Ajustes de Elementum y se pide al usuario que cambie a "Usar Archivos"
    elif seleccion > 1 and not LIBTORRENT and UNRAR and 'RAR-' in item.torrent_info and "elementum" in \
            torrent_options[seleccion][0] \
            and xbmcaddon.Addon(id="plugin.video.%s" % torrent_options[seleccion][0].replace('Plugin externo: ', '')) \
            .getSetting('download_storage') == '1':
        if dialog_yesno(torrent_options[seleccion][0], config.get_localized_string(70780) % size_rar, config.get_localized_string(70781)):
            __settings__ = xbmcaddon.Addon(
                id="plugin.video.%s" % torrent_options[seleccion][0].replace('Plugin externo: ', ''))
            __settings__.openSettings()  # Se visulizan los Ajustes de Elementum
            elementum_dl = xbmcaddon.Addon(
                id="plugin.video.%s" % torrent_options[seleccion][0].replace('Plugin externo: ', '')) \
                .getSetting('download_storage')
            if elementum_dl != '1':
                config.set_setting("elementum_dl", "1", server="torrent")  # Salvamos el cambio para restaurarlo luego
        return  # Se sale, porque habrá refresco y cancelaría Kodi si no

    # Descarga de torrents a local
    if seleccion >= 0:

        #### Compatibilidad con Kodi 18: evita cuelgues/cancelaciones cuando el .torrent se lanza desde pantalla convencional
        # if xbmc.getCondVisibility('Window.IsMedia'):
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, xlistitem)  # Preparamos el entorno para evitar error Kod1 18
        time.sleep(0.5)  # Dejamos tiempo para que se ejecute

        # Nuevo método de descarga previa del .torrent.  Si da error, miramos si hay alternatica local.
        # Si ya es local, lo usamos
        url = ''
        url_stat = False
        torrents_path = ''
        referer = None
        post = None
        rar = False
        size = ''
        password = ''
        if item.password:
            password = item.password

        videolibrary_path = config.get_videolibrary_path()  # Calculamos el path absoluto a partir de la Videoteca
        if scrapertools.find_single_match(videolibrary_path, '(^\w+:\/\/)'):  # Si es una conexión REMOTA, usamos userdata local
            videolibrary_path = config.get_data_path()  # Calculamos el path absoluto a partir de Userdata
        if not filetools.exists(videolibrary_path):  # Si no existe el path, pasamos al modo clásico
            videolibrary_path = False
        else:
            torrents_path = filetools.join(videolibrary_path, 'temp_torrents', 'client_torrent.torrent')  # path descarga temporal
        if not videolibrary_path or not filetools.exists(filetools.join(videolibrary_path, 'temp_torrents')):  # Si no existe la carpeta temporal, la creamos
            filetools.mkdir(filetools.join(videolibrary_path, 'temp_torrents'))

        # Si hay headers, se pasar a la petición de descarga del .torrent
        headers = {}
        if item.headers:
            headers = item.headers

        # identificamos si es una url o un path de archivo
        if not item.url.startswith("\\") and not item.url.startswith("/") and not url_stat:
            timeout = 10
            if item.torrent_alt:
                timeout = 5
            # Si es una llamada con POST, lo preparamos
            if item.referer: referer = item.referer
            if item.post: post = item.post
            # Descargamos el .torrent
            size, url, torrent_f, rar_files = generictools.get_torrent_size(item.url, referer, post, torrents_path=torrents_path, timeout=timeout, lookup=False, headers=headers, short_pad=True)
            if url:
                url_stat = True
                item.url = url
                if "torrentin" in torrent_options[seleccion][0]:
                    item.url = 'file://' + item.url

        if not url and item.torrent_alt:  # Si hay error, se busca un .torrent alternativo
            if (item.torrent_alt.startswith("\\") or item.torrent_alt.startswith("/")) and videolibrary_path:
                item.url = item.torrent_alt  # El .torrent alternativo puede estar en una url o en local
            elif not item.url.startswith("\\") and not item.url.startswith("/"):
                item.url = item.torrent_alt

        # Si es un archivo .torrent local, actualizamos el path relativo a path absoluto
        if (item.url.startswith("\\") or item.url.startswith("/")) and not url_stat and videolibrary_path:  # .torrent alternativo local
            movies = config.get_setting("folder_movies")
            series = config.get_setting("folder_tvshows")
            if item.contentType == 'movie':
                folder = movies  # películas
            else:
                folder = series  # o series
            item.url = filetools.join(config.get_videolibrary_path(), folder, item.url)  # dirección del .torrent local en la Videoteca
            if filetools.copy(item.url, torrents_path, silent=True):  # se copia a la carpeta generíca para evitar problemas de encode
                item.url = torrents_path
            if "torrentin" in torrent_options[seleccion][0]:  # Si es Torrentin, hay que añadir un prefijo
                item.url = 'file://' + item.url
            size, rar_files = generictools.get_torrent_size('', file_list=True, local_torr=torrents_path,short_pad=True)

        mediaurl = item.url

    if seleccion >= 0:

        # Reproductor propio BT (libtorrent)
        if seleccion == 0:
            torrent.bt_client(mediaurl, xlistitem, rar_files, subtitle=item.subtitle, password=password, item=item)

        # Reproductor propio MCT (libtorrent)
        elif seleccion == 1:
            from platformcode import mct
            mct.play(mediaurl, xlistitem, subtitle=item.subtitle, password=password, item=item)

        # Plugins externos
        else:
            mediaurl = urllib.quote_plus(item.url)
            # Llamada con más parámetros para completar el título
            if ("quasar" in torrent_options[seleccion][1] or "elementum" in torrent_options[seleccion][1]) and item.infoLabels['tmdb_id']:
                if item.contentType == 'episode' and "elementum" not in torrent_options[seleccion][1]:
                    mediaurl += "&episode=%s&library=&season=%s&show=%s&tmdb=%s&type=episode" % (
                    item.infoLabels['episode'], item.infoLabels['season'], item.infoLabels['tmdb_id'],
                    item.infoLabels['tmdb_id'])
                elif item.contentType == 'movie':
                    mediaurl += "&library=&tmdb=%s&type=movie" % (item.infoLabels['tmdb_id'])

            xbmc.executebuiltin("PlayMedia(" + torrent_options[seleccion][1] % mediaurl + ")")

            # Si es un archivo RAR, monitorizamos el cliente Torrent hasta que haya descargado el archivo,
            # y después lo extraemos, incluso con RAR's anidados y con contraseña
            torr_client = torrent_options[seleccion][0].replace('Plugin externo: ', '')
            if 'RAR-' in size and torr_client in ['quasar', 'elementum'] and UNRAR:
                rar_file, save_path_videos, folder_torr = torrent.wait_for_download(item, mediaurl, rar_files, torr_client)  # Esperamos mientras se descarga el RAR
                if rar_file and save_path_videos:  # Si se ha descargado el RAR...
                    dp = dialog_progress_bg('KoD %s' % torr_client)
                    video_file, rar, video_path, erase_file_path = torrent.extract_files(rar_file, save_path_videos, password, dp, item, torr_client)  # ... extraemos el vídeo del RAR
                    dp.close()

                    # Reproducimos el vídeo extraido, si no hay nada en reproducción
                    while is_playing() and rar and not xbmc.abortRequested:
                        time.sleep(3)  # Repetimos cada intervalo
                    if rar and not xbmc.abortRequested:
                        time.sleep(1)
                        video_play = filetools.join(video_path, video_file)
                        log("##### video_play: %s" % video_play)
                        playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
                        playlist.clear()
                        playlist.add(video_play, xlistitem)
                        xbmc_player.play(playlist)

        if seleccion > 1:
            # Seleccionamos que clientes torrent soportamos para el marcado de vídeos vistos: asumimos que todos funcionan
            torrent.mark_auto_as_watched(item)

            # Si se ha extraido un RAR, se pregunta para borrar los archivos después de reproducir el vídeo (plugins externos)
            while is_playing() and rar and not xbmc.abortRequested:
                time.sleep(3)  # Repetimos cada intervalo
            if rar and not xbmc.abortRequested:
                if dialog_yesno('KoD %s' % torr_client, config.get_localized_string(30031)):
                    log("##### erase_file_path: %s" % erase_file_path)
                    try:
                        torr_data, deamon_url, index = torrent.get_tclient_data(folder_torr, torr_client)
                        if torr_data and deamon_url:
                            data = httptools.downloadpage('%sdelete/%s' % (deamon_url, index), timeout=5, alfa_s=True).data
                        time.sleep(1)
                        if filetools.isdir(erase_file_path):
                            filetools.rmdirtree(erase_file_path)
                        elif filetools.exists(erase_file_path) and filetools.isfile(erase_file_path):
                            filetools.remove(erase_file_path)
                    except:
                        logger.error(traceback.format_exc(1))
            elementum_dl = config.get_setting("elementum_dl", server="torrent", default='')  # Si salvamos el cambio de Elementum
            if elementum_dl:
                config.set_setting("elementum_dl", "", server="torrent")  # lo reseteamos en Alfa
                xbmcaddon.Addon(id="plugin.video.%s" % torrent_options[seleccion][0].replace('Plugin externo: ', '')) \
                    .setSetting('download_storage', elementum_dl)  # y lo reseteamos en Elementum


def log(texto):
    xbmc.log(texto, xbmc.LOGNOTICE)

