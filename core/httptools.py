# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# httptools
# Based on code from https://github.com/alfa-addon/
# --------------------------------------------------------------------------------

try:
    import urllib.request as urllib
    import urllib.parse as urlparse
    import http.cookiejar as cookielib
except ImportError:
    import urllib, urlparse, cookielib


import inspect, os, time, json
from threading import Lock
from core.jsontools import to_utf8
from platformcode import config, logger
from platformcode.logger import WebErrorException
from core import scrapertoolsV2

# Get the addon version
__version = config.get_addon_version()

cookies_lock = Lock()

cj = cookielib.MozillaCookieJar()
cookies_file = os.path.join(config.get_data_path(), "cookies.dat")

# Headers by default, if nothing is specified
default_headers = dict()
default_headers["User-Agent"] = "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"
default_headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"
default_headers["Accept-Language"] = "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3"
default_headers["Accept-Charset"] = "UTF-8"
default_headers["Accept-Encoding"] = "gzip"

# Maximum wait time for downloadpage, if nothing is specified
HTTPTOOLS_DEFAULT_DOWNLOAD_TIMEOUT = config.get_setting('httptools_timeout', default=15)
if HTTPTOOLS_DEFAULT_DOWNLOAD_TIMEOUT == 0: HTTPTOOLS_DEFAULT_DOWNLOAD_TIMEOUT = None

# Random use of User-Agents, if nad is not specified
HTTPTOOLS_DEFAULT_RANDOM_HEADERS = False

def get_user_agent():
    # Returns the global user agent to be used when necessary for the url.
    return default_headers["User-Agent"]

def get_url_headers(url, forced=False):
    domain = urlparse.urlparse(url)[1]
    sub_dom = scrapertoolsV2.find_single_match(domain, r'\.(.*?\.\w+)')
    if sub_dom and not 'google' in url:
        domain = sub_dom
    domain_cookies = cj._cookies.get("." + domain, {}).get("/", {})

    if "|" in url or not "cf_clearance" in domain_cookies:
        if not forced:
            return url

    headers = dict()
    headers["User-Agent"] = default_headers["User-Agent"]
    headers["Cookie"] = "; ".join(["%s=%s" % (c.name, c.value) for c in domain_cookies.values()])

    return url + "|" + "&".join(["%s=%s" % (h, urllib.quote(headers[h])) for h in headers])

def set_cookies(dict_cookie, clear=True, alfa_s=False):
    """
    View a specific cookie in cookies.dat
    @param dict_cookie: dictionary where the cookie parameters are obtained
        The dict must contain:
        name: cookie name
        value: its value / content
        domain: domain to which the cookie points
        optional:
        expires: life time in seconds, if not used add 1 day (86400s)
    @type dict_cookie: dict

    @param clear: True = delete cookies from the domain, before adding the new one (necessary for cloudproxy, cp)
                  False = disabled by default, just update the cookie
    @type clear: bool
    """

    # The cookie will be given a default day of life
    expires_plus = dict_cookie.get('expires', 86400)
    ts = int(time.time())
    expires = ts + expires_plus

    name = dict_cookie.get('name', '')
    value = dict_cookie.get('value', '')
    domain = dict_cookie.get('domain', '')

    # We delete existing cookies in that domain (cp)
    if clear:
        try:
            cj.clear(domain)
        except:
            pass

    ck = cookielib.Cookie(version=0, name=name, value=value, port=None,
                    port_specified=False, domain=domain,
                    domain_specified=False, domain_initial_dot=False,
                    path='/', path_specified=True, secure=False,
                    expires=expires, discard=True, comment=None, comment_url=None,
                    rest={'HttpOnly': None}, rfc2109=False)

    cj.set_cookie(ck)
    save_cookies()

def load_cookies(alfa_s=False):
    cookies_lock.acquire()
    if os.path.isfile(cookies_file):
        if not alfa_s: logger.info("Reading cookies file")
        try:
            cj.load(cookies_file, ignore_discard=True)
        except:
            if not alfa_s: logger.info("The cookie file exists but is illegible, it is deleted")
            os.remove(cookies_file)
    cookies_lock.release()


