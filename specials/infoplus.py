# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# infoplus ventana con información del Item
# ------------------------------------------------------------

from future import standard_library
standard_library.install_aliases()

import re, sys, xbmc, xbmcaddon, xbmcgui
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

from builtins import range
from threading import Thread
from core import httptools, scrapertools, filetools, tmdb
from core.item import Item
from core.support import typo, dbg
from core.scrapertools import decodeHtmlentities as dhe
from platformcode import config, logger, platformtools

info_language = ["de", "en", "es", "fr", "it", "pt"] # from videolibrary.json
def_lang = info_language[config.get_setting("info_language", "videolibrary")]

max_poster = 6

global mainWindow
mainWindow = list()
ActorsWindow = None
TrailerWindow = None
relatedWindow = None
imagesWindow = None
ActorInfoWindow = None
SearchWindow = None
SearchWindows = list()

exit_loop = False

ACTION_SHOW_FULLSCREEN = 36
ACTION_GESTURE_SWIPE_LEFT = 511
ACTION_SELECT_ITEM = 7
ACTION_PREVIOUS_MENU = 10
ACTION_MOVE_LEFT = 1
ACTION_MOVE_RIGHT = 2
ACTION_MOVE_UP = 3
ACTION_MOVE_DOWN = 4

xinfoplus_set = config.get_setting("infoplus_set")

def start(item, recommendations=[], from_window=False):
    main_window = main(item=item, recommendations=recommendations, from_window=from_window)
    try:
        mainWindow.append(main_window)
        main_window.doModal()
    except:
        return


