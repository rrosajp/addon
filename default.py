# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# XBMC entry point
# ------------------------------------------------------------

import os
import sys

import xbmc
from platformcode import config, logger

logger.info("init...")

librerias = xbmc.translatePath(os.path.join(config.get_runtime_path(), 'lib'))
sys.path.append(librerias)

if not config.dev_mode():
    from platformcode import updater
    updater.showSavedChangelog()

from platformcode import launcher

if sys.argv[2] == "":
    launcher.start()
    launcher.run()
else:
    launcher.run()
