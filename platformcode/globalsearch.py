# -*- coding: utf-8 -*-

import xbmc, xbmcgui, xbmcplugin, sys, channelselector, time
from core.support import dbg, typo
from core.item import Item
from core import channeltools, servertools, scrapertools
from platformcode import platformtools, config, logger
from platformcode.launcher import run, start
from threading import Thread

if sys.version_info[0] >= 3:
    from concurrent import futures
else:
    from concurrent_py2 import futures


def set_workers():
    workers = config.get_setting('thread_number') if config.get_setting('thread_number') > 0 else None
    return workers


def Search(item):
    SearchWindow('GlobalSearch.xml', config.get_runtime_path()).start(item)

# Actions
LEFT = 1
RIGHT = 2
UP = 3
DOWN = 4
EXIT = 10
BACKSPACE = 92

# Container
SEARCH = 1
EPISODES = 2
SERVERS = 3

# Search
PROGRESS = 100
MAINTITLE = 101
CHANNELS = 102
RESULTS = 103
COUNT = 104

# Servers
EPISODESLIST = 200
SERVERLIST = 300

class SearchWindow(xbmcgui.WindowXML):
    def start(self, item):
        xbmc.executebuiltin('Dialog.Close(all,true)')
        self.exit = False
        self.item = item
        self.item.mode = 'all'
        if config.get_setting('last_search'):
            last_search = channeltools.get_channel_setting('Last_searched', 'search', '')
        else:
            last_search = ''
        if not item.text:
            item.text = platformtools.dialog_input(default=last_search, heading='')
        if not item.text:
            return
        channeltools.set_channel_setting('Last_searched', item.text, 'search')
        self.channels = []
        self.results = {}
        self.channelsList =  self.get_channels()
        self.focus = SEARCH
        self.episodes = []
        self.servers = []
        self.doModal()

    def get_channels(self):
        channels_list = []
        all_channels = channelselector.filterchannels('all')

        for ch in all_channels:
            channel = ch.channel
            ch_param = channeltools.get_channel_parameters(channel)
            if not ch_param.get("active", False):
                continue
            list_cat = ch_param.get("categories", [])

            if not ch_param.get("include_in_global_search", False):
                continue

            if 'anime' in list_cat:
                n = list_cat.index('anime')
                list_cat[n] = 'tvshow'

            if self.item.mode == 'all' or (self.item.mode in list_cat):
                if config.get_setting("include_in_global_search", channel) and ch_param.get("active", False):
                    channels_list.append(channel)

        return channels_list

    def getModule(self, channel):
        try:
            module = __import__('channels.%s' % channel, fromlist=["channels.%s" % channel])
            mainlist = getattr(module, 'mainlist')(Item(channel=channel, global_search=True))
            action = [elem for elem in mainlist if elem.action == "search" and (self.item.mode == 'all' or elem.contentType in [self.item.mode, 'undefined'])]
            return module, action
        except:
            import traceback
            logger.error('error importing/getting search items of ' + channel)
            logger.error(traceback.format_exc())

    def search(self):
        self.time = time.time()
        self.count = 0
        self.executor = futures.ThreadPoolExecutor(max_workers=set_workers())
        for searchAction in self.searchActions:
            if self.exit: break
            self.executor.submit(self.get_channel_results, self.item, self.moduleDict, searchAction)

    def get_channel_results(self, item, module_dict, search_action):
        channel = search_action.channel
        results = []
        valid = []
        module = module_dict[channel]
        searched_id = item.infoLabels['tmdb_id']

        try:
            results.extend(module.search(search_action, item.text))
            if len(results) == 1:
                if not results[0].action or config.get_localized_string(70006).lower() in results[0].title.lower():
                    results.clear()
            if item.mode != 'all':
                for elem in results:
                    if not elem.infoLabels.get('year', ""):
                        elem.infoLabels['year'] = '-'
                    tmdb.set_infoLabels_item(elem)
                    if elem.infoLabels['tmdb_id'] == searched_id:
                        elem.from_channel = channel
                        if not config.get_setting('unify'):
                            elem.title += ' [%s]' % channel
                        valid.append(elem)
        except:
            pass

        self.count += 1
        self.update(channel, results)

    def update(self, channel, results):
        if results:
            channelParams = channeltools.get_channel_parameters(channel)
            name = channelParams['title']
            if name not in self.results:
                self.results[name] = [results, len(self.channels)]
                item = xbmcgui.ListItem(name)
                item.setProperty('thumb', channelParams['thumbnail'])
                item.setProperty('position', '0')
                item.setProperty('results', str(len(results)))
                self.channels.append(item)
            else:
                self.results[name].append([results, len(self.channels)])
                self.channels[int(self.results[name][1])].setProperty('results', str(len(results)))
            pos = self.CHANNELS.getSelectedPosition()
            self.CHANNELS.reset()
            self.CHANNELS.addItems(self.channels)
            self.CHANNELS.selectItem(pos)
            if len(self.channels) == 1:
                self.setFocusId(CHANNELS)
                items = []
                for result in self.results[name][0]:
                    item = xbmcgui.ListItem(result.title)
                    item.setProperty('thumb', result.thumbnail)
                    item.setProperty('fanart', result.fanart)
                    item.setProperty('plot', result.plot)
                    items.append(item)
                self.RESULTS.addItems(items)
        percent = (float(self.count) / len(self.searchActions)) * 100
        self.PROGRESS.setPercent(percent)
        self.COUNT.setText('%s/%s [%s"]' % (self.count, len(self.searchActions), int(time.time() - self.time) ))
        xbmcplugin.endOfDirectory()

    def onInit(self):
        self.CHANNELS = self.getControl(CHANNELS)
        self.RESULTS = self.getControl(RESULTS)
        self.PROGRESS = self.getControl(PROGRESS)
        self.COUNT = self.getControl(COUNT)
        self.MAINTITLE = self.getControl(MAINTITLE)
        self.MAINTITLE.setText(typo(config.get_localized_string(30993).replace('...','') % '"%s"' % self.item.text, 'bold'))
        self.SEARCH = self.getControl(SEARCH)
        self.EPISODES = self.getControl(EPISODES)
        self.EPISODESLIST = self.getControl(EPISODESLIST)
        self.SERVERS = self.getControl(SERVERS)
        self.SERVERLIST = self.getControl(SERVERLIST)

        self.moduleDict = {}
        self.searchActions = []

        self.Focus(self.focus)

        if not self.channels:
            with futures.ThreadPoolExecutor() as executor:
                for channel in self.channelsList:
                    if self.exit: break
                    module, action = executor.submit(self.getModule, channel).result()
                    self.moduleDict[channel] = module
                    self.searchActions += action

            self.thread = Thread(target=self.search)
            self.thread.start()

    def Focus(self, focusid):
        if focusid in [SEARCH]:
            self.focus = CHANNELS
            self.SEARCH.setVisible(True)
            self.EPISODES.setVisible(False)
            self.SERVERS.setVisible(False)
        if focusid in [EPISODES]:
            self.focus = focusid
            self.SEARCH.setVisible(False)
            self.EPISODES.setVisible(True)
            self.SERVERS.setVisible(False)
        if focusid in [SERVERS]:
            self.focus = SERVERLIST
            self.SEARCH.setVisible(False)
            self.EPISODES.setVisible(False)
            self.SERVERS.setVisible(True)

    def onAction(self, action):
        action = action.getId()
        focus = self.getFocusId()
        # if action in [117]:
        #     xbmc.executebuiltin('ActivateWindow(10106)')
        if action in [LEFT, RIGHT] and focus in [CHANNELS]:
            items = []
            name = self.CHANNELS.getSelectedItem().getLabel()
            subpos = int(self.CHANNELS.getSelectedItem().getProperty('position'))
            for result in self.results[name][0]:
                item = xbmcgui.ListItem(result.title)
                item.setProperty('thumb', result.thumbnail)
                item.setProperty('fanart', result.fanart)
                item.setProperty('plot', result.plot)
                items.append(item)
            self.RESULTS.reset()
            self.RESULTS.addItems(items)
            self.RESULTS.selectItem(subpos)
        if focus in [RESULTS]:
            pos = self.RESULTS.getSelectedPosition()
            self.CHANNELS.getSelectedItem().setProperty('position', str(pos))

        if action in [BACKSPACE]:
            if self.SERVERS.isVisible():
                if self.episodes:
                    self.Focus(EPISODES)
                    self.setFocusId(EPISODESLIST)
                else:
                    self.Focus(SEARCH)
                    self.setFocusId(RESULTS)
                    self.RESULTS.selectItem(self.pos)
            elif self.EPISODES.isVisible():
                self.Focus(SEARCH)
                self.setFocusId(RESULTS)
                self.RESULTS.selectItem(self.pos)
            else:
                self.exit = True
                self.close()
                xbmc.sleep(600)
                platformtools.itemlist_refresh()

        elif action in [EXIT]:
            self.exit = True
            self.close()
            xbmc.sleep(600)
            platformtools.itemlist_refresh()

    def onClick(self, control_id):
        if control_id in [CHANNELS]:
            items = []
            name = self.CHANNELS.getSelectedItem().getLabel()
            subpos = int(self.CHANNELS.getSelectedItem().getProperty('position'))
            for result in self.results[name][0]:
                logger.info(result)
                item = xbmcgui.ListItem(result.title)
                item.setProperty('thumb', result.thumbnail)
                item.setProperty('fanart', result.fanart)
                item.setProperty('plot', result.plot)
                items.append(item)
            self.RESULTS.reset()
            self.RESULTS.addItems(items)
            self.RESULTS.selectItem(subpos)
            self.CHANNELS.getSelectedItem().setProperty('position', str(subpos))

        if control_id in [RESULTS, EPISODESLIST]:
            if control_id in [RESULTS]:
                name = self.CHANNELS.getSelectedItem().getLabel()
                self.pos = self.RESULTS.getSelectedPosition()
                item = self.results[name][0][self.pos]
            else:
                self.pos = self.EPISODESLIST.getSelectedPosition()
                item = self.episodes[self.pos]

            self.channel = __import__('channels.%s' % item.channel, fromlist=["channels.%s" % item.channel])
            self.itemsResult = getattr(self.channel, item.action)(item)

            if item.action in ['findvideos']:
                if config.get_setting('checklinks') and not config.get_setting('autoplay'):
                    checklinks_number = config.get_setting('checklinks_number')
                    self.itemsResult = servertools.check_list_links(self.itemsResult, checklinks_number)
                self.servers = self.itemsResult 
                self.itemsResult = []
                uhd = []
                fhd = []
                hd = []
                sd = []
                unknown = []
                for i, item in enumerate(self.servers):
                    if item.server:
                        color = scrapertools.find_single_match(item.alive, r'(FF[^\]]+)')
                        it = xbmcgui.ListItem(item.infoLabels['title'])
                        it.setProperty('channel', channeltools.get_channel_parameters(item.channel).get('title',''))
                        it.setProperty('thumb', "https://raw.githubusercontent.com/kodiondemand/media/master/resources/servers/%s.png" % item.server.lower())
                        it.setProperty('servername', servertools.get_server_parameters(item.server.lower()).get('name',item.server))
                        it.setProperty('color', color if color else 'FF0082C2')

                        it.setProperty('index', str(i))
                        if item.quality in ['4k', '2160p', '2160', '4k2160p', '4k2160', '4k 2160p', '4k 2160', '2k']:
                            it.setProperty('quality', 'uhd.png')
                            uhd.append(it)
                        elif item.quality in ['fullhd', 'fullhd 1080', 'fullhd 1080p', 'full hd', 'full hd 1080', 'full hd 1080p', 'hd1080', 'hd1080p', 'hd 1080', 'hd 1080p', '1080', '1080p']:
                            it.setProperty('quality', 'Fhd.png')
                            fhd.append(it)
                        elif item.quality in ['hd', 'hd720', 'hd720p', 'hd 720', 'hd 720p', '720', '720p', 'hdtv']:
                            it.setProperty('quality', 'hd.png')
                            hd.append(it)
                        elif item.quality in ['sd', '480p', '480', '360p', '360', '240p', '240']:
                            it.setProperty('quality', 'sd.png')
                            sd.append(it)
                        else:
                            it.setProperty('quality', '')
                            unknown.append(it)

                uhd.sort(key=lambda it: it.getProperty('index'))
                fhd.sort(key=lambda it: it.getProperty('index'))
                hd.sort(key=lambda it: it.getProperty('index'))
                sd.sort(key=lambda it: it.getProperty('index'))
                unknown.sort(key=lambda it: it.getProperty('index'))

                serverlist = uhd + fhd + hd + sd + unknown

                self.Focus(SERVERS)
                self.SERVERLIST.reset()
                self.SERVERLIST.addItems(serverlist)
                self.setFocusId(SERVERLIST)

            else:
                self.episodes = self.itemsResult
                self.itemsResult = []
                episodes = []
                for item in self.episodes:
                    if item.action == 'findvideos':
                        it = xbmcgui.ListItem(item.title)
                        episodes.append(it)
    
                self.Focus(EPISODES)
                self.EPISODESLIST.reset()
                self.EPISODESLIST.addItems(episodes)
                self.setFocusId(EPISODESLIST)

        
        if control_id in [SERVERLIST]:
            index = int(self.getControl(control_id).getSelectedItem().getProperty('index'))
            server = self.servers[index]
            run(server)