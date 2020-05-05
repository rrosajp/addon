# -*- coding: utf-8 -*-

import os, sys

# from builtins import str
from builtins import range

PY3 = False
VFS = True
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int; VFS = False

if PY3:
    import urllib.parse as urllib
else:
    import urllib

import time, requests, xbmc, xbmcgui, xbmcaddon
from core import filetools, jsontools
from core.support import dbg, log, match
# from core import httptools
# from core import scrapertools
from platformcode import config, platformtools
from threading import Thread, currentThread
from torrentool.api import Torrent

elementum_setting = xbmcaddon.Addon(id='plugin.video.elementum')
elementum_host = 'http://127.0.0.1:' + elementum_setting.getSetting('remote_port') + '/torrents/'
extensions_list = ['aaf', '3gp', 'asf', 'avi', 'flv', 'mpeg', 'm1v', 'm2v', 'm4v', 'mkv', 'mov', 'mpg', 'mpe', 'mp4', 'ogg', 'wmv']


# Returns an array of possible video url's from the page_url
def get_video_url(page_url, premium=False, user='', password='', video_password=''):
    torrent_options = platformtools.torrent_client_installed(show_tuple=True)
    if len(torrent_options) == 0:
        from specials import elementum_download
        elementum_download.download()
    log('server=torrent, the url is the good')

    if page_url.startswith('magnet:'):
        video_urls = [['magnet: [torrent]', page_url]]
    else:
        video_urls = [['.torrent [torrent]', page_url]]

    return video_urls


class XBMCPlayer(xbmc.Player):

    def __init__(self, *args):
        pass

xbmc_player = XBMCPlayer()

def mark_auto_as_watched(item):

    time_limit = time.time() + 150
    while not platformtools.is_playing() and time.time() < time_limit:
        time.sleep(5)
    if item.subtitle:
        time.sleep(5)
        xbmc_player.setSubtitles(item.subtitle)

    if item.strm_path and platformtools.is_playing():
        from platformcode import xbmc_videolibrary
        xbmc_videolibrary.mark_auto_as_watched(item)


##########################  ELEMENTUM MONITOR TEST ##########################

elementumHost = 'http://127.0.0.1:65220/torrents/'

def elementum_download(item):
    sleep = False
    if elementum_setting.getSetting('logger_silent') == False:
        elementum_setting.setSetting('logger_silent', 'true') 
        sleep = True
    if elementum_setting.getSetting('download_storage') != 0:
        config.set_setting('elementumtype', elementum_setting.getSetting('download_storage'))    # Backup Setting
        elementum_setting.setSetting('download_storage', '0')                                    # Set Setting
        sleep = True
    if elementum_setting.getSetting('download_path') != config.get_setting('downloadpath'):
        elementum_setting.setSetting('download_path', config.get_setting('downloadpath'))        # Backup Setting
        config.set_setting('elementumdl', elementum_setting.getSetting('download_path'))         # Set Setting
        sleep = True
    if sleep: time.sleep(3)

    path = filetools.join(config.get_data_path(),'elementum_torrent.txt')
    url = urllib.quote_plus(item.url)
    filetools.write(path, url)


def stop_elementum_monitor():
    config.set_setting('stop_elementum_monitor', True)
    time.sleep(2)

def start_elementum_monitor():
    config.set_setting('stop_elementum_monitor', False)
    time.sleep(3)
    Thread(target=elementum_monitor).start()



