# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# XBMC entry point
# ------------------------------------------------------------


import os
import sys

import xbmc
from platformcode import config, logger
import platform
android = 'ANDROID' if 'ANDROID_STORAGE ' in os.environ else ''
info = 'OS NAME= '+ android + str(os.name) + ' ' + str(platform.system()) + ' ' + str(platform.release()) + ' | KODI VER.= ' + str(config.get_platform(True)['num_version'])
xbmc.log(info, xbmc.LOGNOTICE)


logger.info("init...")
if os.path.isfile(os.path.join(config.get_data_path(), 'alfavorites-default.json')) == True and os.path.isfile(os.path.join(config.get_data_path(), 'kodfavorites-default.json')) == False:
    os.rename(os.path.join(config.get_data_path(), 'alfavorites-default.json'), os.path.join(config.get_data_path(), 'kodfavorites-default.json'))
if os.path.isfile(os.path.join(config.get_data_path(), 'alfa_db.sqlite')) == True and os.path.isfile(os.path.join(config.get_data_path(), 'kod_db.sqlite')) == False:
    os.rename(os.path.join(config.get_data_path(), 'alfa_db.sqlite'), os.path.join(config.get_data_path(), 'kod_db.sqlite'))

librerias = xbmc.translatePath(os.path.join(config.get_runtime_path(), 'lib'))
sys.path.append(librerias)


from platformcode import launcher

if sys.argv[2] == "":
    launcher.start()
    launcher.run()
else:
    launcher.run()