def save_cookies(alfa_s=False):
    cookies_lock.acquire()
    if not alfa_s: logger.info("Saving cookies...")
    cj.save(cookies_file, ignore_discard=True)
    cookies_lock.release()


load_cookies()

def random_useragent():
    """
    Based on code from https://github.com/theriley106/RandomHeaders
    Python Method that generates fake user agents with a locally saved DB (.csv file).
    This is useful for webscraping, and testing programs that identify devices based on the user agent.
    """

    import random

    UserAgentPath = os.path.join(config.get_runtime_path(), 'tools', 'UserAgent.csv')
    if os.path.exists(UserAgentPath):
        UserAgentIem = random.choice(list(open(UserAgentPath))).strip()
        if UserAgentIem:
            return UserAgentIem

    return default_headers["User-Agent"]

def channel_proxy_list(url, forced_proxy=None):
    import base64
    import ast

    try:
        proxy_channel_bloqued_str = base64.b64decode(config.get_setting
                ('proxy_channel_bloqued')).decode('utf-8')
        proxy_channel_bloqued = dict()
        proxy_channel_bloqued = ast.literal_eval(proxy_channel_bloqued_str)
    except:
        logger.debug('Proxytools not initialized correctly')
        return False

    if not url.endswith('/'):
        url += '/'
    if scrapertoolsV2.find_single_match(url, r'(?:http.*\:)?\/\/(?:www\.)?([^\?|\/]+)(?:\?|\/)') \
                in proxy_channel_bloqued:
        if forced_proxy and forced_proxy not in ['Total', 'ProxyDirect', 'ProxyCF', 'ProxyWeb']:
            if forced_proxy in proxy_channel_bloqued[scrapertoolsV2.find_single_match(url, r'(?:http.*\:)?\/\/(?:www\.)?([^\?|\/]+)(?:\?|\/)')]:
                return True
            else:
                return False
        if forced_proxy:
            return True
        if not 'OFF' in proxy_channel_bloqued[scrapertoolsV2.find_single_match(url, r'(?:http.*\:)?\/\/(?:www\.)?([^\?|\/]+)(?:\?|\/)')]:
            return True

    return False

def show_infobox(info_dict):
    logger.info()
    from textwrap import wrap

    box_items_kodi = {'r_up_corner': u'\u250c',
                      'l_up_corner': u'\u2510',
                      'center': u'\u2502',
                      'r_center': u'\u251c',
                      'l_center': u'\u2524',
                      'fill': u'\u2500',
                      'r_dn_corner': u'\u2514',
                      'l_dn_corner': u'\u2518',
                      }

    box_items = {'r_up_corner': '+',
                 'l_up_corner': '+',
                 'center': '|',
                 'r_center': '+',
                 'l_center': '+',
                 'fill': '-',
                 'r_dn_corner': '+',
                 'l_dn_corner': '+',
                 }



    width = 60
    version = '%s: %s' % (config.get_localized_string(20000), __version)
    if config.is_xbmc():
        box = box_items_kodi
    else:
        box = box_items

    logger.info('%s%s%s' % (box['r_up_corner'], box['fill'] * width, box['l_up_corner']))
    logger.info('%s%s%s' % (box['center'], version.center(width), box['center']))
    logger.info('%s%s%s' % (box['r_center'], box['fill'] * width, box['l_center']))

    count = 0
    for key, value in info_dict:
        count += 1
        text = '%s: %s' % (key, value)

        if len(text) > (width - 2):
            text = wrap(text, width)
        else:
            text = text.ljust(width, ' ')
        if isinstance(text, list):
            for line in text:
                if len(line) < width:
                    line = line.ljust(width, ' ')
                logger.info('%s%s%s' % (box['center'], line, box['center']))
        else:
            logger.info('%s%s%s' % (box['center'], text, box['center']))
        if count < len(info_dict):
            logger.info('%s%s%s' % (box['r_center'], box['fill'] * width, box['l_center']))
        else:
            logger.info('%s%s%s' % (box['r_dn_corner'], box['fill'] * width, box['l_dn_corner']))
    return