class main(xbmcgui.WindowDialog):
    def __init__(self, *args, **kwargs):
        self.item = kwargs.get('item')
        self.recommendations = kwargs.get('recommendations')
        self.from_window = kwargs.get('from_window', False)
        self.images = {}

        if self.item.contentType == "movie":
            Type = "movie"
            search_type = "movie"
            rating_icon = imagepath('tmdb')
        else:
            Type = "serie"
            search_type = "tv"
            rating_icon = imagepath('tvdb')

        info_copy = dict(self.item.infoLabels)
        self.item.infoLabels.pop("season", None)
        self.item.infoLabels.pop("episode", None)
        if not self.item.infoLabels["year"] and not self.item.infoLabels["tmdb_id"]:
            platformtools.dialog_notification(config.get_localized_string(60471), config.get_localized_string(60472) % config.get_localized_string(60329))
            global mainWindow
            self.close()
            del mainWindow
            return

        tmdb.set_infoLabels_item(self.item, True)
        self.infoLabels = self.item.infoLabels
        self.infoLabels["season"] = info_copy.get("season", None)
        self.infoLabels["episode"] = info_copy.get("episode", None)

        if not self.infoLabels["tmdb_id"]:
            platformtools.dialog_notification(config.get_localized_string(60473), config.get_localized_string(60474) % config.get_localized_string(60329))
            global mainWindow
            self.close()
            del mainWindow
            return

        Title = typo(self.infoLabels.get("title"), 'bold')
        if self.infoLabels.get("rating"): rating = typo(self.infoLabels["rating"], 'bold')
        else: rating = typo('N/A', 'bold')

        self.infoLabels["plot"] = self.infoLabels.get("plot")

        thread = Thread(target=get_recomendations, args=[self.item, self.infoLabels, self.recommendations])
        thread.setDaemon(True)
        thread.start()

        if self.infoLabels.get("status") == "Ended" and Type == "serie": status = config.get_localized_string(60478)
        elif self.infoLabels.get("status") and Type == "serie": status = config.get_localized_string(60479)
        else: status = "%s"

        if self.infoLabels.get("tagline") and Type == "serie": self.infoLabels["tagline"] = status % "(" + self.infoLabels["tagline"] + ")"
        elif not self.infoLabels.get("tagline") and Type == "serie": self.infoLabels["tagline"] = status % config.get_localized_string(60480) % self.infoLabels.get("number_of_seasons",  "---")
        else: self.infoLabels["tagline"] = status % self.infoLabels.get("tagline", "")

        if self.infoLabels["tmdb_id"]:
            otmdb = tmdb.Tmdb(id_Tmdb=self.infoLabels["tmdb_id"], tipo=search_type)
            self.item.images = otmdb.result.get("images", {})
            for key, value in list(self.item.images.items()):
                if not value: self.item.images.pop(key)

            if not self.infoLabels.get("originaltitle"): self.infoLabels["originaltitle"] = otmdb.result.get("original_title", otmdb.result.get("original_name", ""))
            self.trailers = otmdb.get_videos()
            if otmdb.result.get("runtime", 0): self.infoLabels["duration"] = int(otmdb.result.get("runtime", 0))
        else:
            self.trailers = []

        if self.item.contentType != "movie":
            try:
                # look for the theme of the series
                Title = re.sub(r'\[.*?\]', '', Title)
                Title = self.infoLabels.get("originaltitle", Title)
                Title = re.sub("'", "", Title)
                url_tvthemes = "http://televisiontunes.com/search.php?q=%s" % Title.replace(' ', '+')

                data = httptools.downloadpage(url_tvthemes).data
                page_theme = scrapertools.find_single_match(data, r'<!-- sond design -->.*?<li><a href="([^"]+)"')

                if page_theme:
                    page_theme = "http://televisiontunes.com" + page_theme
                    data = httptools.downloadpage(page_theme).data
                    song = scrapertools.find_single_match(data, r'<form name="song_name_form">.*?type="hidden" value="(.*?)"')
                    song = song.replace(" ", "%20")
                    pl = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
                    pl.clear()
                    pl.add(song)
                    self.player = xbmc.Player()
                    self.player.play(pl)
            except:
                import traceback
                logger.error(traceback.format_exc())

        if not self.infoLabels.get("fanart") and self.images:
            try:
                if self.item.contentType == "movie":
                    self.infoLabels["fanart"] = self.images.get("moviebackground", self.images.get("hdmovieclearart", self.images.get("movieart")))[0].get("url")
                else:
                    self.infoLabels["fanart"] = self.images.get("showbackground", self.images.get("hdclearart", self.images.get("clearart")))[0].get("url")
            except:
                self.infoLabels["fanart"] = imagepath('background.jpg')
                import traceback
                logger.error(traceback.format_exc())

        elif self.infoLabels.get("season") and self.images.get("showbackground"):
            for imagen in self.images["showbackground"]:
                if imagen.get("season") == str(self.infoLabels.get("season", "")):
                    self.infoLabels["fanart"] = imagen["url"]
                    break

        if not self.infoLabels.get("fanart"): self.infoLabels["fanart"] = imagepath('background.jpg')

        self.name = re.sub(r'(\[.*?\])', '', self.infoLabels["title"])
        self.buttons = []

        skin = xbmc.getSkinDir()
        self.fonts = get_fonts(skin)

        #### Kodi 18 Compatibility ####
        if config.get_platform(True)['num_version'] < 18: self.setCoordinateResolution(2)

        self.background = xbmcgui.ControlImage(0, 0, 1280, 720, imagepath('white'), colorDiffuse='FF232323')
        self.addControl(self.background)
        self.fanart = xbmcgui.ControlImage(0, 0, 1280, 720, self.infoLabels.get("fanart", ""), 1, colorDiffuse='88FFFFFF')
        self.addControl(self.fanart)
        self.bar = xbmcgui.ControlImage(0, 680, 1280, 40, imagepath('white'), colorDiffuse='FF232323')
        self.addControl(self.bar)
        self.bar.setAnimations([('WindowOpen', 'effect=slide start=0,40 end=0,0 delay=100 time=200'),('WindowClose', 'effect=slide start=0,0 end=0,40 delay=100 time=200')])

        # TITLE
        self.title = xbmcgui.ControlTextBox(40, 40, 750, 30, font=self.fonts["30"])
        self.addControl(self.title)
        self.title.setAnimations([('WindowOpen', 'effect=slide start=-750,0 end=0,0 delay=100 time=200'), ('WindowClose', 'effect=slide start=0,0 end=-750,0 delay=100 time=200')])
        self.title.setText(Title)

        # TAGLINE
        self.tagline = xbmcgui.ControlFadeLabel(40, 73, 750, 30, font=self.fonts["12"])
        self.addControl(self.tagline)
        self.tagline.setAnimations([('WindowOpen', 'effect=slide start=-750,0 end=0,0 delay=100 time=200'), ('WindowClose', 'effect=slide start=0,0 end=-750,0 delay=100 time=200')])
        self.tagline.addLabel(self.infoLabels.get("tagline"))

        # DURATION
        self.duration = xbmcgui.ControlTextBox(40, 100, 750, 30, self.fonts["10"])
        self.addControl(self.duration)
        self.duration.setAnimations([('WindowOpen', 'effect=slide start=-750,0 end=0,0 delay=100 time=200'), ('WindowClose', 'effect=slide start=0,0 end=-750,0 delay=100 time=200')])
        self.duration.setText(config.get_localized_string(70252) % self.infoLabels["duration"] if self.item.contentType == "movie" and self.infoLabels.get("duration", 0) else '')

        # RATING
        #icon
        self.icon = xbmcgui.ControlImage(40, 140, 50, 50, rating_icon)
        self.addControl(self.icon)
        self.icon.setAnimations([('WindowOpen', 'effect=slide start=-40,0 end=0,0 delay=100 time=200'), ('WindowClose', 'effect=slide start=0,0 end=-40,0 delay=100 time=200')])

        # rating
        self.rating = xbmcgui.ControlTextBox(100, 150, 150, 40)
        self.addControl(self.rating)
        self.rating.setAnimations([('WindowOpen', 'effect=slide start=-100,0 end=0,0 delay=100 time=200'), ('WindowClose', 'effect=slide start=0,0 end=-100,0 delay=100 time=200')])
        self.rating.setText(rating)

        # TRAILER
        self.trailerButton = xbmcgui.ControlButton(180, 140, 50, 50, '', noFocusTexture=imagepath('trailer_no_focus'), focusTexture=imagepath('trailer_focus'))
        self.trailerButton.setAnimations([('WindowOpen', 'effect=slide start=-170,0 end=0,0 delay=100 time=200'), ('WindowClose', 'effect=slide start=0,0 end=-170,0 delay=100 time=200')])
        self.addControl(self.trailerButton)
        self.buttons.append(self.trailerButton)

        # ACTOR
        self.actorButton = xbmcgui.ControlButton(240, 140, 50, 50, '', noFocusTexture=imagepath('actors_no_focus'), focusTexture=imagepath('actors_focus'))
        self.trailerButton.setAnimations([('WindowOpen', 'effect=slide start=-220,0 end=0,0 delay=100 time=200'), ('WindowClose', 'effect=slide start=0,0 end=-220,0 delay=100 time=200')])
        self.addControl(self.actorButton)
        self.buttons.append(self.actorButton)

        # SEARCH
        self.global_search = xbmcgui.ControlButton(300, 140, 50, 50, '', noFocusTexture=imagepath('search_no_focus'), focusTexture=imagepath('search_focus'))
        self.trailerButton.setAnimations([('WindowOpen', 'effect=slide start=-270,0 end=0,0 delay=100 time=200'), ('WindowClose', 'effect=slide start=0,0 end=-270,0 delay=100 time=200')])
        self.addControl(self.global_search)
        self.buttons.append(self.global_search)

        self.setFocus(self.trailerButton)

        # PLOT
        self.plot = xbmcgui.ControlTextBox(40, 240, 760, 360, font=self.fonts["24"])
        self.addControl(self.plot)
        self.plot.setAnimations([('WindowOpen', 'effect=slide start=-750,0 end=0,0 delay=100 time=200'), ('WindowClose', 'effect=slide start=0,0 end=-750,0 delay=100 time=200')])
        try: self.plot.autoScroll(10000, 2000, 30000)
        except: xbmc.executebuiltin(config.get_localized_string(70500))
        self.plot.setText(dhe(typo(self.infoLabels.get("plot", ""),'bold')))

        # POSTER
        self.poster = xbmcgui.ControlImage(880, 40, 400, 600, self.item.thumbnail)
        self.addControl(self.poster)
        self.poster.setAnimations([('WindowOpen', 'effect=slide start=+400,0 end=0,0 delay=100 time=200'), ('WindowClose', 'effect=slide start=0,0 end=+400,0 delay=100 time=200')])
        self.thumbnail = xbmcgui.ControlButton(880, 40, 400, 600, '', focusTexture=imagepath('focus'), noFocusTexture=imagepath('nofocus'))
        self.thumbnail.setAnimations([('WindowOpen', 'effect=slide start=+400,0 end=0,0 delay=100 time=200'), ('WindowClose', 'effect=slide start=0,0 end=+400,0 delay=100 time=200')])
        self.addControl(self.thumbnail)
        self.buttons.append(self.thumbnail)

        # BUTTON LEFT
        self.btn_left = xbmcgui.ControlButton(0, 680, 40, 40, '', imagepath('previous_focus'), imagepath('previous_no_focus'))
        self.addControl(self.btn_left)
        self.buttons.append(self.btn_left)
        self.btn_left.setAnimations([('WindowOpen', 'effect=slide start=0,40 end=0,0 delay=100 time=200'),('WindowClose', 'effect=slide start=0,0 end=0,40 delay=100 time=200')])

        # RECOMMENDED
        xbmc.sleep(200)
        self.max_movies = max_poster
        self.idps = []
        self.max_movies_buttons = []
        self.focus = 0
        i = 0
        count = 0
        if thread:
            while thread.isAlive(): xbmc.sleep(100)
        for idp, title, thumbnail in self.recommendations:
            if count % max_poster == 0: i = 0
            if thumbnail:
                self.image = xbmcgui.ControlButton(40 + i, 420 + 260, 200, 300, '', thumbnail, thumbnail)
                self.buttons.append(self.image)
                if count < max_poster:
                    self.addControl(self.image)
                    self.image.setAnimations([('focus', 'effect=slide start=0,0 end=0,-260 time=200'),('unfocus', 'effect=slide start=-0,-260 end=0,0 time=200'),('WindowOpen', 'effect=slide start=0,40 end=0,0 delay=100 time=200 conditional=true'),('WindowClose', 'effect=slide start=0,0 end=0,40 delay=100 time=200 conditional=true')])
                self.idps.append([self.image, title, idp, thumbnail])
                self.max_movies_buttons.append([self.image, title])
                i += 200
                count += 1
        xbmc.sleep(200)

        # BUTTON RIGHT
        self.btn_right = xbmcgui.ControlButton(1240, 680, 40, 40, '', imagepath('next_focus'), imagepath('next_no_focus'))
        self.addControl(self.btn_right)
        self.buttons.append(self.btn_right)
        self.btn_right.setAnimations([('WindowOpen', 'effect=slide start=0,40 end=0,0 delay=100 time=200'),('WindowClose', 'effect=slide start=0,0 end=0,40 delay=100 time=200')])
        xbmc.sleep(200)


    def onAction(self, action):
        if action == ACTION_PREVIOUS_MENU or action == ACTION_GESTURE_SWIPE_LEFT or action == 110 or action == 92:
            global mainWindow
            xbmc.executebuiltin('PlayMedia(Stop)')
            self.close()
            mainWindow.pop()
            if not mainWindow:
                del mainWindow
            else:
                xbmc.sleep(800)
                mainWindow[-1].doModal()

        if action == ACTION_MOVE_RIGHT:
            if self.getFocusId() not in [3014, 3022]:
                if self.focus < len(self.buttons) - 1:
                    self.focus += 1
                    while True:
                        id_focus = str(self.buttons[self.focus].getId())
                        if xbmc.getCondVisibility('[Control.IsVisible(' + id_focus + ')]'):
                            self.setFocus(self.buttons[self.focus])
                            break
                        self.focus += 1
                        if self.focus == len(self.buttons):
                            break
            elif self.getFocusId() in [3014]:
                self.focus = 0
                self.setFocus(self.trailerButton)
            elif self.getFocusId() in [3022]:
                self.focus = 4
                self.setFocus(self.btn_left)


        if action == ACTION_MOVE_DOWN or action == ACTION_MOVE_UP:
            if self.focus < 4:
                self.focus = 4
                self.setFocus(self.btn_left)
            else:
                self.focus = 0
                self.setFocus(self.trailerButton)

        if action == ACTION_MOVE_LEFT:
            if self.getFocusId() not in [3009, 3015]:
                if self.focus > 0:
                    self.focus -= 1
                    while True:
                        id_focus = str(self.buttons[self.focus].getId())
                        if xbmc.getCondVisibility('[Control.IsVisible(' + id_focus + ')]'):
                            self.setFocus(self.buttons[self.focus])
                            break
                        self.focus -= 1
                        if self.focus == 0:
                            break
            elif self.getFocusId() in [3009]:
                self.focus = 3
                self.setFocus(self.thumbnail)
            elif self.getFocusId() in [3015]:
                self.focus = len(self.buttons) - 1
                self.setFocus(self.btn_right)

        if action == 105 or action == 6:
            xbmc.executebuiltin('SendClick(%s)' % self.btn_right.getId())

        if action == 104 or action == 5:
            xbmc.executebuiltin('SendClick(%s)' % self.btn_left.getId())

    def onControl(self, control):
        if control == self.actorButton:
            global ActorsWindow
            ActorsWindow = Actors('DialogSelect.xml', config.get_runtime_path(), tmdb_id=self.infoLabels["tmdb_id"], item=self.item, fonts=self.fonts)
            ActorsWindow.doModal()

        elif control == self.trailerButton:
            global TrailerWindow
            item = self.item.clone(thumbnail=self.infoLabels.get("thumbnail", ""), contextual=True, contentTitle=self.name, windowed=True, infoLabels=self.infoLabels)
            Trailer('TrailerWindow.xml', config.get_runtime_path()).Start(item, self.trailers)

        elif control == self.thumbnail:
            global imagesWindow
            imagesWindow = images(tmdb=self.item.images)
            imagesWindow.doModal()

        elif control == self.global_search:
            if self.from_window:
                itemlist = search_type(self, self.item.from_channel)
                SearchWindow = Search('DialogSelect.xml', config.get_runtime_path(), itemlist=itemlist, item=self.item.clone(channel=self.item.from_channel))
            else:
                itemlist = search_type(self)
                SearchWindow = Search('DialogSelect.xml', config.get_runtime_path(), itemlist=itemlist, item=self.item.clone())

            if not itemlist and self.from_window:
                if platformtools.dialog_yesno(typo(self.item.contentTitle,'bold'), config.get_localized_string(70820) % self.item.from_channel):
                    itemlist = search_type(self)
                    SearchWindow = Search('DialogSelect.xml', config.get_runtime_path(), itemlist=itemlist, item=self.item.clone())
            if itemlist:
                global SearchWindow
                SearchWindow.doModal()
            else:
                platformtools.dialog_ok(typo(self.item.contentTitle,'bold'), config.get_localized_string(70819) % self.item.from_channel)

        elif control == self.btn_right:
            try:
                i = 1
                count = 0
                for photo, title in self.max_movies_buttons:
                    if i > self.max_movies - max_poster and i <= self.max_movies and count < max_poster:
                        self.removeControls([photo])
                        count += 1
                    elif i > self.max_movies and count < max_poster * 2:
                        self.addControl(photo)
                        photo.setAnimations([('focus', 'effect=slide start=0,0 end=0,-260 time=200'),('unfocus', 'effect=slide start=-0,-260 end=0,0 time=200'),('WindowOpen', 'effect=slide start=0,40 end=0,0 delay=100 time=200 conditional=true'),('WindowClose', 'effect=slide start=0,0 end=0,40 delay=100 time=200 conditional=true')])
                        count += 1
                        self.max_movies += 1
                        xbmc.sleep(120)
                    i += 1
                xbmc.sleep(300)
            except:
                pass

        elif control == self.btn_left:
            try:
                i = 1
                count = 0
                for photo, title in self.max_movies_buttons:
                    stay = max_poster + (self.max_movies % max_poster)
                    if stay == max_poster:
                        stay = max_poster * 2
                    stay2 = self.max_movies % max_poster
                    if not stay2:
                        stay2 = max_poster
                    if i > lself.max_movies - stay and count < max_poster:
                        self.addControl(photo)
                        photo.setAnimations([('focus', 'effect=slide start=0,0 end=0,-260 time=200'),('unfocus', 'effect=slide start=-0,-260 end=0,0 time=200'),('WindowOpen', 'effect=slide start=0,40 end=0,0 delay=100 time=200 conditional=true'),('WindowClose', 'effect=slide start=0,0 end=0,40 delay=100 time=200 conditional=true')])
                        count += 1
                    elif i > self.max_movies - stay2 and i <= self.max_movies and count < max_poster * 2:
                        self.removeControls([photo])
                        count += 1
                        self.max_movies -= 1
                    i += 1
            except:
                pass

        else:
            for button, title, id, poster in self.idps:
                logger.log('INFOS',button, title, id, poster)
                if control == button:
                    new_item=self.item.clone(title=title, infoLabels={'tmdb_id':id}, contentType=self.item.contentType)
                    self.close()
                    start(new_item, from_window=True)


