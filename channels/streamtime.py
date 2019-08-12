# -*- coding: utf-8 -*-
from core import support, httptools, scrapertoolsV2
from core.item import Item
from platformcode import config

__channel__ = "streamtime"
host = config.get_channel_url(__channel__)
headers = [['Referer', host]]
list_servers = ['directo']
list_quality = ['default']

@support.menu
def mainlist(item):
    film = []
    tvshow = []
    return locals()


@support.scrape
def peliculas(item):
    patron = """tgme_widget_message_photo_wrap blured.*?image:url\(\"(?P<thumbnail>[^"]+).*?🎥.*?<b>(?P<title>.*?)</b>.*?Genere(?P<genre>.*?)<b>Anno</b>: (?P<year>[0-9]{4}).*?<b>Stream</b>: (?P<quality>[^<]+).*?tgme_widget_message_inline_button url_button" href="(?P<url>[^"]+)"""
    patronBlock = '<div class="tgme_widget_message force_userpic js-widget_message"(?P<block>.*?)</div></div>'
    def itemlistHook(itemlist):
        return itemlist[::-1]
    # debug = True
    return locals()


def findvideos(item):
    id = item.url.split('/')[-1]
    url = scrapertoolsV2.find_single_match(item.url, 'https?://[a-z0-9.-]+') + '/play_f.php?f=' + id
    res = support.match(item, 'src="([^"]+)"></video>', url=url)

    itemlist = [
        Item(channel=item.channel,
             action="play",
             title='stpgs.ml [COLOR blue]' + item.quality + '[/COLOR]',
             url=res[0][0],
             fulltitle=item.fulltitle,
             thumbnail=item.thumbnail,
             show=item.show,
             quality=item.quality,
             contentType=item.contentType,
             folder=False)]
    return support.controls(itemlist, item, True, False)
