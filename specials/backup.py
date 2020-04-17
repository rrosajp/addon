# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Backup and restore video library
# ------------------------------------------------------------

import os, datetime

import xbmc

from core import ziptools, videolibrarytools, filetools
from platformcode import logger, config, platformtools, xbmc_videolibrary
from distutils.dir_util import copy_tree

temp_path = xbmc.translatePath("special://userdata/addon_data/plugin.video.kod/temp/")
movies_path = os.path.join(temp_path, "movies")
tvshows_path = os.path.join(temp_path, "tvshows")


def export_videolibrary(item):
    logger.info()

    zip_file_folder = platformtools.dialog_browse(3, config.get_localized_string(80002))
    if zip_file_folder == "":
        return
    zip_file = xbmc.translatePath(zip_file_folder + "KoD_video_library-" + str(datetime.date.today()) + ".zip")

    p_dialog = platformtools.dialog_progress_bg(config.get_localized_string(20000), config.get_localized_string(80003))
    p_dialog.update(0)

    if filetools.exists(temp_path):
        filetools.rmdirtree(temp_path)
    filetools.mkdir(temp_path)
    p_dialog.update(25)
    filetools.mkdir(movies_path)
    copy_tree(videolibrarytools.MOVIES_PATH, movies_path)
    p_dialog.update(50)
    filetools.mkdir(tvshows_path)
    copy_tree(videolibrarytools.TVSHOWS_PATH, tvshows_path)
    p_dialog.update(75)

    zipper = ziptools.ziptools()
    zipper.zip(temp_path, zip_file)

    filetools.rmdirtree(temp_path)

    p_dialog.update(100)
    xbmc.sleep(1000)
    p_dialog.close()
    platformtools.dialog_notification(config.get_localized_string(20000), config.get_localized_string(80004), icon=0, time=5000, sound=False)


def import_videolibrary(item):
    logger.info()

    zip_file = platformtools.dialog_browse(1, config.get_localized_string(80005))
    if zip_file == "":
        return
    if not platformtools.dialog_yesno(config.get_localized_string(20000), config.get_localized_string(80006)):
        return

    p_dialog = platformtools.dialog_progress_bg(config.get_localized_string(20000), config.get_localized_string(80007))
    p_dialog.update(0)

    if filetools.exists(temp_path):
        filetools.rmdirtree(temp_path)
    filetools.mkdir(temp_path)

    unzipper = ziptools.ziptools()
    unzipper.extract(zip_file, temp_path)
    p_dialog.update(25)

    filetools.rmdirtree(videolibrarytools.MOVIES_PATH)
    filetools.rmdirtree(videolibrarytools.TVSHOWS_PATH)
    p_dialog.update(50)
    if config.is_xbmc() and config.get_setting("videolibrary_kodi"):
        strm_list = []
        strm_list.append(config.get_setting('videolibrarypath'))
        xbmc_videolibrary.clean(strm_list)

    config.verify_directories_created()
    if filetools.exists(movies_path):
        copy_tree(movies_path, videolibrarytools.MOVIES_PATH)
    p_dialog.update(70)
    if filetools.exists(tvshows_path):
        copy_tree(tvshows_path, videolibrarytools.TVSHOWS_PATH)
    p_dialog.update(90)
    filetools.rmdirtree(temp_path)

    p_dialog.update(100)
    xbmc.sleep(1000)
    p_dialog.close()
    platformtools.dialog_notification(config.get_localized_string(20000), config.get_localized_string(80008), icon=0, time=5000, sound=False)

    if platformtools.dialog_yesno(config.get_localized_string(20000), config.get_localized_string(80009)):
        import service
        service.check_for_update(overwrite=True)

    if config.is_xbmc() and config.get_setting("videolibrary_kodi"):
        xbmc_videolibrary.update()