def check_proxy(url, **opt):
    proxy_data = dict()
    proxy_data['dict'] = {}
    proxy = opt.get('proxy', True)
    proxy_web = opt.get('proxy_web', False)
    proxy_addr_forced = opt.get('proxy_addr_forced', None)
    forced_proxy = opt.get('forced_proxy', None)

    try:
        if (proxy or proxy_web) and (forced_proxy or proxy_addr_forced or
                                     channel_proxy_list(url, forced_proxy=forced_proxy)):
            import proxytools
            proxy_data['addr'], proxy_data['CF_addr'], proxy_data['web_name'], \
            proxy_data['log'] = proxytools.get_proxy_addr(url, post=opt.get('post', None), forced_proxy=forced_proxy)

            if proxy_addr_forced and proxy_data['log']:
                proxy_data['log'] = scrapertoolsV2.find_single_match(str(proxy_addr_forced), r"{'http.*':\s*'(.*?)'}")

            if proxy and proxy_data['addr']:
                if proxy_addr_forced: proxy_data['addr'] = proxy_addr_forced
                proxy_data['dict'] = proxy_data['addr']
                proxy_data['stat'] = ', Proxy Direct ' + proxy_data['log']
            elif proxy and proxy_data['CF_addr']:
                if proxy_addr_forced: proxy_data['CF_addr'] = proxy_addr_forced
                proxy_data['dict'] = proxy_data['CF_addr']
                proxy_data['stat'] = ', Proxy CF ' + proxy_data['log']
            elif proxy and proxy_addr_forced:
                proxy_data['addr'] = proxy_addr_forced
                proxy_data['dict'] = proxy_data['addr']
                proxy_data['stat'] = ', Proxy Direct ' + proxy_data['log']
            elif proxy and not proxy_data['addr'] and not proxy_data['CF_addr'] \
                    and not proxy_addr_forced:
                proxy = False
                if not proxy_data['web_name']:
                    proxy_data['addr'], proxy_data['CF_addr'], proxy_data['web_name'], \
                    proxy_data['log'] = proxytools.get_proxy_addr(url, forced_proxy='Total')
                if proxy_data['web_name']:
                    proxy_web = True
                else:
                    proxy_web = False
                    if proxy_data['addr']:
                        proxy = True
                        proxy_data['dict'] = proxy_data['addr']
                        proxy_data['stat'] = ', Proxy Direct ' + proxy_data['log']

            if proxy_web and proxy_data['web_name']:
                if opt.get('post', None): proxy_data['log'] = '(POST) ' + proxy_data['log']
                url, opt['post'], headers_proxy, proxy_data['web_name'] = \
                    proxytools.set_proxy_web(url, proxy_data['web_name'], post=opt.get('post', None))
                if proxy_data['web_name']:
                    proxy_data['stat'] = ', Proxy Web ' + proxy_data['log']
                    if headers_proxy:
                        request_headers.update(dict(headers_proxy))
            if proxy_web and not proxy_data['web_name']:
                proxy_web = False
                proxy_data['addr'], proxy_data['CF_addr'], proxy_data['web_name'], \
                proxy_data['log'] = proxytools.get_proxy_addr(url, forced_proxy='Total')
                if proxy_data['CF_addr']:
                    proxy = True
                    proxy_data['dict'] = proxy_data['CF_addr']
                    proxy_data['stat'] = ', Proxy CF ' + proxy_data['log']
                elif proxy_data['addr']:
                    proxy = True
                    proxy_data['dict'] = proxy_data['addr']
                    proxy_data['stat'] = ', Proxy Direct ' + proxy_data['log']

    except:
        import traceback
        logger.error(traceback.format_exc())
        opt['proxy'] = ''
        opt['proxy_web'] = ''
        proxy_data['stat'] = ''
        proxy_data['addr'] = ''
        proxy_data['CF_addr'] = ''
        proxy_data['dict'] = {}
        proxy_data['web_name'] = ''
        proxy_data['log'] = ''
        url = opt['url_save']
    try:
        proxy_data['addr']['https'] = str('https://'+ proxy_data['addr']['https'])
    except:
        pass
    return url, proxy_data, opt


