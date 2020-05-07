# -*- coding: utf-8 -*-

import re, os, sys

# from builtins import str
from builtins import range

PY3 = False
VFS = True
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int; VFS = False

if PY3:
    import urllib.parse as urllib
else:
    import urllib

import time, requests, xbmc, xbmcgui, xbmcaddon, shutil
from core import filetools, jsontools
from core.support import dbg, log, match
# from core import httptools
# from core import scrapertools
from platformcode import config, platformtools
from threading import Thread, currentThread
from torrentool.api import Torrent
from lib.guessit import guessit
try:
    elementum_setting = xbmcaddon.Addon(id='plugin.video.elementum')
    elementum_host = 'http://127.0.0.1:' + elementum_setting.getSetting('remote_port') + '/torrents/'
    TorrentPath = xbmc.translatePath(elementum_setting.getSetting('torrents_path'))
except:
    pass
extensions_list = ['.aaf', '.3gp', '.asf', '.avi', '.flv', '.mpeg', '.m1v', '.m2v', '.m4v', '.mkv', '.mov', '.mpg', '.mpe', '.mp4', '.ogg', '.wmv']



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
    elementum = False
    while not elementum:
        try:
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
            elementum = True
            path = filetools.join(config.get_data_path(),'elementum_torrent.txt')
            url = urllib.quote_plus(item.url)
            filetools.write(path, url)
        except:
            pass


# def stop_elementum_monitor():
#     config.set_setting('stop_elementum_monitor', True)
#     time.sleep(2)

# def start_elementum_monitor():
#     config.set_setting('stop_elementum_monitor', False)
#     time.sleep(3)
#     Thread(target=elementum_monitor).start()



def elementum_monitor():
    log('Start Elementum Monitor')
    path = filetools.join(config.get_data_path(),'elementum_torrent.txt')
    partials = []
    while True:
        try:
            if filetools.isfile(path):
                log('Add Torrent')
                url = filetools.read(path)
                if url.startswith('/'):
                    requests.get(elementum_host + url)
                    wait = False
                else:
                    TorrentName = match(url, patron=r'btih(?::|%3A)([^&%]+)', string=True).match
                    uri = elementum_host  + 'add'
                    post = 'uri=%s&file=null&all=1' % url
                    match(uri, post=post, timeout=5, alfa_s=True, ignore_response_code=True)
                    wait = True
                filetools.remove(path)
                if wait:
                    while not filetools.isfile(filetools.join(elementum_setting.getSetting('torrents_path'), TorrentName + '.torrent')):
                        time.sleep(1)
            else:
                log('Watch')
                try:
                    data = requests.get(elementum_host).json()
                except:
                    data = ''
                if data:
                    json = data['items']

                    for it in json:
                        Partial = float(match(it['label'], patron=r'(\d+\.\d+)%').match)
                        Title = it['info']['title']
                        TorrentName = match(it['path'], patron=r'resume=([^&]+)').match
                        File, Json = find_file(TorrentName)
                        update_download_info(Partial, Title, TorrentName, File, Json)
                        partials.append(Partial)

                partials.sort()
                if len(partials) > 0 and partials[0] == 100:
                    unset_elementum()

                time.sleep(1)
        except:
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

    if 'TorrentName' not in Json:
        jsontools.update_node(TorrentName, File, 'TorrentName', path, silent=True)
    if Json['downloadSize'] == 0:
        size = Torrent.from_file(filetools.join(TorrentPath, TorrentName + '.torrent')).total_size
        jsontools.update_node(size, File, 'downloadSize', path, silent=True)
    if Json['downloadFilename'] != dlpath and 'backupFilename' not in Json:
        jsontools.update_node(Json['downloadFilename'], File, 'backupFilename', path, silent=True)
        jsontools.update_node(dlpath, File, 'downloadFilename', path, silent=True)
    if Json['downloadProgress'] != Partial and Partial != 0:
        jsontools.update_node(Partial, File, 'downloadProgress', path, silent=True)
        jsontools.update_node(4, File, 'downloadStatus', path, silent=True)
        if Partial == 100:
            jsontools.update_node(Json['downloadSize'], File, 'downloadCompleted', path, silent=True)
            jsontools.update_node(2, File, 'downloadStatus', path, silent=True)
            requests.get(elementum_host + 'pause/' + TorrentName)
            del_torrent(TorrentName)
            time.sleep(1)
            rename(TorrentName, path)
            # requests.get(elementum_host + 'delete/' + TorrentName + '?files=false')