def elementum_monitor():
    log('Start Elementum Monitor')
    path = filetools.join(config.get_data_path(),'elementum_torrent.txt')
    partials = []
    while True:
        if filetools.isfile(path):
            log('Add Torrent')
            url = filetools.read(path)
            TorrentName = match(url, patron=r'btih(?::|%3A)([^&%]+)', string=True).match
            uri = elementum_host  + 'add'
            post = 'uri=%s&file=null&all=1' % url
            match(uri, post=post, timeout=5, alfa_s=True, ignore_response_code=True)
            filetools.remove(path)
            while not filetools.isfile(filetools.join(elementum_setting.getSetting('torrents_path'), TorrentName + '.torrent')):
                time.sleep(1)
        else:
            data = match(elementum_host, alfa_s=True).data
            if data:
                json = jsontools.load(data)['items']

                for it in json:
                    Partial = float(match(it['label'], patron=r'(\d+\.\d+)%').match)
                    Title = it['info']['title']
                    TorrentName = match(it['path'], patron=r'resume=([^&]+)').match
                    File, Json = find_file(TorrentName)
                    update_download_info(Partial, Title, TorrentName, File, Json)
                    partials.append(Partial)

            result = 0
            for p in partials:
                result += p

            if result / len(partials) == 100:
                unset_elementum()

            time.sleep(1)


def find_file(File):
    path = xbmc.translatePath(config.get_setting('downloadlistpath'))
    files = filetools.listdir(path)
    # dbg()
    for f in files:
        filepath = filetools.join(path, f)
        json = jsontools.load(filetools.read(filepath))
        if ('downloadServer' in json and 'url' in json['downloadServer'] and File in json['downloadServer']['url']) or ('url' in json and File in json['url']):
            break
    return filetools.split(filepath)[-1], json


def update_download_info(Partial, Title, TorrentName, File, Json):
    path = xbmc.translatePath(config.get_setting('downloadlistpath'))
    dlpath = filetools.join(config.get_setting('downloadpath'), Title)
    tpath = filetools.join(xbmc.translatePath(elementum_setting.getSetting('torrents_path')), TorrentName)
    if Json['downloadSize'] == 0:
        size = Torrent.from_file(tpath + '.torrent').total_size
        jsontools.update_node(size, File, 'downloadSize', path)
    if Json['downloadFilename'] != dlpath and 'backupFilename' not in Json:
        jsontools.update_node(Json['downloadFilename'], File, 'backupFilename', path)
        jsontools.update_node(dlpath, File, 'downloadFilename', path)
    if Json['downloadProgress'] != Partial and Partial != 0:
        jsontools.update_node(Partial, File, 'downloadProgress', path)
        jsontools.update_node(4, File, 'downloadStatus', path)
        if Partial == 100:
            jsontools.update_node(Json['downloadSize'], File, 'downloadCompleted', path)
            jsontools.update_node(2, File, 'downloadStatus', path)
            requests.get(elementum_host + 'pause/' + TorrentName)
            filetools.remove(tpath + '.torrent')
            time.sleep(5)
            rename(TorrentName, path)


def rename(TorrentName, Path):
    File, Json = find_file(TorrentName)
    path = Json['downloadFilename']
    if filetools.isdir(path):
        extension = ''
        files = filetools.listdir(path)
        sep = '/' if path.lower().startswith("smb://") else os.sep
        oldName = path.split(sep)[-1]
        newName = Json['backupFilename']
        for f in files:
            ext = f.split('.')[-1]
            if ext in extensions_list: extension = '.' + ext
            filetools.rename(filetools.join(path, f), f.replace(oldName, newName))
        filetools.rename(path, newName)
        jsontools.update_node(filetools.join(newName,newName + extension), File, 'downloadFilename', Path)

    else:
        oldName = filetools.split(path)[-1]
        newName = Json['backupFilename'] + '.' + oldName.split('.')[-1]
        filetools.rename(path, newName)
        jsontools.update_node(newName, File, 'downloadFilename', Path)


def unset_elementum():
    log('UNSET Elementum')
    Sleep = False
    if config.get_setting('elementumtype'):
        elementum_setting.setSetting('download_storage', str(config.get_setting('elementumtype')))
        Sleep = True
    if config.get_setting('elementumdl'):
        elementum_setting.setSetting('download_path', config.get_setting('elementumdl'))
        Sleep = True
    if Sleep:
        time.sleep(3)

##########################  ELEMENTUM MONITOR TEST ##########################