def proxy_post_processing(url, proxy_data, response, opt):
    opt['out_break'] = False
    try:
        if ', Proxy Web' in proxy_data.get('stat', ''):
            import proxytools
            response["data"] = proxytools.restore_after_proxy_web(response["data"],
                                                                  proxy_data['web_name'], opt['url_save'])
            if response["data"] == 'ERROR':
                response['sucess'] = False
            if response["code"] == 302:
                proxy_data['stat'] = ', Proxy Direct'
                opt['forced_proxy'] = 'ProxyDirect'
                url = opt['url_save']
                opt['post'] = opt['post_save']
                response['sucess'] = False

        if proxy_data.get('stat', '') and response['sucess'] == False and \
                opt.get('proxy_retries_counter', 0) <= opt.get('proxy_retries', 1) and opt.get('count_retries_tot', 5) > 1:
            import proxytools
            if ', Proxy Direct' in proxy_data.get('stat', ''):
                proxytools.get_proxy_list_method(proxy_init='ProxyDirect',
                                                 error_skip=proxy_data['addr'], url_test=url)
            elif ', Proxy CF' in proxy_data.get('stat', ''):
                proxytools.get_proxy_list_method(proxy_init='ProxyCF',
                                                 error_skip=proxy_data['CF_addr'])
                url = opt['url_save']
            elif ', Proxy Web' in proxy_data.get('stat', ''):
                if channel_proxy_list(opt['url_save'], forced_proxy=proxy_data['web_name']):
                    opt['forced_proxy'] = 'ProxyCF'
                    url =opt['url_save']
                    opt['post'] = opt['post_save']
                else:
                    proxytools.get_proxy_list_method(proxy_init='ProxyWeb',
                                                     error_skip=proxy_data['web_name'])
                    url =opt['url_save']
                    opt['post'] = opt['post_save']

        else:
            opt['out_break'] = True
    except:
        import traceback
        logger.error(traceback.format_exc())
        opt['out_break'] = True

    return response["data"], response['sucess'], url, opt



