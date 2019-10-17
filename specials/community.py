# -*- coding: utf-8 -*-
# -*- Channel Community -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re, urllib, os
import requests

from core import httptools, scrapertoolsV2, servertools, jsontools, tmdb
from core.item import Item
from core.support import typo
from channelselector import get_thumb
from platformcode import logger, config, platformtools
from specials import autoplay


list_data = {}

list_language = ['ITA', 'SUB-ITA']
list_servers = ['directo', 'akvideo', 'verystream', 'openload']
list_quality = ['SD', '720', '1080', '4k']

def mainlist(item):
    logger.info()

    path = os.path.join(config.get_data_path(), 'community_channels.json')
    if not os.path.exists(path):
        with open(path, "w") as file:
            file.write('{"channels":{}}')
            file.close()
    autoplay.init(item.channel, list_servers, list_quality)

    return show_channels(item)


def show_channels(item):
    logger.info()
    itemlist = []

    context = [{"title": config.get_localized_string(50005),
                 "action": "remove_channel",
                 "channel": "community"}]

    path = os.path.join(config.get_data_path(), 'community_channels.json')
    file = open(path, "r")
    json = jsontools.load(file.read())

    itemlist.append(Item(channel=item.channel, title=typo(config.get_localized_string(70676),'bold color kod'), action='add_channel', thumbnail=get_thumb('add.png')))

    for key, channel in json['channels'].items():
        if 'http' in channel['path']: file_path = requests.get(channel['path']).url
        else: file_path = channel['path']
        path = os.path.dirname(os.path.abspath(file_path))
        if 'http' in path: path = path[path.find('http'):].replace('\\','/').replace(':/','://')
        if file_path.startswith('http'):
            file_url = httptools.downloadpage(file_path, follow_redirects=True).data
        else:
            file_url = open(file_path, "r").read()
        json_url = jsontools.load(file_url)
        thumbnail = json_url['thumbnail'] if 'thumbnail' in json_url and ':/' in json_url['thumbnail'] else path + json_url['thumbnail'] if 'thumbnail' in json_url and  '/' in json_url['thumbnail'] else ''
        fanart = json_url['fanart'] if 'fanart' in json_url and ':/' in json_url['fanart'] else path + json_url['fanart'] if 'fanart' in json_url and  '/' in json_url['fanart'] else ''
        plot = json_url['plot'] if 'plot' in json_url else ''

        itemlist.append(Item(channel=item.channel,
                             title=typo(channel['channel_name'],'bold'),
                             url=file_path,
                             thumbnail=thumbnail,
                             fanart=fanart,
                             plot=plot,
                             action='show_menu',
                             channel_id = key,
                             context=context,
                             path=path))
    return itemlist

def load_json(item):

    url= item if type(item) == str else item.url

    if url:
        if url.startswith('http'):
            json_file = httptools.downloadpage(url).data
        else:
            json_file = open(url, "r").read()

        json_data = jsontools.load(json_file)
    else:
        json_data = ''

    return json_data

def show_menu(item):
    global list_data
    itemlist = []
    logger.info()

    json_data = load_json(item)

    if "menu" in json_data:
        for option in json_data['menu']:
            if 'thumbnail' in json_data:
                thumbnail = option['thumbnail'] if ':/' in option['thumbnail'] else item.path + option['thumbnail'] if '/' in option['thumbnail'] else get_thumb(option['thumbnail'])
            else:
                thumbnail = ''
            if 'fanart' in option and option['fanart']:
                fanart = option['fanart'] if ':/' in option['fanart'] else item.path + option['fanart']
            else:
                fanart = item.fanart
            if 'plot' in option and option['plot']:
                plot = option['plot']
            else:
                plot = item.plot
            url = '' if not option['link'] else option['link'] if ':/' in option['link'] else item.path + option['link']
            itemlist.append(Item(channel=item.channel, title=format_title(option['title']), thumbnail=thumbnail, fanart=fanart, plot=plot, action='show_menu', url=url, path=item.path))
        itemlist.append(Item(channel=item.channel, title=typo('Cerca...','color kod bold'), thumbnail=get_thumb('search.png'), action='search', url=item.url, path=item.path))
        if 'channel_name' in json_data: autoplay.show_option(item.channel, itemlist)
        return itemlist

    if "movies_list" in json_data:
        item.media_type='movies_list'

    elif "tvshows_list" in json_data:
        item.media_type = 'tvshows_list'

    elif "episodes_list" in json_data:
        item.media_type = 'episodes_list'

    if "generic_list" in json_data:
        item.media_type='generic_list'

    return list_all(item)

