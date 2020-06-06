# -*- coding: utf-8 -*-
import os
import sys
import unittest
import parameterized

from platformcode import config
librerias = os.path.join(config.get_runtime_path(), 'lib')
sys.path.insert(0, librerias)
from core.support import typo
from core.item import Item
import channelselector

chBlackList = ['url']

def getChannels():
    channel_list = channelselector.filterchannels("all")
    ret = []
    for chItem in channel_list:
        ch = chItem.channel
        if ch not in chBlackList:
            ret.append({'ch': ch})
    return ret

from specials import news
dictNewsChannels, any_active = news.get_channels_list()


@parameterized.parameterized_class(getChannels())
class GenericChannelTest(unittest.TestCase):
    def __init__(self, *args):
        self.module = __import__('channels.%s' % self.ch, fromlist=["channels.%s" % self.ch])
        super(GenericChannelTest, self).__init__(*args)

    def test_menuitems(self):
        hasAutoplayConfig = False
        hasChannelConfig = False
        mainlist = self.module.mainlist(Item())
        self.assertTrue(mainlist, 'channel ' + self.ch + ' has no menu')

        for it in mainlist:
            if it.action == 'autoplay_config':
                hasAutoplayConfig = True
                continue
            if it.action == 'channel_config':
                hasChannelConfig = True
                continue
            if it.action == 'search':  # channel specific
                continue
            itemlist = getattr(self.module, it.action)(it)
            self.assertTrue(itemlist, 'channel ' + self.ch + ' -> ' + it.title + ' is empty')
            for resIt in itemlist:
                self.assertLess(len(resIt.fulltitle), 100, 'channel ' + self.ch + ' -> ' + it.title + ' might contain wrong titles\n' + resIt.fulltitle)
                if resIt.title == typo(config.get_localized_string(30992), 'color kod bold'):  # next page
                    nextPageItemlist = getattr(self.module, resIt.action)(resIt)
                    self.assertTrue(nextPageItemlist, 'channel ' + self.ch + ' -> ' + it.title + ' has nextpage not working')
        self.assertTrue(hasChannelConfig, 'channel ' + self.ch + ' has no channel config')
        self.assertTrue(hasAutoplayConfig, 'channel ' + self.ch + ' has not autoplay config')

    def test_newest(self):
        for cat in dictNewsChannels:
            for ch in dictNewsChannels[cat]:
                if self.ch == ch[0]:
                    itemlist = self.module.newest(cat)
                    self.assertTrue(itemlist, 'channel ' + self.ch + ' returned no news for category ' + cat)
                    break

if __name__ == '__main__':
    unittest.main()