def del_torrent(TorrentName):
    filetools.remove(filetools.join(TorrentPath, TorrentName + '.torrent'))


def rename(TorrentName, Path):
    # dbg()
    File, Json = find_file(TorrentName)
    path = Json['downloadFilename']
    if Json['infoLabels']['mediatype'] == 'movie':
        if filetools.isdir(path):
            extension = ''
            files = filetools.listdir(path)
            sep = '/' if path.lower().startswith("smb://") else os.sep
            oldName = path.split(sep)[-1]
            newName = Json['backupFilename']
            for f in files:
                ext = os.path.splitext(f)[-1]
                if ext in extensions_list: extension = ext
                filetools.rename(filetools.join(path, f), f.replace(oldName, newName))
            filetools.rename(path, newName)
            jsontools.update_node(filetools.join(newName, newName + extension), File, 'downloadFilename', Path)

        else:
            oldName = filetools.split(path)[-1]
            newName = Json['backupFilename'] + os.path.splitext(oldName)[-1]
            filetools.rename(path, newName)
            jsontools.update_node(newName, File, 'downloadFilename', Path)
    else:
        sep = '/' if path.lower().startswith("smb://") else os.sep
        FolderName = Json['backupFilename'].split(sep)[0]
        Title = re.sub(r'(\s*\[[^\]]+\])', '', FolderName)
        if filetools.isdir(path):
            files = filetools.listdir(path)
            file_dict = {}
            for f in files:
                title = process_filename(f, Title, ext=False)
                ext = os.path.splitext(f)[-1]
                name = os.path.splitext(f)[0]
                if title not in file_dict and ext in extensions_list:
                    file_dict[title] = name

            for title, name in file_dict.items():
                for f in files:
                    if name in f:
                        # log('Name:',name,'Title:',title)
                        filetools.rename(filetools.join(path, f), f.replace(name, title))

            filetools.rename(path, FolderName)
            jsontools.update_node(FolderName, File, 'downloadFilename', Path)
        else:
            filename = filetools.split(path)[-1]
            title = process_filename(filename, Title)
            NewFolder = filetools.join(config.get_setting('downloadpath'), FolderName)
            if not filetools.isdir(NewFolder):
                filetools.mkdir(NewFolder)
            from_folder = filetools.join(config.get_setting('downloadpath'), filename)
            to_folder = filetools.join(config.get_setting('downloadpath'), FolderName, title)
            filetools.move(from_folder, to_folder)
            jsontools.update_node(filetools.join(FolderName, title), File, 'downloadFilename', Path)

def process_filename(filename, Title, ext=True):
    extension = os.path.splitext(filename)[-1]
    parsedTitle = guessit(filename)
    t = parsedTitle.get('title', '')
    episode = ''
    s = ' - '
    if parsedTitle.get('episode') and parsedTitle.get('season'):
        if type(parsedTitle.get('season')) == list:
            episode += str(parsedTitle.get('season')[0]) + '-' + str(parsedTitle.get('season')[-1])
        else:
            episode += str(parsedTitle.get('season'))

        if type(parsedTitle.get('episode')) == list:
                episode += 'x' + str(parsedTitle.get('episode')[0]).zfill(2) + '-' + str(parsedTitle.get('episode')[-1]).zfill(2)
        else:
            episode += 'x' + str(parsedTitle.get('episode')).zfill(2)
    elif parsedTitle.get('season') and type(parsedTitle.get('season')) == list:
        episode += s + config.get_localized_string(30140) + " " +str(parsedTitle.get('season')[0]) + '-' + str(parsedTitle.get('season')[-1])
    elif parsedTitle.get('season'):
        episode += s + config.get_localized_string(60027) % str(parsedTitle.get('season'))
    if parsedTitle.get('episode_title'):
        episode += s + parsedTitle.get('episode_title')
    title = (t if t else Title) + s + episode + (extension if ext else '')
    return title

def unset_elementum():
    log('UNSET Elementum')
    Sleep = False
    if config.get_setting('elementumtype') and config.get_setting('elementumtype') != elementum_setting.gerSetting('download_storage'):
        elementum_setting.setSetting('download_storage', str(config.get_setting('elementumtype')))
        Sleep = True
    if config.get_setting('elementumdl') and config.get_setting('elementumdl') != elementum_setting.gerSetting('download_path'):
        elementum_setting.setSetting('download_path', config.get_setting('elementumdl'))
        Sleep = True
    if Sleep:
        time.sleep(1)

##########################  ELEMENTUM MONITOR TEST ##########################