def list_all(item):
    logger.info()

    itemlist = []
    media_type = item.media_type
    json_data = load_json(item)
    if json_data:
        for media in json_data[media_type]:

            quality, language, plot, poster = set_extra_values(media)

            title = media['title']
            title = set_title(title, language, quality)

            new_item = Item(channel=item.channel, title=format_title(title), quality=quality,
                            language=language, plot=plot, personal_plot=plot, thumbnail=poster, path=item.path)

            new_item.infoLabels['year'] = media['year'] if 'year' in media else ''
            new_item.infoLabels['tmdb_id'] = media['tmdb_id'] if 'tmdb_id' in media else ''

            if 'movies_list' in json_data or 'generic_list' in json_data:
                new_item.url = media
                new_item.contentTitle = media['title']
                new_item.action = 'findvideos'
            else:
                new_item.url = media['seasons_list']
                new_item.contentSerieName = media['title']
                new_item.action = 'seasons'

            itemlist.append(new_item)

        if not 'generic_list' in json_data:
            tmdb.set_infoLabels(itemlist, seekTmdb=True)
            for item in itemlist:
                if item.personal_plot != item.plot and item.personal_plot:
                    item.plot = '\n\n' + typo('','submenu') + '\n' + item.personal_plot + '\n' + typo('','submenu') + '\n\n' + item.plot
        return itemlist

def seasons(item):
    logger.info()
    itemlist = []
    infoLabels = item.infoLabels
    list_seasons = item.url
    for season in list_seasons:
        infoLabels['season'] = season['season']
        title = config.get_localized_string(60027) % season['season']
        url = '' if not season['link'] else season['link'] if ':/' in season['link'] else item.path + season['link']
        itemlist.append(Item(channel=item.channel, title=format_title(title), url=url, action='episodesxseason',
                             contentSeasonNumber=season['season'], infoLabels=infoLabels))

    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    itemlist = sorted(itemlist, key=lambda i: i.title)

    return itemlist


def episodesxseason(item):
    logger.info()

    itemlist = []
    json_data = load_json(item)
    infoLabels = item.infoLabels

    season_number = infoLabels['season']
    for episode in json_data['episodes_list']:
        episode_number = episode['number']
        infoLabels['season'] = season_number
        infoLabels['episode'] = episode_number

        title = config.get_localized_string(70677) + ' %s' % (episode_number)

        itemlist.append(Item(channel=item.channel, title=format_title(title), url=episode, action='findvideos',
                             contentEpisodeNumber=episode_number, infoLabels=infoLabels))

    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    if 'links' in item.url:
        for url in item.url['links']:
            quality, language, plot, poster = set_extra_values(url)
            title = ''
            title = set_title(title, language, quality)

            itemlist.append(Item(channel=item.channel, title=format_title('%s'+title), url=url['url'], action='play', quality=quality,
                                language=language, infoLabels = item.infoLabels))

        itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())

        autoplay.start(itemlist, item)

        return itemlist

def add_channel(item):
    logger.info()
    import xbmc
    import xbmcgui
    channel_to_add = {}
    json_file = ''
    result = platformtools.dialog_select(config.get_localized_string(70676), [config.get_localized_string(70678), config.get_localized_string(70679)])
    if result == -1:
        return
    if result==0:
        file_path = xbmcgui.Dialog().browseSingle(1, config.get_localized_string(70680), 'files')
        try:
            channel_to_add['path'] = file_path
            json_file = jsontools.load(open(file_path, "r").read())
            channel_to_add['channel_name'] = json_file['channel_name']
        except:
            pass

    elif result==1:
        url = platformtools.dialog_input("", config.get_localized_string(70681), False)
        try:
            channel_to_add['path'] = url
            json_file = jsontools.load(httptools.downloadpage(url).data)
        except:
            pass

    if len(json_file) == 0:
        return
    if "episodes_list" in json_file:
        platformtools.dialog_ok(config.get_localized_string(20000), config.get_localized_string(70682))
        return
    channel_to_add['channel_name'] = json_file['channel_name']
    channel_to_add['thumbnail'] = json_file['thumbnail']
    channel_to_add['fanart'] = json_file['fanart']
    path = os.path.join(config.get_data_path(), 'community_channels.json')

    community_json = open(path, "r")
    community_json = jsontools.load(community_json.read())
    id = len(community_json['channels']) + 1
    community_json['channels'][id]=(channel_to_add)

    with open(path, "w") as file:
         file.write(jsontools.dump(community_json))
    file.close()

    platformtools.dialog_notification(config.get_localized_string(20000), config.get_localized_string(70683) % json_file['channel_name'])
    return