def downloadpage(url, **opt):
    logger.info()
    """
       Open a url and return the data obtained

        @param url: url to open.
        @type url: str
        @param post: If it contains any value, it is sent by POST.
        @type post: str
        @param headers: Headers for the request, if it contains nothing the default headers will be used.
        @type headers: dict, list
        @param timeout: Timeout for the request.
        @type timeout: int
        @param follow_redirects: Indicates if redirects are to be followed.
        @type follow_redirects: bool
        @param cookies: Indicates whether cookies are to be used.
        @type cookies: bool
        @param replace_headers: If True, headers passed by the "headers" parameter will completely replace the default headers.
                                If False, the headers passed by the "headers" parameter will modify the headers by default.
        @type replace_headers: bool
        @param add_referer: Indicates whether to add the "Referer" header using the domain of the url as a value.
        @type add_referer: bool
        @param only_headers: If True, only headers will be downloaded, omitting the content of the url.
        @type only_headers: bool
        @param random_headers: If True, use the method of selecting random headers.
        @type random_headers: bool
        @param ignore_response_code: If True, ignore the method for WebErrorException for error like 404 error in veseriesonline, but it is a functional data
        @type ignore_response_code: bool
        @return: Result of the petition
        @rtype: HTTPResponse
        @param use_requests: Use requests.session()
        @type: bool

                Parameter Type Description
                -------------------------------------------------- -------------------------------------------------- ------------
                HTTPResponse.sucess: bool True: Request successful | False: Error when making the request
                HTTPResponse.code: int Server response code or error code if an error occurs
                HTTPResponse.error: str Description of the error in case of an error
                HTTPResponse.headers: dict Dictionary with server response headers
                HTTPResponse.data: str Response obtained from server
                HTTPResponse.json: dict Response obtained from the server in json format
                HTTPResponse.time: float Time taken to make the request

        """
    load_cookies()
    if config.get_setting('resolver_dns'):
        from specials import resolverdns
        session = resolverdns.session()
    else:
        if opt.get('session', False):
            session = opt['session']  # same session to speed up search
            logger.info('same session')
        elif opt.get('use_requests', False):
            from lib import requests
            session = requests.session()
        else:
            from lib import cloudscraper
            session = cloudscraper.create_scraper()

    req_headers = default_headers.copy()

    # Headers passed as parameters
    if opt.get('headers', None) is not None:
        if not opt.get('replace_headers', False):
            req_headers.update(dict(opt['headers']))
        else:
            req_headers = dict(opt['headers'])

    if opt.get('random_headers', False) or HTTPTOOLS_DEFAULT_RANDOM_HEADERS:
        req_headers['User-Agent'] = random_useragent()
    url = urllib.quote(url, safe="%/:=&?~#+!$,;'@()*[]")

    opt['proxy_retries_counter'] = 0
    opt['url_save'] = url
    opt['post_save'] = opt.get('post', None)

    while opt['proxy_retries_counter'] <= opt.get('proxy_retries', 1):
        response = {}
        info_dict = []
        payload = dict()
        files = {}
        file_name = ''
        opt['proxy_retries_counter'] += 1

        session.verify = opt.get('verify', True)

        if opt.get('cookies', True):
            session.cookies = cj
        session.headers.update(req_headers)

        # Prepare the url in case you need a proxy, or if proxies are sent from the channel
        # url, proxy_data, opt = check_proxy(url, **opt)
        # if opt.get('proxies', None) is not None:
        #     session.proxies = opt['proxies']
        # elif proxy_data.get('dict', {}):
        #     session.proxies = proxy_data['dict']
        proxy_data = {'dict': {}}

        inicio = time.time()

        if opt.get('timeout', None) is None and HTTPTOOLS_DEFAULT_DOWNLOAD_TIMEOUT is not None:
            opt['timeout'] = HTTPTOOLS_DEFAULT_DOWNLOAD_TIMEOUT
        if opt['timeout'] == 0: opt['timeout'] = None

        if len(url) > 0:
            try:
                if opt.get('post', None) is not None or opt.get('file', None) is not None:
                    if opt.get('post', None) is not None:
                        # Convert string post in dict
                        try:
                            json.loads(opt['post'])
                            payload = opt['post']
                        except:
                            if not isinstance(opt['post'], dict):
                                post = urlparse.parse_qs(opt['post'], keep_blank_values=1)
                                payload = dict()

                                for key, value in post.items():
                                    try:
                                        payload[key] = value[0]
                                    except:
                                        payload[key] = ''
                            else:
                                payload = opt['post']

                    # Verify 'file' and 'file_name' options to upload a buffer or file
                    if opt.get('file', None) is not None:
                        if os.path.isfile(opt['file']):
                            if opt.get('file_name', None) is None:
                                path_file, opt['file_name'] = os.path.split(opt['file'])
                            files = {'file': (opt['file_name'], open(opt['file'], 'rb'))}
                            file_name = opt['file']
                        else:
                            files = {'file': (opt.get('file_name', 'Default'), opt['file'])}
                            file_name = opt.get('file_name', 'Default') + ', Buffer de memoria'

                    info_dict = fill_fields_pre(url, opt, proxy_data, file_name)
                    if opt.get('only_headers', False):
                        # Makes the request with HEAD method
                        req = session.head(url, allow_redirects=opt.get('follow_redirects', True),
                                          timeout=opt['timeout'])
                    else:
                        # Makes the request with POST method
                        req = session.post(url, data=payload, allow_redirects=opt.get('follow_redirects', True),
                                          files=files, timeout=opt['timeout'])

                elif opt.get('only_headers', False):
                    info_dict = fill_fields_pre(url, opt, proxy_data, file_name)
                    # Makes the request with HEAD method
                    req = session.head(url, allow_redirects=opt.get('follow_redirects', True),
                                      timeout=opt['timeout'])
                else:
                    info_dict = fill_fields_pre(url, opt, proxy_data, file_name)
                    # Makes the request with GET method
                    req = session.get(url, allow_redirects=opt.get('follow_redirects', True),
                                      timeout=opt['timeout'])
            except Exception as e:
                from lib import requests
                if not opt.get('ignore_response_code', False) and not proxy_data.get('stat', ''):
                    req = requests.Response()
                    response['data'] = ''
                    response['sucess'] = False
                    info_dict.append(('Success', 'False'))
                    response['code'] = str(e)
                    info_dict.append(('Response code', str(e)))
                    info_dict.append(('Finalizado en', time.time() - inicio))
                    if not opt.get('alfa_s', False):
                        show_infobox(info_dict)
                    return type('HTTPResponse', (), response)
                else:
                    req = requests.Response()
                    req.status_code = str(e)

        else:
            response['data'] = ''
            response['sucess'] = False
            response['code'] = ''
            return type('HTTPResponse', (), response)

        response_code = req.status_code

        response['data'] = req.content
        response['url'] = req.url
        if not response['data']:
            response['data'] = ''
        try:
            response['json'] = to_utf8(req.json())
        except:
            response['json'] = dict()
        response['code'] = response_code
        response['headers'] = req.headers
        response['cookies'] = req.cookies

        info_dict, response = fill_fields_post(info_dict, req, response, req_headers, inicio)

        if opt.get('cookies', True):
            save_cookies(alfa_s=opt.get('alfa_s', False))

        # is_channel = inspect.getmodule(inspect.currentframe().f_back)
        # is_channel = scrapertoolsV2.find_single_match(str(is_channel), "<module '(channels).*?'")
        # if is_channel and isinstance(response_code, int):
        #     if not opt.get('ignore_response_code', False) and not proxy_data.get('stat', ''):
        #         if response_code > 399:
        #             show_infobox(info_dict)
        #             raise WebErrorException(urlparse.urlparse(url)[1])

        if not 'api.themoviedb' in url and not opt.get('alfa_s', False):
            show_infobox(info_dict)

        # If there is a proxy error, refresh the list and retry the number indicated in proxy_retries
        # response['data'], response['sucess'], url, opt = proxy_post_processing(url, proxy_data, response, opt)
        # if opt.get('out_break', False):
        #     break

    return type('HTTPResponse', (), response)

