# -*- coding: utf-8 -*-

from core import servertools
from core.support import match, log
from core.item import Item
from platformcode import config, logger


def mainlist(item):
    log()

    itemlist = []
    itemlist.append(Item(channel=item.channel, action="search", title=config.get_localized_string(60089), thumbnail=item.thumbnail, args='server'))
    itemlist.append(Item(channel=item.channel, action="search", title=config.get_localized_string(60090), thumbnail=item.thumbnail, args='direct'))
    itemlist.append(Item(channel=item.channel, action="search", title=config.get_localized_string(60091), thumbnail=item.thumbnail))

    return itemlist


# Al llamarse "search" la función, el launcher pide un text a buscar y lo añade como parámetro
def search(item, text):
    log(text)

    if not text.startswith("http"):
        text = "http://" + text

    itemlist = []

    if "server" in item.args:
        itemlist = servertools.find_video_items(data=text)
        for item in itemlist:
            item.channel = "url"
            item.action = "play"
    elif "direct" in item.args:
        itemlist.append(Item(channel=item.channel, action="play", url=text, server="directo", title=config.get_localized_string(60092)))
    else:
        data = match(text).data
        itemlist = servertools.find_video_items(data=data)
        for item in itemlist:
            item.channel = "url"
            item.action = "play"

    if len(itemlist) == 0:
        itemlist.append(Item(channel=item.channel, action="search", title=config.get_localized_string(60093)))

    return itemlist
