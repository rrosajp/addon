# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Backup and restore video library
# ------------------------------------------------------------

import os, datetime

import xbmc

from core import ziptools, videolibrarytools, filetools
from platformcode import logger, config, platformtools, xbmc_videolibrary
from distutils.dir_util import copy_tree

def export_videolibrary(item):
    logger.info()

    temp_path = xbmc.translatePath("special://userdata/addon_data/plugin.video.kod/temp/")
    movies_path = os.path.join(temp_path, "movies")
    tvshows_path = os.path.join(temp_path, "tvshows")

    zip_file_folder = platformtools.dialog_browse(3, config.get_localized_string(80002))
    if zip_file_folder == "":
        return
    zip_file = xbmc.translatePath(zip_file_folder + "KoD_video_library-" + str(datetime.date.today()) + ".zip")

    p_dialog = platformtools.dialog_progress_bg(config.get_localized_string(80003), config.get_localized_string(20000))
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
    xbmc.sleep(2000)
    p_dialog.close()
    platformtools.dialog_notification(config.get_localized_string(20000), config.get_localized_string(80004), icon=3, time=5000, sound=False)

def import_videolibrary(item):
    logger.info()

    zip_file = platformtools.dialog_browse(1, config.get_localized_string(80005))
    if zip_file == "":
        return
    if not platformtools.dialog_yesno(config.get_localized_string(20000), config.get_localized_string(80006)):
        return

    temp_path = xbmc.translatePath("special://userdata/addon_data/plugin.video.kod/temp/")

    p_dialog = platformtools.dialog_progress_bg(config.get_localized_string(80007), config.get_localized_string(20000))
    p_dialog.update(0)

    if filetools.exists(temp_path):
        filetools.rmdirtree(temp_path)
    filetools.mkdir(temp_path)

    unzipper = ziptools.ziptools()
    unzipper.extract(zip_file, temp_path)
    p_dialog.update(25)
		
    filetools.rmdirtree(videolibrarytools.VIDEOLIBRARY_PATH)
    p_dialog.update(50)
    if config.is_xbmc() and config.get_setting("videolibrary_kodi") == True:
        xbmc.sleep(5000)
        xbmc_videolibrary.clean()

    config.verify_directories_created()
    if filetools.exists(temp_path + "movies"):
        copy_tree(temp_path + "movies", videolibrarytools.MOVIES_PATH)
    p_dialog.update(70)
    if filetools.exists(temp_path + "tvshows"):
        copy_tree(temp_path + "tvshows", videolibrarytools.TVSHOWS_PATH)
    p_dialog.update(90)
    filetools.rmdirtree(temp_path)

    p_dialog.update(100)
    xbmc.sleep(2000)
    p_dialog.close()
    platformtools.dialog_notification(config.get_localized_string(20000), config.get_localized_string(80008), icon=3, time=5000, sound=False)

    if platformtools.dialog_yesno(config.get_localized_string(20000), config.get_localized_string(80009)):
        import videolibrary_service
        videolibrary_service.check_for_update(overwrite=True)

    if config.is_xbmc() and config.get_setting("videolibrary_kodi") == True:
        xbmc_videolibrary.update()