def fill_fields_pre(url, opt, proxy_data, file_name):
    info_dict = []

    try:
        info_dict.append(('Timeout', opt['timeout']))
        info_dict.append(('URL', url))
        info_dict.append(('Domain', urlparse.urlparse(url)[1]))
        if opt.get('post', None):
            info_dict.append(('Petition', 'POST' + proxy_data.get('stat', '')))
        else:
            info_dict.append(('Petition', 'GET' + proxy_data.get('stat', '')))
        info_dict.append(('Download Page', not opt.get('only_headers', False)))
        if file_name: info_dict.append(('Upload File', file_name))
        info_dict.append(('Use cookies', opt.get('cookies', True)))
        info_dict.append(('Cookie file', cookies_file))
    except:
        import traceback
        logger.error(traceback.format_exc(1))

    return info_dict


def fill_fields_post(info_dict, req, response, req_headers, inicio):
    try:
        info_dict.append(('Cookies', req.cookies))
        info_dict.append(('Data Encoding', req.encoding))
        info_dict.append(('Response code', response['code']))

        if response['code'] == 200:
            info_dict.append(('Success', 'True'))
            response['sucess'] = True
        else:
            info_dict.append(('Success', 'False'))
            response['sucess'] = False

        info_dict.append(('Response data length', len(response['data'])))

        info_dict.append(('Request Headers', ''))
        for header in req_headers:
            info_dict.append(('- %s' % header, req_headers[header]))

        info_dict.append(('Response Headers', ''))
        for header in response['headers']:
            info_dict.append(('- %s' % header, response['headers'][header]))
        info_dict.append(('Finished in', time.time() - inicio))
    except:
        import traceback
        logger.error(traceback.format_exc(1))

    return info_dict, response
