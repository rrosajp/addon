# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Canale per Mediaset Play
# ------------------------------------------------------------

import requests
from core import support, httptools
import sys
if sys.version_info[0] >= 3:
    from concurrent import futures
    from urllib.parse import urlencode, quote
else:
    from concurrent_py2 import futures
    from urllib import urlencode, quote

DRM = 'com.widevine.alpha'
key_widevine = "https://la7.prod.conax.cloud/widevine/license"
host = 'https://www.la7.it'
headers = {
    'host_token': 'pat.la7.it',
    'host_license': 'la7.prod.conax.cloud',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
    'accept': '*/*',
    'accept-language': 'en,en-US;q=0.9,it;q=0.8',
    'dnt': '1',
    'te': 'trailers',
    'origin': 'https://www.la7.it',
    'referer': 'https://www.la7.it/',
}

icons = {'la7':'https://upload.wikimedia.org/wikipedia/commons/thumb/0/02/LA7_-_Logo_2011.svg/512px-LA7_-_Logo_2011.svg.png',
         'la7d': 'https://upload.wikimedia.org/wikipedia/it/e/ea/LA7d_LOGO_.png' }

@support.menu
def mainlist(item):
    top =  [('Dirette {bold}', ['', 'live']),
            ('Replay {bold}', ['', 'replay_channels'])]

    menu = [('Programmi TV {bullet bold}', ['/tutti-i-programmi', 'peliculas', '', 'tvshow']),
            # ('Fiction / Serie TV {bullet bold}', ['5acfcb3c23eec6000d64a6a4', 'menu', ['Tutte','all','Fiction'], 'tvshow']),
            # ('Programmi TV{ bullet bold}', ['', 'menu', ['Tutti','all','Programmi Tv'], 'tvshow']),
            # ('Documentari {bullet bold}', ['5bfd17c423eec6001aec49f9', 'menu', ['Tutti','all','Documentari'], 'undefined']),
            # ('Kids {bullet bold}', ['5acfcb8323eec6000d64a6b3', 'menu',['Tutti','all','Kids'], 'undefined']),
           ]

    # search = ''
    return locals()


def live(item):
    itemlist = [item.clone(title='La7', url= host + '/dirette-tv', action='play', forcethumb = True,  thumbnail= icons['la7']),
                item.clone(title='La7d', url= host + '/live-la7d', action='play', forcethumb = True, thumbnail= icons['la7d'])]
    return itemlist

def replay_channels(item):
    itemlist = [item.clone(title='La7', url= host + '/rivedila7/0/la7', action='replay_menu', forcethumb = True,  thumbnail= icons['la7']),
                item.clone(title='La7d', url= host + '/rivedila7/0/la7d', action='replay_menu', forcethumb = True, thumbnail= icons['la7d'])]
    return itemlist

@support.scrape
def replay_menu(item):
    action = 'replay'
    patron = r'href="(?P<url>[^"]+)"><div class="giorno-text">\s*(?P<day>[^>]+)</div><[^>]+>\s*(?P<num>[^<]+)</div><[^>]+>\s*(?P<month>[^<]+)<'
    def itemHook(item):
        item.title = support.typo(item.day + ' ' + item.num + ' ' + item.month,'bold')
        return item
    return locals()

@support.scrape
def replay(item):
    action = 'play'
    patron = r'guida-tv"><[^>]+><[^>]+>(?P<hour>[^<]+)<[^>]+><[^>]+><[^>]+>\s*<a href="(?P<url>[^"]+)"><[^>]+><div class="[^"]+" data-background-image="(?P<t>[^"]+)"><[^>]+><[^>]+><[^>]+><[^>]+>\s*(?P<name>[^<]+)<[^>]+><[^>]+><[^>]+>(?P<plot>[^<]+)<'
    def itemHook(item):
        item.title = support.typo(item.hour + ' - ' + item.name,'bold')
        item.contentTitle = item.fulltitle = item.show = item.name
        item.thumbnail = 'http:' + item.t
        item.fanart = item.thumbnail
        item.forcethumb = True
        return item
    return locals()

@support.scrape
def peliculas(item):
    pagination = 40
    action = 'episodios'
    patron = r'<a href="(?P<url>[^"]+)"[^>]+><div class="[^"]+" data-background-image="(?P<thumb>[^"]+)"></div><div class="titolo">\s*(?P<title>[^<]+)<'
    return locals()

@support.scrape
def episodios(item):
    data = support.match(item).data
    # debug=True
    action = 'play'
    if 'ultima puntata' in data:
        patron = r'<a href="(?P<url>[^"]+)"><div class="[^"]+" data-background-image="(?P<thumb>[^"]+)">[^>]+>[^>]+>[^>]+><div class="title_puntata">\s*(?P<title>[^<]+)'
    else:
        item.url += '/video'
        data = support.match(item).data
        patron = r'<a href="(?P<url>[^"]+)"><[^>]+><div class="[^"]+" data-background-image="(?P<thumb>[^"]+)"><[^>]+><[^>]+><[^>]+><[^>]+>(?P<title>[^<]+)'
        patronNext = r'<a href="([^"]+)">›'
    addVideolibrary = False
    return locals()


def findvideos(item):
    url = 'https://awsvodpkg.iltrovatore.it/local/hls/,/content/entry/data/' + support.match(item, patron='/content/entry/data/(.*?).mp4').match + '.mp4.urlset/master.m3u8'
    itemlist = [item.clone(title='Direct', url=url, server='directo', action='play')]
    return support.server(item, itemlist=itemlist, Download=False)


def play(item):
    support.log()
    data = support.match(item).data
    match = support.match(data, patron='/content/entry/data/(.*?).mp4').match
    if match:
        url = 'https://awsvodpkg.iltrovatore.it/local/hls/,/content/entry/data/' + support.match(item, patron='/content/entry/data/(.*?).mp4').match + '.mp4.urlset/master.m3u8'
        item = item.clone(title='Direct', url=url, server='directo', action='play')
    else:
        preurl = support.match(data, patron=r'preTokenUrl = "(.+?)"').match
        url = support.match(data, patron=r'["]?dash["]?\s*:\s*"([^"]+)"').match
        tokenHeader = {
            'host': headers['host_token'],
            'user-agent': headers['user-agent'],
            'accept': headers['accept'],
            'accept-language': headers['accept-language'],
            'dnt': headers['dnt'],
            'te': headers['te'],
            'origin': headers['origin'],
            'referer': headers['referer'],
        }
        preAuthToken = requests.get(preurl, headers=tokenHeader,verify=False).json()['preAuthToken']
        licenseHeader = {
            'host': headers['host_license'],
            'user-agent': headers['user-agent'],
            'accept': headers['accept'],
            'accept-language': headers['accept-language'],
            'preAuthorization': preAuthToken,
            'origin': headers['origin'],
            'referer': headers['referer'],
        }
        preLic= '&'.join(['%s=%s' % (name, value) for (name, value) in licenseHeader.items()])
        tsatmp=str(int(support.time()))
        license_url= key_widevine + '?d=%s'%tsatmp
        lic_url='%s|%s|R{SSM}|'%(license_url, preLic)
        item.drm = DRM
        item.license = lic_url
    return support.servertools.find_video_items(item, data=url)
