# -*- coding: utf-8 -*-
# -*- Channel Community -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import re, os, inspect, requests

from core import httptools, scrapertoolsV2, servertools, jsontools, tmdb, support
from core.item import Item
from core.support import typo
from channelselector import get_thumb
from platformcode import  config, platformtools
from specials import autoplay


list_data = {}

list_language = ['ITA', 'SUB-ITA']
list_servers = ['directo', 'akvideo', 'verystream', 'openload']
list_quality = ['SD', '720', '1080', '4k']


def mainlist(item):
    support.log()

    path = os.path.join(config.get_data_path(), 'community_channels.json')
    if not os.path.exists(path):
        with open(path, "w") as file:
            file.write('{"channels":{}}')
            file.close()
    autoplay.init(item.channel, list_servers, list_quality)

    return show_channels(item)


def show_channels(item):
    support.log()
    itemlist = []

    context = [{"title": config.get_localized_string(50005),
                "action": "remove_channel",
                "channel": "community"}]

    path = os.path.join(config.get_data_path(), 'community_channels.json')
    file = open(path, "r")
    json = jsontools.load(file.read())

    itemlist.append(Item(channel=item.channel,
                         title=typo(config.get_localized_string(70676),'bold color kod'),
                         action='add_channel',
                         thumbnail=get_thumb('add.png')))

    for key, channel in json['channels'].items():
        # Find File Path
        if 'http' in channel['path']: file_path = requests.get(channel['path']).url
        else: file_path = channel['path']

        # make relative path
        path = os.path.dirname(os.path.abspath(file_path))
        if 'http' in path: path = path[path.find('http'):].replace('\\','/').replace(':/','://')
        if file_path.startswith('http'): file_url = httptools.downloadpage(file_path, follow_redirects=True).data
        else: file_url = open(file_path, "r").read()

        # loa djson
        json_url = jsontools.load(file_url)

        thumbnail = relative('thumbnail', json_url, path)
        fanart = relative('fanart', json_url, path)
        plot = json_url['plot'] if json_url.has_key('plot') else ''

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


def show_menu(item):
    global list_data
    itemlist = []
    support.log()

    json_data = load_json(item)

    if "menu" in json_data:
        for option in json_data['menu']:
            thumbnail = relative('thumbnail', option, item.path)
            fanart = relative('fanart', option, item.path)
            plot = option['plot'] if option.has_key('plot') else item.plot
            url = relative('link', option, item.path)
            submenu = option['submenu'] if option.has_key('submenu') else []
            itemlist.append(Item(channel=item.channel,
                                 title=format_title(option['title']),
                                 thumbnail=thumbnail,
                                 fanart=fanart,
                                 plot=plot,
                                 action='show_menu',
                                 url=url,
                                 path=item.path))
            if submenu:
                for key in submenu:
                    if key != 'search':
                        itemlist.append(Item(channel=item.channel,
                                            title=typo(submenu[key],'submenu'),
                                            url=url,
                                            path=item.path,
                                            thumbnail=item.thumbnail,
                                            action='submenu',
                                            filterkey=key))
                if submenu.has_key('search'):
                    itemlist.append(Item(channel=item.channel,
                                         title=typo('Cerca ' + option['title'] +'...','color kod bold'),
                                         thumbnail=get_thumb('search.png'),
                                         action='search',
                                         url=url,
                                         path=item.path))
         # add Search
        itemlist.append(Item(channel=item.channel,
                             title=typo('Cerca nel Canale...','color kod bold'),
                             thumbnail=get_thumb('search.png'),
                             action='search',
                             url=item.url,
                             path=item.path))
        # autoplay config only in main menu
        if json_data.has_key('channel_name'): autoplay.show_option(item.channel, itemlist)
        return itemlist

    # select type of list
    if json_data.has_key("movies_list"): item.media_type= 'movies_list'
    elif json_data.has_key("tvshows_list"): item.media_type = 'tvshows_list'
    elif json_data.has_key("episodes_list"): item.media_type = 'episodes_list'
    elif json_data.has_key("generic_list"): item.media_type= 'generic_list'

    return list_all(item)


