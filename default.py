# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# XBMC entry point
# ------------------------------------------------------------

import os
import sys

import xbmc
from platformcode import config, logger
import ssl
logger.info(ssl.OPENSSL_VERSION)

logger.info("init...")

librerias = xbmc.translatePath(os.path.join(config.get_runtime_path(), 'lib'))
sys.path.insert(0, librerias)


from platformcode import launcher

if sys.argv[2] == "":
    launcher.start()
    launcher.run()
else:
    launcher.run()
