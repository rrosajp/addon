# -*- coding: utf-8 -*-

from builtins import map
import sys, xbmc, xbmcaddon, xbmcgui, base64, json
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int
from threading import Timer

from channelselector import get_thumb
from platformcode import config, logger
import channelselector


class KeyListener(xbmcgui.WindowXMLDialog):
    TIMEOUT = 10

    def __new__(cls):
        gui_api = tuple(map(int, xbmcaddon.Addon('xbmc.gui').getAddonInfo('version').split('.')))
        if gui_api >= (5, 11, 0):
            filenname = "DialogNotification.xml"
        else:
            filenname = "DialogKaiToast.xml"
        return super(KeyListener, cls).__new__(cls, filenname, "")

    def __init__(self):
        self.key = None

    def onInit(self):
        try:
            self.getControl(401).addLabel(config.get_localized_string(70698))
            self.getControl(402).addLabel(config.get_localized_string(70699) % self.TIMEOUT)
        except AttributeError:
            self.getControl(401).setLabel(config.get_localized_string(70698))
            self.getControl(402).setLabel(config.get_localized_string(70699) % self.TIMEOUT)

    def onAction(self, action):
        code = action.getButtonCode()
        if code == 0:
            self.key = None
        else:
            self.key = str(code)
        self.close()

    @staticmethod
    def record_key():
        dialog = KeyListener()
        timeout = Timer(KeyListener.TIMEOUT, dialog.close)
        timeout.start()
        dialog.doModal()
        timeout.cancel()
        key = dialog.key
        del dialog
        return key


def set_key():
    saved_key = config.get_setting("shortcut_key")
    new_key = KeyListener().record_key()

    if new_key and saved_key != new_key:
        from core import filetools
        from platformcode import platformtools
        import xbmc
        file_xml = "special://profile/keymaps/kod.xml"
        data = '<keymap><global><keyboard><key id="%s">' % new_key + 'runplugin(plugin://plugin.video.kod/?ew0KICAgICJhY3Rpb24iOiAia2V5bWFwIiwNCiAgICAib3BlbiI6IHRydWUNCn0=)</key></keyboard></global></keymap>'
        filetools.write(xbmc.translatePath(file_xml), data)
        platformtools.dialog_notification(config.get_localized_string(70700),config.get_localized_string(70702))

        config.set_setting("shortcut_key", new_key)

    return

def delete_key():
    from core import filetools
    from platformcode import platformtools
    import xbmc

    file_xml = "special://profile/keymaps/kod.xml"
    filetools.write(xbmc.translatePath(file_xml), '')
    platformtools.dialog_notification(config.get_localized_string(70701),config.get_localized_string(70702))

    config.set_setting("shortcut_key", '')

MAIN_MENU = channelselector.getmainlist()

class Main(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.items = []

    def onInit(self):
        #### Compatibilidad con Kodi 18 ####
        if config.get_platform(True)['num_version'] < 18:
            self.setCoordinateResolution(2)

        for menuentry in MAIN_MENU:
            item = xbmcgui.ListItem(menuentry.title)
            item.setProperty("thumb", menuentry.thumbnail)
            action = {"channel" : menuentry.channel, "action" : menuentry.action}
            item.setProperty("action", base64.b64encode(json.dumps(action).encode()))
            self.items.append(item)

        self.getControl(32500).addItems(self.items)
        self.setFocusId(32500)

    def onClick(self, control_id):
        if control_id == 32500:
            action = self.getControl(32500).getSelectedItem().getProperty("action")
            xbmc.executebuiltin('Dialog.Close(all,true)')
            xbmc.executebuiltin('ActivateWindow(10025, "plugin://plugin.video.kod/?' + action + '")')



    def onAction(self, action):
        # exit
        if action.getId() in [xbmcgui.ACTION_PREVIOUS_MENU, xbmcgui.ACTION_NAV_BACK]:
            xbmc.executebuiltin('Dialog.Close(all,true)')

        if action.getId() == xbmcgui.ACTION_CONTEXT_MENU:
            config.open_settings()


def open_shortcut_menu():
    XML =  'ShortCutMenu.xml'
    if config.get_setting('icon_set') == 'dark':
        XML = 'Dark' + XML
    main = Main(XML, config.get_runtime_path())
    main.doModal()
    del main