def submenu(item):
    support.log()

    itemlist = []
    filter_list = []

    json_data = load_json(item)
    if json_data.has_key("movies_list"): item.media_type= 'movies_list'
    elif json_data.has_key("tvshows_list"): item.media_type = 'tvshows_list'
    elif json_data.has_key("episodes_list"): item.media_type = 'episodes_list'
    elif json_data.has_key("generic_list"): item.media_type= 'generic_list'
    media_type = item.media_type

    for media in json_data[media_type]:
        if media.has_key(item.filterkey):
            if type(media[item.filterkey]) == str and media[item.filterkey] not in filter_list:
                filter_list.append(media[item.filterkey].lower())
            elif type(media[item.filterkey]) == list:
                for f in media[item.filterkey]:
                    if f not in filter_list:
                        filter_list.append(f.lower())
    filter_list.sort()
    for filter in filter_list:
        itemlist.append(Item(channel=item.channel,
                             title=typo(filter, 'bold'),
                             url=item.url,
                             media_type=item.media_type,
                             action='list_filtered',
                             filterkey=item.filterkey,
                             filter=filter))
    return itemlist


def list_all(item):
    support.log()

    itemlist = []
    media_type = item.media_type
    json_data = load_json(item)
    contentTitle = contentSerieName = ''
    infoLabels = item.infoLabels if item.infoLabels else {}

    if json_data:
        for media in json_data[media_type]:

            quality, language, plot, poster = set_extra_values(media)

            fulltitle = media['title']
            title = set_title(fulltitle, language, quality)

            infoLabels['year'] = media['year'] if media.has_key('year')else ''
            infoLabels['tmdb_id'] = media['tmdb_id'] if media.has_key('tmdb_id') else ''

            if 'movies_list' in json_data or 'generic_list' in json_data:
                url= media
                contentTitle = fulltitle
                contentType = 'movie'
                action='findvideos'

            else:
                contentSerieName = fulltitle
                contentType = 'tvshow'
                if media.has_key('seasons_list'):
                    url = media['seasons_list']
                    action = 'get_seasons'
                else:
                    url = relative('link', media, item.path)
                    action = 'episodios'

            itemlist.append(Item(channel=item.channel,
                                 contentType=contentType,
                                 title=format_title(title),
                                 fulltitle=fulltitle,
                                 show=fulltitle,
                                 quality=quality,
                                 language=language,
                                 plot=plot,
                                 personal_plot=plot,
                                 thumbnail=poster,
                                 path=item.path,
                                 url=url,
                                 contentTitle=contentTitle,
                                 contentSerieName=contentSerieName,
                                 action=action))

        if not 'generic_list' in json_data:
            tmdb.set_infoLabels(itemlist, seekTmdb=True)
            for item in itemlist:
                if item.personal_plot != item.plot and item.personal_plot:
                    item.plot = '\n\n' + typo('','submenu') + '\n' + item.personal_plot + '\n' + typo('','submenu') + '\n\n' + item.plot
        return itemlist


def list_filtered(item):
    support.log()

    itemlist = []
    media_type = item.media_type
    json_data = load_json(item)
    contentTitle = contentSerieName = ''
    infoLabels = item.infoLabels if item.infoLabels else {}

    if json_data:
        for media in json_data[media_type]:
            if media.has_key(item.filterkey) and (item.filter.lower() in media[item.filterkey]):

                quality, language, plot, poster = set_extra_values(media)

                fulltitle = media['title']
                title = set_title(fulltitle, language, quality)

                infoLabels['year'] = media['year'] if media.has_key('year')else ''
                infoLabels['tmdb_id'] = media['tmdb_id'] if media.has_key('tmdb_id') else ''

                if 'movies_list' in json_data or 'generic_list' in json_data:
                    url= media
                    contentTitle = fulltitle
                    contentType = 'movie'
                    action='findvideos'

                else:
                    contentSerieName = fulltitle
                    contentType = 'tvshow'
                    if media.has_key('seasons_list'):
                        url = media['seasons_list']
                        action = 'get_seasons'
                    else:
                        url = relative('link', media, item.path)
                        action = 'episodios'

                itemlist.append(Item(channel=item.channel,
                                     contentType=contentType,
                                     title=format_title(title),
                                     fulltitle=fulltitle,
                                     show=fulltitle,
                                     quality=quality,
                                     language=language,
                                     plot=plot,
                                     personal_plot=plot,
                                     thumbnail=poster,
                                     path=item.path,
                                     url=url,
                                     contentTitle=contentTitle,
                                     contentSerieName=contentSerieName,
                                     action=action))

        if not 'generic_list' in json_data:
            tmdb.set_infoLabels(itemlist, seekTmdb=True)
            for item in itemlist:
                if item.personal_plot != item.plot and item.personal_plot:
                    item.plot = '\n\n' + typo('','submenu') + '\n' + item.personal_plot + '\n' + typo('','submenu') + '\n\n' + item.plot
    return itemlist