class Search(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.list = kwargs.get("itemlist")
        self.item = kwargs.get("item")

    def onInit(self):
        try:
            self.control_list = self.getControl(6)
            self.getControl(5).setNavigation(self.control_list, self.control_list, self.control_list, self.control_list)
            self.getControl(3).setEnabled(0)
            self.getControl(3).setVisible(0)
        except:
            pass
        self.getControl(1).setLabel(config.get_localized_string(60498))

        self.getControl(5).setLabel(config.get_localized_string(60495))
        self.control_list.reset()
        items = []
        for item_l in self.list:
            item = xbmcgui.ListItem(item_l.title)
            try: item.setArt({"thumb": item_l.thumbnail})
            except: item.setThumbnailImage(item_l.thumbnail)
            item.setProperty("item_copy", item_l.tourl())
            items.append(item)

        self.getControl(6).addItems(items)
        self.setFocusId(6)

    def onAction(self, action):
        global SearchWindow
        if (action == ACTION_SELECT_ITEM or action == 100) and self.getFocusId() == 6:
            dialog = platformtools.dialog_progress_bg(config.get_localized_string(60496), config.get_localized_string(60497))
            selectitem = self.getControl(6).getSelectedItem()
            item = Item().fromurl(selectitem.getProperty("item_copy"))
            channel = __import__('channels.%s' % item.channel, fromlist=["channels.%s" % item.channel])
            itemlist = getattr(channel, item.action)(item)
            global SearchWindows
            window = GlobalSearch('DialogSelect.xml', config.get_runtime_path(), itemlist=itemlist, dialog=dialog)
            SearchWindows.append(window)
            self.close()
            window.doModal()

        if (action == ACTION_SELECT_ITEM or action == 100) and self.getFocusId() in [5,7]: self.close()
        elif action == ACTION_PREVIOUS_MENU or action == ACTION_GESTURE_SWIPE_LEFT or action == 110 or action == 92: self.close()


class GlobalSearch(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.lista = kwargs.get("itemlist")
        self.dialog = kwargs.get("dialog")

    def onInit(self):
        self.dialog.close()
        try:
            self.control_list = self.getControl(6)
            self.getControl(5).setNavigation(self.control_list, self.control_list, self.control_list, self.control_list)
            self.getControl(3).setEnabled(0)
            self.getControl(3).setVisible(0)
        except:
            pass

        self.getControl(1).setLabel(config.get_localized_string(60498))
        self.getControl(5).setLabel(config.get_localized_string(60495))
        self.control_list.reset()
        if not self.lista:
            global SearchWindows
            self.close()
            SearchWindows.pop()
            if len(SearchWindows) - 1 >= 0:
                SearchWindows[-1].doModal()
            else:
                SearchWindow.doModal()
        else:
            items = []
            for item_l in self.lista:
                item = xbmcgui.ListItem(item_l.title)
                try:
                    item.setArt({"thumb": item_l.thumbnail})
                except:
                    item.setThumbnailImage(item_l.thumbnail)
                item.setProperty("item_copy", item_l.tourl())
                items.append(item)
            self.getControl(6).addItems(items)
            self.setFocusId(6)

    def onAction(self, action):
        global SearchWindows
        if (action == ACTION_SELECT_ITEM or action == 100) and self.getFocusId() == 6:
            selectitem = self.getControl(6).getSelectedItem()
            item = Item().fromurl(selectitem.getProperty("item_copy"))
            channel = __import__('channels.%s' % item.channel, fromlist=["channels.%s" % item.channel])
            ventana_error = None
            if item.action == "play":
                if hasattr(channel, 'play'):
                    itemlist = channel.play(item)
                    if len(itemlist) > 0:
                        item = itemlist[0]
                    else:
                        ventana_error = xbmcgui.Dialog()
                        ok = ventana_error.ok("plugin", config.get_localized_string(60500))
                        return

                global SearchWindow, exit_loop, mainWindow, ActorInfoWindow, relatedWindow, ActorsWindow
                borrar = [relatedWindow, ActorInfoWindow, ActorsWindow, SearchWindow]

                borrar.extend(SearchWindows)
                borrar.extend(mainWindow)
                if item.server != "torrent":
                    import time
                    check = False
                    time_start = time.time()
                    try: platformtools.play_video(item)
                    except: check = True
                    xbmc.sleep(1500)
                    if not check and xbmc.Player().isPlaying():
                        exit_loop = True
                        for window in borrar:
                            try: window.close()
                            except: pass
                        while True:
                            xbmc.sleep(1000)
                            if not xbmc.Player().isPlaying(): break
                            if time.time() - time_start > 120: return

                        for window in SearchWindows: window.doModal()
                        SearchWindow.doModal()
                        mainWindow[-1].doModal()

                elif item.server == "torrent":
                    exit_loop = True
                    for window in borrar:
                        try:
                            window.close()
                            del window
                        except:
                            pass
                    platformtools.play_video(item)

            else:
                try:
                    dialog = platformtools.dialog_progress_bg(config.get_localized_string(60496), config.get_localized_string(60497))
                    itemlist = getattr(channel, item.action)(item)
                    window = GlobalSearch('DialogSelect.xml', config.get_runtime_path(), itemlist=itemlist, dialog=dialog)
                    SearchWindows.append(window)
                    self.close()
                    window.doModal()
                except:
                    pass

        elif (action == ACTION_SELECT_ITEM or action == 100) and self.getFocusId() in [5,7]:
            self.close()
            SearchWindows.pop()
            if len(SearchWindows) - 1 >= 0: SearchWindows[-1].doModal()
            else: SearchWindow.doModal()

        elif action == ACTION_PREVIOUS_MENU or action == ACTION_GESTURE_SWIPE_LEFT or action == 110 or action == 92:
            self.close()
            SearchWindows.pop()
            if len(SearchWindows) - 1 >= 0: SearchWindows[-1].doModal()
            else: SearchWindow.doModal()


def globalSearch(item, infoLabels, org_title=False):
    logger.log()
    if item.contentType == "movie": cat = ["movie"]
    else: cat = ["serie"]
    cat += ["infoPlus"]
    new_item = Item(title=item.contentTitle, text=item.contentTitle, mode=item.contentType, infoLabels=item.infoLabels)
    from specials import search
    return search.channel_search(new_item)


class Actors(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.tmdb_id = kwargs.get("tmdb_id")
        self.item = kwargs.get("item")
        self.fonts = kwargs.get("fonts")

    def onInit(self):
        try:
            self.control_list = self.getControl(6)
            self.getControl(5).setNavigation(self.control_list, self.control_list, self.control_list, self.control_list)
            self.getControl(3).setEnabled(0)
            self.getControl(3).setVisible(0)
        except:
            pass
        self.getControl(1).setLabel(config.get_localized_string(60501))
        self.getControl(5).setLabel(config.get_localized_string(60495))
        self.control_list.reset()
        items = []

        Type = self.item.contentType
        if Type != "movie": Type = "tv"
        otmdb = tmdb.Tmdb(id_Tmdb=self.tmdb_id, tipo=Type)
        actors = otmdb.result.get("credits", {}).get("cast", [])

        if self.item.contentType == "movie": cast = otmdb.result.get("credits", {}).get("crew", [])
        else: cast = otmdb.result.get("created_by", [])

        for crew in cast:
            if crew.get('job', '') == 'Director' or self.item.contentType != "movie": actors.insert(0, crew)

        for actor in actors:
            name_info = typo(actor["name"], 'bold')
            try:
                name = "%s (%s)" % (actor["name"], actor["character"])
                job = "actor"
            except:
                job = "Director"
                name = "%s (%s)" % (actor["name"], job)
            image = "https://image.tmdb.org/t/p/original"
            if actor["profile_path"]: image += actor["profile_path"]
            else: image = imagepath('no_photo')
            item = xbmcgui.ListItem(name)
            try:
                item.setArt({"thumb": image})
            except:
                item.setThumbnailImage(image)
            item.setProperty("id_actor", str(actor["id"]))
            item.setProperty("name_info", name_info)
            item.setProperty("thumbnail", image)
            item.setProperty("job", job)
            items.append(item)

        self.getControl(6).addItems(items)
        self.setFocusId(6)

    def onAction(self, action):
        if (action == ACTION_SELECT_ITEM or action == 100) and self.getFocusId() == 6:
            selectitem = self.getControl(6).getSelectedItem()
            id_actor = selectitem.getProperty("id_actor")
            name_info = selectitem.getProperty("name_info")
            thumbnail = selectitem.getProperty("thumbnail")
            job = selectitem.getProperty("job")
            dialog = platformtools.dialog_progress(config.get_localized_string(60502), config.get_localized_string(60503) % job.lower())

            global ActorInfoWindow
            ActorInfoWindow = ActorInfo(id=id_actor, name=name_info, thumbnail=thumbnail, item=self.item, fonts=self.fonts, dialog=dialog, job=job)
            ActorInfoWindow.doModal()
            xbmc.sleep(400)
        elif (action == ACTION_SELECT_ITEM or action == 100) and self.getFocusId() == [5,7]: self.close()
        elif action == ACTION_PREVIOUS_MENU or action == ACTION_GESTURE_SWIPE_LEFT or action == 110 or action == 92: self.close()

class ActorInfo(xbmcgui.WindowDialog):
    def __init__(self, *args, **kwargs):
        global exit_loop
        if exit_loop: exit_loop = False
        self.id = kwargs.get('id')
        self.nombre = kwargs.get('name')
        self.thumbnail = kwargs.get('thumbnail')
        self.item = kwargs.get('item')
        self.fonts = kwargs.get('fonts')
        self.job = kwargs.get('job')

        self.dialog = kwargs.get('dialog')
        if self.item.contentType == "movie":
            Type = "movie"
            search = {'url': 'person/%s' % self.id, 'language': def_lang, 'append_to_response': 'movie_credits,images'}
        else:
            Type = "tv"
            search = {'url': 'person/%s' % self.id, 'language': def_lang, 'append_to_response': 'tv_credits,images'}

        actor_tmdb = tmdb.Tmdb(discover=search)
        if not actor_tmdb.result.get("biography") and actor_tmdb.result.get("imdb_id"):
            data = httptools.downloadpage("http://www.imdb.com/name/%s/bio" % actor_tmdb.result["imdb_id"]).data
            info = scrapertools.find_single_match(data, r'<div class="soda odd">.*?<p>(.*?)</p>')
            if info:
                bio = dhe(scrapertools.htmlclean(info.strip()))
                actor_tmdb.result["biography"] = bio
            else:
                actor_tmdb.result["biography"] = config.get_localized_string(60504)
        elif not actor_tmdb.result.get("biography"):
            actor_tmdb.result["biography"] = config.get_localized_string(60504)

        #### Kodi 18 Compatibility ####
        if config.get_platform(True)['num_version'] < 18:
            self.setCoordinateResolution(2)

        self.background = xbmcgui.ControlImage(0, 0, 1280, 720, imagepath('white'), colorDiffuse='FF232323')
        self.addControl(self.background)

        # TITLE
        self.title = xbmcgui.ControlTextBox(40, 40, 750, 30, font=self.fonts["30"])
        self.addControl(self.title)
        self.title.setAnimations([('WindowOpen', 'effect=slide start=-750,0 end=0,0 delay=100 time=200'), ('WindowClose', 'effect=slide start=0,0 end=-750,0 delay=100 time=200')])
        self.title.setText(self.nombre)

        # ACTOR INFO (PLOT)
        self.info_actor = xbmcgui.ControlTextBox(40, 140, 760, 460, font=self.fonts["24"])
        self.addControl(self.info_actor)
        self.info_actor.setAnimations([('WindowOpen', 'effect=slide start=-750,0 end=0,0 delay=100 time=200'), ('WindowClose', 'effect=slide start=0,0 end=-750,0 delay=100 time=200')])
        try: self.info_actor.autoScroll(10000, 2000, 30000)
        except: xbmc.executebuiltin( config.get_localized_string(70500))
        self.info_actor.setText(typo(actor_tmdb.result.get("biography", config.get_localized_string(60504)),'bold'))

        # POSTER
        self.thumbnail = xbmcgui.ControlImage(880, 40, 400, 600, self.thumbnail)
        self.addControl(self.thumbnail)
        self.thumbnail.setAnimations([('WindowOpen', 'effect=slide start=+400,0 end=0,0 delay=100 time=200'), ('WindowClose', 'effect=slide start=0,0 end=+400,0 delay=100 time=200')])
        xbmc.sleep(300)

        # Movies
        self.Titles = []
        search_type = "cast"
        if self.job != "actor": search_type = "crew"
        ids = []
        for entradas in actor_tmdb.result.get("%s_credits" % Type, {}).get(search_type, []):
            if entradas["id"] not in ids and entradas["poster_path"]:
                ids.append(entradas["id"])
                thumbnail = "https://image.tmdb.org/t/p/original"
                thumbnail += entradas["poster_path"]
                if self.item.contentType == "movie": self.Titles.append([entradas["id"], entradas.get("title", entradas.get("original_title", "")), thumbnail])
                else: self.Titles.append([entradas["id"], entradas.get("title", entradas.get("original_title", "")), thumbnail])

        self.dialog.update(40, config.get_localized_string(60505))
        self.max_movies = max_poster
        self.idps = []
        self.buttons = []
        self.max_movies_buttons = []
        self.focus = 0
        i = 0
        count = 0
        self.btn_left = xbmcgui.ControlButton(0, 680, 40, 40, '', imagepath('previous_focus'), imagepath('previous_no_focus'))
        self.addControl(self.btn_left)
        self.buttons.append(self.btn_left)
        for idp, title, photo in self.Titles:
            if count % max_poster == 0: i = 0
            self.image = xbmcgui.ControlButton(40 + i, 420 + 260, 200, 300, '', photo, photo)
            self.buttons.append(self.image)
            if count < max_poster:
                self.addControl(self.image)
                self.image.setAnimations([('focus', 'effect=slide start=0,0 end=0,-260 time=200'),('unfocus', 'effect=slide start=-0,-260 end=0,0 time=200'),('WindowOpen', 'effect=slide start=0,40 end=0,0 delay=100 time=200 conditional=true'),('WindowClose', 'effect=slide start=0,0 end=0,40 delay=100 time=200 conditional=true')])
            self.idps.append([self.image, title, idp, photo])
            self.max_movies_buttons.append([self.image, title])
            i += 200
            count += 1
        xbmc.sleep(200)

        self.btn_right = xbmcgui.ControlButton(1240, 680, 40, 40, '', imagepath('next_focus'), imagepath('next_no_focus'))
        self.addControl(self.btn_right)
        self.buttons.append(self.btn_right)
        xbmc.sleep(200)
        self.dialog.close()


    def onAction(self, action):
        global exit_loop
        if exit_loop:
            exit_loop = False

        if action == ACTION_MOVE_RIGHT:
            if self.getFocusId() not in [3012]:
                if self.focus < len(self.buttons) - 1:
                    self.focus += 1
                    while True:
                        id_focus = str(self.buttons[self.focus].getId())
                        if xbmc.getCondVisibility('[Control.IsVisible(' + id_focus + ')]'):
                            self.setFocus(self.buttons[self.focus])
                            break
                        self.focus += 1
                        if self.focus == len(self.buttons):
                            break
            elif self.getFocusId() in [3012]:
                self.focus = 0
                self.setFocus(self.btn_left)

        if action == ACTION_MOVE_LEFT:
            if self.getFocusId() not in [3005]:
                if self.focus > 0:
                    self.focus -= 1
                    while True:
                        id_focus = str(self.buttons[self.focus].getId())
                        if xbmc.getCondVisibility('[Control.IsVisible(' + id_focus + ')]'):
                            self.setFocus(self.buttons[self.focus])
                            break
                        self.focus -= 1
                        if self.focus == len(self.buttons):
                            break
            elif self.getFocusId() in [3005]:
                self.focus = len(self.buttons) - 1
                self.setFocus(self.btn_right)

        if action == ACTION_PREVIOUS_MENU or action == ACTION_GESTURE_SWIPE_LEFT or action == 110 or action == 92:
            exit_loop = True
            self.close()

        if action == 105 or action == 6:
            for button, title, id, poster in self.idps:
                try:
                    if self.getFocusId() == button.getId() and self.btn_right:
                        self.focus = len(self.buttons) - 1
                        xbmc.executebuiltin('SendClick(%s)' % self.btn_right.getId())
                except:
                    pass

        if action == 104 or action == 5:
            for button, title, id, poster in self.idps:
                try:
                    if self.getFocusId() == button.getId() and self.btn_left:
                        self.setFocus(self.btn_left)
                        xbmc.executebuiltin('SendClick(%s)' % self.btn_left.getId())
                except:
                    pass

    def onControl(self, control):
        if control == self.btn_right:
            try:
                i = 1
                count = 0
                for photo, title in self.max_movies_buttons:
                    if i > self.max_movies - max_poster and i <= self.max_movies and count < max_poster:
                        self.removeControls([photo])
                        count += 1
                    elif i > self.max_movies and count < max_poster * 2:
                        self.addControl(photo)
                        photo.setAnimations([('focus', 'effect=slide start=0,0 end=0,-260 time=200'),('unfocus', 'effect=slide start=-0,-260 end=0,0 time=200'),('WindowOpen', 'effect=slide start=0,40 end=0,0 delay=100 time=200 conditional=true'),('WindowClose', 'effect=slide start=0,0 end=0,40 delay=100 time=200 conditional=true')])
                        count += 1
                        self.max_movies += 1
                        xbmc.sleep(120)
                    i += 1
                xbmc.sleep(300)
            except:
                pass
        elif control == self.btn_left:
            try:
                i = 1
                count = 0
                for photo, title in self.max_movies_buttons:
                    stay = max_poster + (self.max_movies % max_poster)
                    if stay == max_poster:
                        stay = max_poster * 2
                    stay2 = self.max_movies % max_poster
                    if not stay2:
                        stay2 = max_poster
                    if i > self.max_movies - stay and count < max_poster:
                        self.addControl(photo)
                        photo.setAnimations([('focus', 'effect=slide start=0,0 end=0,-260 time=200'),('unfocus', 'effect=slide start=-0,-260 end=0,0 time=200'),('WindowOpen', 'effect=slide start=0,40 end=0,0 delay=100 time=200 conditional=true'),('WindowClose', 'effect=slide start=0,0 end=0,40 delay=100 time=200 conditional=true')])
                        count += 1
                    elif i > self.max_movies - stay2 and i <= self.max_movies and count < max_poster * 2:
                        self.removeControls([photo])
                        count += 1
                        self.max_movies -= 1
                    i += 1
                if self.max_movies == max_poster:
                    self.btn_left.setVisible(False)
            except:
                pass

        else:
            for button, title, id, poster in self.idps:
                if control == button:
                    new_item = self.item.clone(title=title,infoLabels={'tmdb_id':id})
                    self.close()
                    start(new_item, from_window=True)


class images(xbmcgui.WindowDialog):
    def __init__(self, *args, **kwargs):
        self.tmdb = kwargs.get("tmdb", {})

        self.image_list = []

        for key, value in self.tmdb.items():
            for detail in value: self.image_list.append('http://image.tmdb.org/t/p/original' + detail["file_path"])
        # for image in self.imdb: self.image_list.append(image["src"])
        # for image, title in self.mal: self.image_list.append(image)

        #### Kodi 18 Compatibility ####
        if config.get_platform(True)['num_version'] < 18: self.setCoordinateResolution(2)

        self.background = xbmcgui.ControlImage(0, 0, 1280, 720, imagepath('white'), colorDiffuse='CC232323')
        self.addControl(self.background)
        main_image = self.image_list[0] if self.image_list else ''
        self.main_image = xbmcgui.ControlImage(0, 0, 1280, 720, main_image, 2)
        self.addControl(self.main_image)

        # BUTTON LEFT
        self.btn_left = xbmcgui.ControlButton(0, 300, 60, 60, '', imagepath('previous_focus'), imagepath('previous_no_focus'))
        self.addControl(self.btn_left)
        self.btn_left.setAnimations([('WindowOpen', 'effect=slide start=-60,0 end=0,0 delay=100 time=200'),('WindowClose', 'effect=slide start=0,0 end=-60,0 delay=100 time=200')])

        # BUTTON RIGHT
        self.btn_right = xbmcgui.ControlButton(1220, 300, 60, 60, '', imagepath('next_focus'), imagepath('next_no_focus'))
        self.addControl(self.btn_right)
        self.btn_right.setAnimations([('WindowOpen', 'effect=slide start=60,0 end=0,0 delay=100 time=200'),('WindowClose', 'effect=slide start=0,0 end=60,0 delay=100 time=200')])

        self.count = 0

    def onAction(self, action):
        if action == ACTION_PREVIOUS_MENU or action == ACTION_GESTURE_SWIPE_LEFT or action == 110 or action == 92:
            self.close()

        if action == ACTION_MOVE_RIGHT or action == ACTION_MOVE_DOWN:
            self.count += 1
            if self.count > len(self.image_list) -1: self.count = 0
            self.main_image.setImage(self.image_list[self.count])

        if action == ACTION_MOVE_LEFT or action == ACTION_MOVE_UP:
            self.count -= 1
            if self.count < 0: self.count = len(self.image_list) -1
            self.main_image.setImage(self.image_list[self.count])


    def onControl(self, control):
        if control == self.btn_right:
            self.count += 1
            if self.count > len(self.image_list) -1: self.count = 0
            self.main_image.setImage(self.image_list[self.count])

        if control == self.btn_left:
            self.count -= 1
            if self.count < 0: self.count = len(self.image_list) -1
            self.main_image.setImage(self.image_list[self.count])


class Trailer(xbmcgui.WindowXMLDialog):
    def Start(self, item, trailers):
        self.item = item
        from specials import trailertools
        self.video_url, self.windows = trailertools.buscartrailer(self.item.clone(), trailers=trailers)
        self.doModal()

    def onInit(self):
        #### Kodi 18  Compatibility####
        if config.get_platform(True)['num_version'] < 18: self.setCoordinateResolution(0)

        if not self.video_url:
            platformtools.dialog_notification(config.get_localized_string(60507), config.get_localized_string(60508), 2)
            self.close()
        elif self.video_url == "no_video":
            self.close()
        else:
            new_video = False
            while True:
                if new_video: self.doModal()
                xlistitem = xbmcgui.ListItem(path=self.video_url, thumbnailImage=self.item.thumbnail)
                pl = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
                pl.clear()
                pl.add(self.video_url, xlistitem)
                self.player = xbmc.Player()
                self.player.play(pl, windowed=True)
                while xbmc.Player().isPlaying(): xbmc.sleep(1000)
                self.close()
                self.video_url = None
                new_video = True
                self.windows[-1].doModal()
                try:
                    self.video_url = self.windows[-1].result
                    if not self.video_url: break
                except:
                    break

    def onAction(self, action):
        if action == ACTION_PREVIOUS_MENU or action == ACTION_GESTURE_SWIPE_LEFT or action == 110 or action == 92:
            self.player.stop()
            self.close()

        elif action == ACTION_MOVE_LEFT: xbmc.executebuiltin('PlayerControl(Rewind)')
        elif action == ACTION_MOVE_RIGHT: xbmc.executebuiltin('PlayerControl(Forward)')
        elif action == ACTION_SELECT_ITEM: xbmc.executebuiltin('PlayerControl(Play)')
        elif action == 199 or action == ACTION_SHOW_FULLSCREEN or action == 9: xbmc.log("tuprimalafachaaa")
        if action == 13: self.close()


def get_recomendations(item, infoLabels, recommendations):
    Type = item.contentType
    if Type != "movie": Type = "tv"
    search = {'url': '%s/%s/recommendations' % (Type, infoLabels['tmdb_id']), 'language': def_lang, 'page': 1}
    reco_tmdb = tmdb.Tmdb(discover=search, tipo=Type, idioma_Search=def_lang)

    for i in range(0, len(reco_tmdb.results)):
        Title = reco_tmdb.results[i].get("title", reco_tmdb.results[i].get("original_title", ""))
        if not Title: Title = reco_tmdb.results[i].get("name", reco_tmdb.results[i].get("original_name", ""))
        idtmdb = str(reco_tmdb.results[i].get("id"))
        thumbnail = reco_tmdb.results[i].get("poster_path", "")
        if thumbnail: thumbnail = 'http://image.tmdb.org/t/p/original' + thumbnail
        recommendations.append([idtmdb, Title, thumbnail])


def get_fonts(skin):
    data_font = ""
    fonts = {}
    if "confluence" in skin or "estuary" in skin or "refocus" in skin: fonts = {"10": "font10", "12": "font12", "16": "font16", "24": "font24_title", "30": "font30"}
    elif "aeonmq" in skin: fonts = {"10": "font_14", "12": "font_16", "16": "font_20", "24": "font_24", "30": "font_30"}
    elif "madnox" in skin: fonts = {"10": "Font_Reg22", "12": "Font_Reg26", "16": "Font_Reg32", "24": "Font_Reg38", "30": "Font_ShowcaseMainLabel2_Caps"}

    if not fonts:
        from core import filetools
        try:
            data_font = filetools.read(xbmc.translatePath(filetools.join('special://skin/1080i', 'Font.xml')), "r")
        except:
            try: data_font = filetools.read(xbmc.translatePath(filetools.join('special://skin/720p', 'Font.xml')), "r")
            except: pass

    if data_font:
        fuentes = scrapertools.find_multiple_matches(data_font, r"<name>([^<]+)<\/name>(?:<![^<]+>|)\s*<filename>[^<]+<\/filename>\s*<size>(\d+)<\/size>")
        sizes = []
        try:
            for name, size in fuentes:
                size = int(size)
                sizes.append([size, name])
            sizes.sort()
            fonts["10"] = sizes[0][1].lower()
            check = False
            if not 12 in sizes:
                for size, name in sizes:
                    if size != fonts["10"]:
                        fonts["12"] = name.lower()
                        check = True
                        break
            for size, name in sizes:
                if size == 12 and not check: fonts["12"] = name.lower()
                elif size == 16:
                    fonts["16"] = name.lower()
                elif size == 24:
                    fonts["24"] = name.lower()
                elif size == 30:
                    fonts["30"] = name.lower()
                    break
                elif size > 30 and size <= 33:
                    fonts["30"] = name.lower()
                    break
        except:
            pass
    if not fonts:
        fonts = {"10": "font10", "12": "font12", "16": "font16", "24": "font24", "30": "font30"}

    return fonts


def imagepath(image):
    if len(image.split('.')) == 1: image += '.png'
    path = filetools.join(config.get_runtime_path(), 'resources', 'skins' , 'Default', 'media', 'Infoplus', image)
    return path


def search_type(self, channel=''):
    if channel:
        try:
            channel = self.item.from_channel
            if not channel: channel = self.item.channel
            channel_obj = __import__('channels.%s' % channel, None, None, ["channels.%s" % channel])
            itemlist = channel_obj.search(self.item.clone(channel=channel), self.infoLabels.get("title"))
            if not itemlist and self.infoLabels.get("originaltitle"): itemlist = channel_obj.search(self.item.clone(), self.infoLabels.get("originaltitle", ""))
        except:
            import traceback
            logger.error(traceback.format_exc())
    else:
        itemlist = globalSearch(self.item, self.infoLabels)
        if len(itemlist) == 0 and self.infoLabels.get("originaltitle"):
            itemlist = globalSearch(self.item, self.infoLabels, org_title=True)
    return itemlist