def remove_channel(item):
    logger.info()
    import xbmc
    import xbmcgui
    path = os.path.join(config.get_data_path(), 'community_channels.json')

    community_json = open(path, "r")
    community_json = jsontools.load(community_json.read())

    id = item.channel_id
    to_delete = community_json['channels'][id]['channel_name']
    del community_json['channels'][id]
    with open(path, "w") as file:
         file.write(jsontools.dump(community_json))
    file.close()

    platformtools.dialog_notification(config.get_localized_string(20000), config.get_localized_string(70684) % to_delete)
    platformtools.itemlist_refresh()
    return


def set_extra_values(dict):
    logger.info()
    quality = ''
    language = ''
    plot = ''
    poster = ''

    if 'quality' in dict and dict['quality'] != '':
        quality = dict['quality'].upper()
    if 'language' in dict and dict['language'] != '':
        language = dict['language'].upper()
    if 'plot' in dict and dict['plot'] != '':
        plot = dict['plot']
    if 'poster' in dict and dict['poster'] != '':
        poster = dict['poster']

    return quality, language, plot, poster

def set_title(title, language, quality):
    logger.info()

    if not config.get_setting('unify'):
        if quality != '':
            title += typo(quality, '_ [] color kod')
        if language != '':
            if not isinstance(language, list):
                title += typo(language.upper(), '_ [] color kod')
            else:
                for lang in language:
                    title += typo(lang.upper(), '_ [] color kod')

    return title

def format_title(title):
    t = scrapertoolsV2.find_single_match(title, r'\{([^\}]+)\}')
    if 'bold' not in t: t += ' bold'
    title = re.sub(r'(\{[^\}]+\})','',title)
    return typo(title,t)

def search(item, text):
    logger.info('Search '+ text)
    itemlist = []
    json_data = load_json(item)

    return load_links(item, itemlist, json_data, text)

def load_links(item, itemlist, json_data, text):
    for option in json_data['menu']:
        json_data = load_json(option['link'] if option['link'].startswith('http') else item.path+option['link'])
        if not 'menu' in json_data:
            if "movies_list" in json_data: media_type= 'movies_list'
            elif "tvshows_list" in json_data: media_type = 'tvshows_list'
            elif "episodes_list" in json_data: media_type = 'episodes_list'
            if "generic_list" in json_data: media_type= 'generic_list'

            if json_data:
                for media in json_data[media_type]:
                    if text.lower() in media['title'].lower():
                        quality, language, plot, poster = set_extra_values(media)

                        title = media['title']
                        title = set_title(title, language, quality)

                        new_item = Item(channel=item.channel, title=format_title(title), quality=quality,
                                        language=language, plot=plot, personal_plot=plot, thumbnail=poster, path=item.path)

                        new_item.infoLabels['year'] = media['year'] if 'year' in media else ''
                        new_item.infoLabels['tmdb_id'] = media['tmdb_id'] if 'tmdb_id' in media else ''

                        if 'movies_list' in json_data or 'generic_list' in json_data:
                            new_item.url = media
                            new_item.contentTitle = media['title']
                            new_item.action = 'findvideos'
                        else:
                            new_item.url = media['seasons_list']
                            new_item.contentSerieName = media['title']
                            new_item.action = 'seasons'

                        itemlist.append(new_item)

                        if not 'generic_list' in json_data:
                            tmdb.set_infoLabels(itemlist, seekTmdb=True)
                            for item in itemlist:
                                if item.personal_plot != item.plot and item.personal_plot:
                                    item.plot = '\n\n' + typo('','submenu') + '\n' + item.personal_plot + '\n' + typo('','submenu') + '\n\n' + item.plot
        else:
            load_links(item, itemlist, json_data, text)
    return itemlist