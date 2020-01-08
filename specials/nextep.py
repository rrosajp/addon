# -*- coding: utf-8 -*-
import xbmc, os, urlparse
from platformcode import config, platformtools, logger
from time import time, sleep
from core import scrapertools
from core import jsontools, filetools


def afther_stop(item):
    condition = config.get_setting('next_ep')

    if condition == 1: # Hide servers afther stop video
        while not platformtools.is_playing():
            pass
        while platformtools.is_playing():
            pass
        sleep(0.5)
        xbmc.executebuiltin('Action(Back)')

    elif condition == 2: # Bring servers afther stop video
        from platformcode.launcher import play_from_library
        # Check if next episode exist
        current_filename = os.path.basename(item.strm_path)
        path = filetools.join(config.get_videolibrary_path(), config.get_setting("folder_tvshows"),os.path.dirname(item.strm_path))
        fileList = []
        for file in os.listdir(path):
            if file.endswith('.strm'):
                fileList.append(file)
        nextIndex = fileList.index(current_filename) + 1
        if nextIndex == 0 or nextIndex == len(fileList):
            next_file = None
        else:
            next_file = fileList[nextIndex]

        # start next episode window afther x time
        if next_file:
            play_next = False
            time_limit = time() + 30
            TimeFromEnd = congig.get_setting('next_ep_seconds')
            while not platformtools.is_playing() and time() < time_limit:
                sleep(1)
            while platformtools.is_playing() and play_next == False:
                Difference = xbmc.Player().getTotalTime() - xbmc.Player().getTime()
                if 0 < Difference <= 60:
                    logger.info('Exit '+str(Difference))
                    play_next = True

            if play_next:
                play_next = False
                season_ep = next_file.split('.')[0]
                season = season_ep.split('x')[0]
                episode = season_ep.split('x')[1]
                next_ep = '%sx%s' % (season, episode)
                item.contentSeason = item.infoLabels['season'] = season
                item.contentEpisodeNumber = item.infoLabels['episode'] = episode
                item.contentTitle = item.infoLabels['title'] = next_ep
                item.strm_path = filetools.join(os.path.dirname(item.strm_path), next_file)
                # from core.support import dbg; dbg()

                global ITEM
                ITEM = item
                nextDialog = NextDialog('NextDialog.xml', config.get_runtime_path())
                nextDialog.show()
                while platformtools.is_playing() and not nextDialog.is_still_watching():
                    xbmc.sleep(100)
                    pass

                nextDialog.close()
                logger.info('CONTINUA: ' +str(nextDialog.stillwatching))

                if nextDialog.stillwatching or nextDialog.continuewatching:
                    xbmc.Player().stop()
                    sleep(0.5)
                    xbmc.executebuiltin('Action(Back)')
                    sleep(0.5)
                    play_from_library(item)
                else:
                    sleep(0.5)
                    xbmc.executebuiltin('Action(Back)')


import xbmcgui

PLAYER_STOP = 13


class NextDialog(xbmcgui.WindowXMLDialog):
    item = None
    cancel = False
    stillwatching = False
    continuewatching = True

    def __init__(self, *args, **kwargs):
        logger.info()
        self.action_exitkeys_id = [10, 13]
        self.progress_control = None
        self.item = ITEM

    def set_still_watching(self, stillwatching):
        self.stillwatching = stillwatching

    def set_continue_watching(self, continuewatching):
        self.continuewatching = continuewatching

    def is_still_watching(self):
        return self.stillwatching

    def onFocus(self, controlId):
        pass

    def doAction(self):
        pass

    def closeDialog(self):
        self.close()

    def onClick(self, controlId):
        if controlId == 3012:  # Still watching
            self.set_still_watching(True)
            self.set_continue_watching(False)
            self.close()
        elif controlId == 3013:  # Cancel
            self.set_continue_watching(False)
            self.close()

    def onAction(self, action):
        logger.info()
        if action == PLAYER_STOP:
            self.set_continue_watching(False)
            self.close()
