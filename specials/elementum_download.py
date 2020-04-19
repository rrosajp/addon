
from core import filetools, downloadtools, support
from platformcode import config, platformtools, updater
from time import sleep

import xbmc, xbmcaddon, os, sys, platform

host = 'https://github.com'
elementum_url = host + '/elgatito/plugin.video.elementum/releases'
filename = filetools.join(config.get_data_path(),'elementum.zip')
addon_path = xbmc.translatePath("special://home/addons/")
elementum_path = filetools.join(addon_path,'plugin.video.elementum')


def download(item=None):
    if filetools.exists(elementum_path):
        xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id":1, "method": "Addons.SetAddonEnabled", "params": { "addonid": "plugin.video.elementum", "enabled": false }}')
        sleep(1)
        filetools.rmdirtree(elementum_path)

    if filetools.exists(filename):
        filetools.remove(filename)
        return download()
    else:
        platform = get_platform()
        support.log('OS:', platform)
        support.log('Extract IN:', elementum_path)
        url = support.match(elementum_url, patronBlock=r'<div class="release-entry">(.*?)<!-- /.release-body -->', patron=r'<a href="([a-zA-Z0-9/\.-]+%s.zip)' % platform).match
        support.log('URL:', url)
        if url:
            downloadtools.downloadfile(host + url, filename)
            extract()

def extract():
    import zipfile
    support.log('Estraggo Elementum in:', elementum_path)
    with zipfile.ZipFile(filename, 'r') as zip_ref:
        zip_ref.extractall(xbmc.translatePath("special://home/addons/"))

    xbmc.executebuiltin('UpdateLocalAddons')
    if platformtools.dialog_ok('Elementum', config.get_localized_string(70783)):
        if filetools.exists(filename):
            filetools.remove(filename)
        xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id":1, "method": "Addons.SetAddonEnabled", "params": { "addonid": "plugin.video.elementum", "enabled": true }}')
        xbmc.executebuiltin('UpdateLocalAddons')
        updater.refreshLang()

        elementum_settings = filetools.join(config.get_data_path().replace('kod','elementum'),'settings.xml')
        if filetools.isfile(elementum_settings):
            xbmcaddon.Addon(id="plugin.video.elementum").setSetting('skip_burst_search',True)
            xbmcaddon.Addon(id="plugin.video.elementum").setSetting('greeting_enabled',False)
            xbmcaddon.Addon(id="plugin.video.elementum").setSetting('do_not_disturb',True)
        else:
            settings_file = filetools.join(config.get_runtime_path(), 'resources', 'settings', 'elementum', 'settings.xml')
            filetools.copy(settings_file, elementum_settings)



def get_platform():
    build = xbmc.getInfoLabel("System.BuildVersion")
    kodi_version = int(build.split()[0][:2])
    ret = {
        "auto_arch": sys.maxsize > 2 ** 32 and "64-bit" or "32-bit",
        "arch": sys.maxsize > 2 ** 32 and "x64" or "x86",
        "os": "",
        "version": platform.release(),
        "kodi": kodi_version,
        "build": build
    }
    if xbmc.getCondVisibility("system.platform.android"):
        ret["os"] = "android"
        if "arm" in platform.machine() or "aarch" in platform.machine():
            ret["arch"] = "arm"
            if "64" in platform.machine() and ret["auto_arch"] == "64-bit":
                ret["arch"] = "arm"
                ret["arch"] = "x64"
    elif xbmc.getCondVisibility("system.platform.linux"):
        ret["os"] = "linux"
        if "aarch" in platform.machine() or "arm64" in platform.machine():
            if xbmc.getCondVisibility("system.platform.linux.raspberrypi"):
                ret["arch"] = "armv7"
            elif ret["auto_arch"] == "32-bit":
                ret["arch"] = "armv7"
            elif ret["auto_arch"] == "64-bit":
                ret["arch"] = "arm64"
            elif platform.architecture()[0].startswith("32"):
                ret["arch"] = "arm"
            else:
                ret["arch"] = "arm64"
        elif "armv7" in platform.machine():
            ret["arch"] = "armv7"
        elif "arm" in platform.machine():
            ret["arch"] = "arm"
    elif xbmc.getCondVisibility("system.platform.xbox"):
        ret["os"] = "windows"
        ret["arch"] = "x64"
    elif xbmc.getCondVisibility("system.platform.windows"):
        ret["os"] = "windows"
        if platform.machine().endswith('64'):
            ret["arch"] = "x64"
    elif xbmc.getCondVisibility("system.platform.osx"):
        ret["os"] = "darwin"
        ret["arch"] = "x64"
    elif xbmc.getCondVisibility("system.platform.ios"):
        ret["os"] = "ios"
        ret["arch"] = "arm"

    return ret['os'] + '_' + ret['arch']