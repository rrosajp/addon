# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per accuradio
# ------------------------------------------------------------

import random
from core import httptools,support
from platformcode import logger

host = 'https://www.accuradio.com'
headers = [['Referer', host]]

@support.scrape
def mainlist(item):
    if item.data: data = item.data
    else: item.url = host
    action = 'peliculas'
    patronBlock = r'Genres(?P<block>.*?)</ul'
    patron = r'listOptionBrand">\s*<a href="(?P<url>[^"]+)"(?:[^>]+>){2}(?P<title>[^<]+)'

    def itemHook(item):
        item.url = host + item.url
        item.thumbnail = support.thumb('music')
        return item

    def itemlistHook(itemlist):
        itemlist.append(
            item.clone(title=support.typo('Cerca...', 'bold color kod'), action='search', thumbnail=support.thumb('search')))
        support.channel_config(item, itemlist)
        return itemlist
    return locals()


@support.scrape
def peliculas(item):
    action = 'playradio'
    patron = r'data-id="(?P<id>[^"]+)"\s*data-oldid="(?P<oldid>[^"]+)".*?data-name="(?P<title>[^"]+)(?:[^>]+>){5}<img class="[^"]+"\s*src="(?P<thumb>[^"]+)(?:[^>]+>){6}\s*(?P<plot>[^<]+)'
    return locals()


def playradio(item):
    import xbmcgui, xbmc
    items = httptools.downloadpage('{}/playlist/json/{}/?ando={}&rand={}'.format(host, item.id, item.oldid, random.random())).json
    playlist = xbmc.PlayList(xbmc.PLAYLIST_MUSIC)
    playlist.clear()
    for i in items:
        if 'id' in i:
            url = i['primary'] + i['fn'] + '.m4a'
            title = i['title']
            artist = i['track_artist']
            album = i['album']['title']
            year = i['album']['year']
            thumb = 'https://www.accuradio.com/static/images/covers300' + i['album']['cdcover']
            duration = i['duration']
            info = {'duration':duration,
                    'album':album,
                    'artist':artist,
                    'title':title,
                    'year':year,
                    'mediatype':'music'}
            item = xbmcgui.ListItem(title, path=url)
            item.setArt({'thumb':thumb, 'poster':thumb, 'icon':thumb})
            item.setInfo('music',info)
            playlist.add(url, item)
    xbmc.Player().play(playlist)


def search(item, text):
    support.info(text)
    item.url = host + '/search/' + text
    itemlist = []
    try:
        data = support.match(item.url).data
        artists = support.match(data, patronBlock=r'artistResults(.*?)</ul', patron=r'href="(?P<url>[^"]+)"\s*>(?P<title>[^<]+)').matches
        if artists:
            for url, artist in artists:
                itemlist.append(item.clone(title=support.typo(artist,'bullet bold'), thumbnail=support.thumb('music'), url=host+url, action='peliculas'))
        item.data = data
        itemlist += peliculas(item)
    # Continua la ricerca in caso di errore
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
    return itemlist
