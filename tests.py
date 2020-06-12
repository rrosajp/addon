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
from core import servertools
import re
validUrlRegex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

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

srvLinkDict = {
    "wstream": ["https://wstream.video/video6zvimpy52/dvvwxyfs32ab"],
    "akvideo": ["https://akvideo.stream/video.php?file_code=23god95lrtqv"]
}

def getServers():
    server_list = servertools.get_servers_list()
    ret = []
    for srv in server_list:
        if srv in srvLinkDict:
            ret.append({'srv': srv})
    return ret

@parameterized.parameterized_class(getChannels())
class GenericChannelTest(unittest.TestCase):
    def __init__(self, *args):
        self.module = __import__('channels.%s' % self.ch, fromlist=["channels.%s" % self.ch])
        super(GenericChannelTest, self).__init__(*args)

    def test_menuitems(self):
        hasChannelConfig = False
        mainlist = self.module.mainlist(Item())
        self.assertTrue(mainlist, 'channel ' + self.ch + ' has no menu')

        for it in mainlist:
            if it.action == 'channel_config':
                hasChannelConfig = True
                continue
            if it.action == 'search':  # channel specific
                continue
            itemlist = getattr(self.module, it.action)(it)
            self.assertTrue(itemlist, 'channel ' + self.ch + ' -> ' + it.title + ' is empty')
            for resIt in itemlist:
                self.assertLess(len(resIt.fulltitle), 100, 'channel ' + self.ch + ' -> ' + it.title + ' might contain wrong titles\n' + resIt.fulltitle)
                if resIt.url:
                    self.assertIsNotNone(re.match(validUrlRegex, resIt.url), 'channel ' + self.ch + ' -> ' + it.title + ' -> ' + resIt.title + ' might contain wrong url\n' + resIt.url)
                if 'year' in resIt.infoLabels:
                    msgYear = 'channel ' + self.ch + ' -> ' + it.title + ' might contain wrong infolabels year\n' + str(resIt.infoLabels['year'])
                    self.assert_(type(resIt.infoLabels['year']) is int or resIt.infoLabels['year'].isdigit(), msgYear)
                    self.assert_(int(resIt.infoLabels['year']) > 1900 and int(resIt.infoLabels['year']) < 2100, msgYear)

                if resIt.title == typo(config.get_localized_string(30992), 'color kod bold'):  # next page
                    nextPageItemlist = getattr(self.module, resIt.action)(resIt)
                    self.assertTrue(nextPageItemlist, 'channel ' + self.ch + ' -> ' + it.title + ' has nextpage not working')
        self.assertTrue(hasChannelConfig, 'channel ' + self.ch + ' has no channel config')

    def test_newest(self):
        for cat in dictNewsChannels:
            for ch in dictNewsChannels[cat]:
                if self.ch == ch[0]:
                    itemlist = self.module.newest(cat)
                    self.assertTrue(itemlist, 'channel ' + self.ch + ' returned no news for category ' + cat)
                    break

#
# @parameterized.parameterized_class(getServers())
# class GenericServerTest(unittest.TestCase):
#     def __init__(self, *args):
#         self.module = __import__('servers.%s' % self.srv, fromlist=["servers.%s" % self.srv])
#         super(GenericServerTest, self).__init__(*args)
#
#     def test_resolve(self):
#         for link in srvLinkDict[self.srv]:
#             find = servertools.findvideosbyserver(link, self.srv)
#             self.assertTrue(find, 'link ' + link + ' not recognised')
#             page_url = find[0][1]
#             if self.module.test_video_exists(page_url)[0]:
#                 urls = self.module.get_video_url(page_url)
#                 print urls
#                 for u in urls:
#                     directUrl, headersUrl = u[1].split('|')
#                     headers = {}
#                     for name in headersUrl.split('&'):
#                         h, v = name.split('=')
#                         headers[h] = v
#                     print headers
#                     self.assertEqual(requests.head(directUrl, headers=headers, timeout=15).status_code, 200, self.srv + ' scraper did not return valid url for link ' + link)

if __name__ == '__main__':
    unittest.main()