def get_seasons(item):
    support.log()
    itemlist = []
    infoLabels = item.infoLabels if item.infolabels else {}
    list_seasons = item.url

    for season in list_seasons:
        infoLabels['season'] = season['season']
        title = config.get_localized_string(60027) % season['season']
        url = relative('link', season, item.path)

        itemlist.append(Item(channel=item.channel,
                             title=format_title(title),
                             fulltitle=item.fulltitle,
                             show=item.show,
                             thumbnails=item.thumbnails,
                             url=url,
                             action='episodios',
                             contentSeason=season['season'],
                             infoLabels=infoLabels,
                             contentType='tvshow'))


    if inspect.stack()[1][3] in ['add_tvshow', "get_seasons"]:
        it = []
        for item in itemlist:
            it += episodios(item)

        itemlist = it
    else:
        tmdb.set_infoLabels(itemlist, seekTmdb=True)
        itemlist = sorted(itemlist, key=lambda i: i.title)
        support.videolibrary(itemlist,item)

    return itemlist


def episodios(item):
    support.log()

    itemlist = []
    json_data = load_json(item)
    infoLabels = item.infoLabels
    ep = 1
    season_number = infoLabels['season'] if infoLabels.has_key('season') else item.contentSeason if item.contentSeason  else 1
    for episode in json_data['episodes_list']:
        match = []
        if episode.has_key('number'): match = support.match(episode['number'], r'(?P<season>\d+)x(?P<episode>\d+)')[0][0]
        if not match and episode.has_key('title'): match = support.match(episode['title'], r'(?P<season>\d+)x(?P<episode>\d+)')[0][0]
        if match:
            episode_number = match[1]
            ep = int(match[1]) + 1
            season_number = match[0]
        else:
           season_number = episode['season'] if episode.has_key('season') else 1
           episode_number = episode['number'] if episode.has_key('number') else ''
           ep = int(episode_number) if episode_number else ep
        if not episode_number:
            episode_number = str(ep).zfill(2)
            ep += 1

        infoLabels['season'] = season_number
        infoLabels['episode'] = episode_number

        plot = episode['plot'] if episode.has_key('plot') else item.plot
        thumbnail = episode['poster'] if episode.has_key('poster') else episode['thumbnail'] if episode.has_key('thumbnail') else item.thumbnail

        title = ' - ' + episode['title'] if episode.has_key('title') else ''
        title = '%sx%s%s' % (season_number, episode_number, title)

        itemlist.append(Item(channel= item.channel,
                             title= format_title(title),
                             fulltitle = item.fulltitle,
                             show = item.show,
                             url= episode,
                             action= 'findvideos',
                             plot= plot,
                             thumbnail= thumbnail,
                             contentSeason= season_number,
                             contentEpisode= episode_number,
                             infoLabels= infoLabels,
                             contentType= 'episode'))

    tmdb.set_infoLabels(itemlist, seekTmdb=True)
    return itemlist


def findvideos(item):
    support.log()
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
    support.log()
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
    support.log()
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
    support.log()
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
    support.log()

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
    support.log('Search ', text)
    itemlist = []
    json_data = load_json(item)
    support.log('JSON= ', json_data)

    return load_links(item, itemlist, json_data, text)


def load_links(item, itemlist, json_data, text):
    support.log()

    def links(item, itemlist, json_data, text):
        support.log()
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

    if json_data.has_key('menu'):
        for option in json_data['menu']:
            json_data = load_json(option['link'] if option['link'].startswith('http') else item.path+option['link'])
            load_links(item, itemlist, json_data, text)
    else:
        links(item, itemlist, json_data, text)

    return itemlist


def relative(key, json, path):
    if json.has_key(key):
        if key == 'thumbnail':
            ret = json[key] if ':/' in json[key] else path + json[key] if '/' in json[key] else get_thumb(json[key]) if json[key] else ''
        else:
            ret = json[key] if ':/' in json[key] else path + json[key] if '/' in json[key]  else ''
    else:
        ret = ''
    return ret


def load_json(item):
    support.log()
    url= item if type(item) == str else item.url
    try:
        if url.startswith('http'):
            json_file = httptools.downloadpage(url).data
        else:
            json_file = open(url, "r").read()

        json_data = jsontools.load(json_file)

    except:
        json_data = {}

    return json_data