## Modded version of cloudscrape 1.1.24
## https://github.com/venomous/cloudscraper


import logging
import re
import sys
import ssl
import requests

from copy import deepcopy
from time import sleep
from collections import OrderedDict

from requests.sessions import Session
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.ssl_ import create_urllib3_context

from .interpreters import JavaScriptInterpreter
from .reCaptcha import reCaptcha
from .user_agent import User_Agent

try:
    from requests_toolbelt.utils import dump
except ImportError:
    pass

try:
    import brotli
except ImportError:
    pass

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

##########################################################################################################################################################

__version__ = '1.1.24'

BUG_REPORT = 'Cloudflare may have changed their technique, or there may be a bug in the script.'

##########################################################################################################################################################


# class CipherSuiteAdapter(HTTPAdapter):
#
#     def __init__(self, cipherSuite=None, **kwargs):
#         self.cipherSuite = cipherSuite
#
#         self.ssl_context = create_urllib3_context(
#             ssl_version=ssl.PROTOCOL_TLS,
#             ciphers=self.cipherSuite
#         )
#
#         super(CipherSuiteAdapter, self).__init__(**kwargs)
class CipherSuiteAdapter(HTTPAdapter):

    def __init__(self, cipherSuite=None, **kwargs):
        self.cipherSuite = cipherSuite

        if hasattr(ssl, 'PROTOCOL_TLS'):
            self.ssl_context = create_urllib3_context(
                ssl_version=getattr(ssl, 'PROTOCOL_TLSv1_3', ssl.PROTOCOL_TLSv1_2),
                ciphers=self.cipherSuite
            )
        else:
            self.ssl_context = create_urllib3_context(ssl_version=ssl.PROTOCOL_TLSv1)

        super(CipherSuiteAdapter, self).__init__(**kwargs)

    ##########################################################################################################################################################

    def init_poolmanager(self, *args, **kwargs):
        kwargs['ssl_context'] = self.ssl_context
        return super(CipherSuiteAdapter, self).init_poolmanager(*args, **kwargs)

    ##########################################################################################################################################################

    def proxy_manager_for(self, *args, **kwargs):
        kwargs['ssl_context'] = self.ssl_context
        return super(CipherSuiteAdapter, self).proxy_manager_for(*args, **kwargs)

##########################################################################################################################################################


class CloudScraper(Session):
    def __init__(self, *args, **kwargs):
        self.allow_brotli = kwargs.pop('allow_brotli', True if 'brotli' in sys.modules.keys() else False)
        self.debug = kwargs.pop('debug', False)
        self.delay = kwargs.pop('delay', None)
        self.interpreter = kwargs.pop('interpreter', 'js2py')
        self.recaptcha = kwargs.pop('recaptcha', {})

        self.cipherSuite = None

        super(CloudScraper, self).__init__(*args, **kwargs)

        if 'requests' in self.headers['User-Agent']:
            # Set a random User-Agent if no custom User-Agent has been set
            self.headers = User_Agent(allow_brotli=self.allow_brotli).headers

        self.mount('https://', CipherSuiteAdapter(self.loadCipherSuite()))

    ##########################################################################################################################################################

    @staticmethod
    def debugRequest(req):
        try:
            print(dump.dump_all(req).decode('utf-8'))
        except:  # noqa
            pass

    ##########################################################################################################################################################

    def loadCipherSuite(self):
        if self.cipherSuite:
            return self.cipherSuite

        self.cipherSuite = ''

        if hasattr(ssl, 'PROTOCOL_TLS'):
            ciphers = [
                'TLS13-AES-128-GCM-SHA256',
                'TLS13-AES-256-GCM-SHA384',
                'TLS13-CHACHA20-POLY1305-SHA256',
                'ECDHE-ECDSA-CHACHA20-POLY1305',
                'ECDHE-ECDSA-AES128-GCM-SHA256',
                'ECDHE-ECDSA-AES128-SHA',
                'ECDHE-ECDSA-AES128-SHA256',
                'ECDHE-ECDSA-AES256-GCM-SHA384',
                'ECDHE-ECDSA-AES256-SHA',
                'ECDHE-ECDSA-AES256-SHA384',
                # Slip in some additional intermediate compatibility ciphers, This should help out users for non Cloudflare based sites.
                'ECDHE-RSA-AES128-SHA256',
                'ECDHE-RSA-AES256-SHA384',
                'ECDHE-RSA-AES256-GCM-SHA384',
                'DHE-RSA-AES128-GCM-SHA256',
                'DHE-RSA-AES256-GCM-SHA384'
            ]

            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS)

            for cipher in ciphers:
                try:
                    ctx.set_ciphers(cipher)
                    self.cipherSuite = '{}:{}'.format(self.cipherSuite, cipher).rstrip(':').lstrip(':')
                except ssl.SSLError:
                    pass

        return self.cipherSuite

    ##########################################################################################################################################################

    def request(self, method, url, *args, **kwargs):
        ourSuper = super(CloudScraper, self)
        resp = ourSuper.request(method, url, *args, **kwargs)

        if requests.packages.urllib3.__version__ < '1.25.1' and resp.headers.get('Content-Encoding') == 'br':
            if self.allow_brotli and resp._content:
                resp._content = brotli.decompress(resp.content)
            else:
                logging.warning('Brotli content detected, But option is disabled, we will not continue.')
                return resp

        # Debug request
        if self.debug:
            self.debugRequest(resp)

        # Check if Cloudflare anti-bot is on
        if self.isChallengeRequest(resp):
            if resp.request.method != 'GET':
                # Work around if the initial request is not a GET,
                # Supersede with a GET then re-request the original METHOD.
                self.request('GET', resp.url)
                resp = ourSuper.request(method, url, *args, **kwargs)
            else:
                # Solve Challenge
                resp = self.sendChallengeResponse(resp, **kwargs)

        return resp

    ##########################################################################################################################################################
    # ------------------------------------------------------------------------------- #
    # check if the response contains a valid Cloudflare reCaptcha challenge
    # ------------------------------------------------------------------------------- #

    @staticmethod
    def is_reCaptcha_Challenge(resp):
        try:
            return (
                resp.headers.get('Server', '').startswith('cloudflare')
                and resp.status_code == 403
                and re.search(
                    r'action="/.*?__cf_chl_captcha_tk__=\S+".*?data\-sitekey=.*?',
                    resp.text,
                    re.M | re.DOTALL
                )
            )
        except AttributeError:
            pass

        return False

    @staticmethod
    def isChallengeRequest(resp):
        if resp.headers.get('Server', '').startswith('cloudflare'):
            return (
                resp.status_code in [403, 429, 503]
                and (
                    all(s in resp.content for s in [b'jschl_vc', b'jschl_answer'])
                    or
                    all(s in resp.content for s in [b'why_captcha', b'/cdn-cgi/l/chk_captcha'])
                )
            )

        return False


    # ------------------------------------------------------------------------------- #
    # Try to solve cloudflare javascript challenge.
    # ------------------------------------------------------------------------------- #

    @staticmethod
    def IUAM_Challenge_Response(body, domain, interpreter):
        try:
            challengeUUID = re.search(
                r'__cf_chl_jschl_tk__=(?P<challengeUUID>\S+)"',
                body, re.M | re.DOTALL
            ).groupdict().get('challengeUUID')
            params = OrderedDict(re.findall(r'name="(r|jschl_vc|pass)"\svalue="(.*?)"', body))
        except AttributeError:
            sys.tracebacklimit = 0
            raise RuntimeError("Cloudflare IUAM detected, unfortunately we can't extract the parameters correctly.")

        try:
            params['jschl_answer'] = JavaScriptInterpreter.dynamicImport(
                interpreter
            ).solveChallenge(body, domain)
        except Exception as e:
            raise RuntimeError(
                'Unable to parse Cloudflare anti-bots page: {}'.format(
                    getattr(e, 'message', e)
                )
            )

        return {
            'url': 'https://{}/'.format(domain),
            'params': {'__cf_chl_jschl_tk__': challengeUUID},
            'data': params
        }

    @staticmethod
    def reCaptcha_Challenge_Response(provider, provider_params, body, url):
        try:
            params = re.search(
                r'(name="r"\svalue="(?P<r>\S+)"|).*?__cf_chl_captcha_tk__=(?P<challengeUUID>\S+)".*?'
                r'data-ray="(?P<data_ray>\S+)".*?data-sitekey="(?P<site_key>\S+)"',
                body, re.M | re.DOTALL
            ).groupdict()
        except (AttributeError):
            sys.tracebacklimit = 0
            raise RuntimeError(
                "Cloudflare reCaptcha detected, unfortunately we can't extract the parameters correctly."
            )

        return {
            'url': url,
            'params': {'__cf_chl_captcha_tk__': params.get('challengeUUID')},
            'data': OrderedDict([
                ('r', ''),
                ('id', params.get('data_ray')),
                (
                    'g-recaptcha-response',
                    reCaptcha.dynamicImport(
                        provider.lower()
                    ).solveCaptcha(url, params.get('site_key'), provider_params)
                )
            ])
        }

    ##########################################################################################################################################################

    def sendChallengeResponse(self, resp, **original_kwargs):
        if self.is_reCaptcha_Challenge(resp):
            # ------------------------------------------------------------------------------- #
            # double down on the request as some websites are only checking
            # if cfuid is populated before issuing reCaptcha.
            # ------------------------------------------------------------------------------- #

            resp = self.decodeBrotli(
                super(CloudScraper, self).request(resp.request.method, resp.url, **original_kwargs)
            )

            if not self.is_reCaptcha_Challenge(resp):
                return resp

            # ------------------------------------------------------------------------------- #
            # if no reCaptcha provider raise a runtime error.
            # ------------------------------------------------------------------------------- #

            if not self.recaptcha or not isinstance(self.recaptcha, dict) or not self.recaptcha.get('provider'):
                sys.tracebacklimit = 0
                raise RuntimeError(
                    "Cloudflare reCaptcha detected, unfortunately you haven't loaded an anti reCaptcha provider "
                    "correctly via the 'recaptcha' parameter."
                )

            # ------------------------------------------------------------------------------- #
            # if provider is return_response, return the response without doing anything.
            # ------------------------------------------------------------------------------- #

            if self.recaptcha.get('provider') == 'return_response':
                return resp

            self.recaptcha['proxies'] = self.proxies
            submit_url = self.reCaptcha_Challenge_Response(
                self.recaptcha.get('provider'),
                self.recaptcha,
                resp.text,
                resp.url
            )
        else:
            # ------------------------------------------------------------------------------- #
            # Cloudflare requires a delay before solving the challenge
            # ------------------------------------------------------------------------------- #

            if not self.delay:
                try:
                    delay = float(
                        re.search(
                            r'submit\(\);\r?\n\s*},\s*([0-9]+)',
                            resp.text
                        ).group(1)
                    ) / float(1000)
                    if isinstance(delay, (int, float)):
                        self.delay = delay
                except (AttributeError, ValueError):
                    sys.tracebacklimit = 0
                    raise RuntimeError("Cloudflare IUAM possibility malformed, issue extracing delay value.")

            sleep(self.delay)

            # ------------------------------------------------------------------------------- #

            submit_url = self.IUAM_Challenge_Response(
                resp.text,
                urlparse(resp.url).netloc,
                self.interpreter
            )

        # ------------------------------------------------------------------------------- #
        # Send the Challenge Response back to Cloudflare
        # ------------------------------------------------------------------------------- #

        if submit_url:
            def updateAttr(obj, name, newValue):
                try:
                    obj[name].update(newValue)
                    return obj[name]
                except (AttributeError, KeyError):
                    obj[name] = {}
                    obj[name].update(newValue)
                    return obj[name]

            cloudflare_kwargs = deepcopy(original_kwargs)
            cloudflare_kwargs['allow_redirects'] = False
            cloudflare_kwargs['params'] = updateAttr(cloudflare_kwargs, 'params', submit_url['params'])
            cloudflare_kwargs['data'] = updateAttr(cloudflare_kwargs, 'data', submit_url['data'])
            cloudflare_kwargs['headers'] = updateAttr(cloudflare_kwargs, 'headers', {'Referer': resp.url})

            self.request(
                'POST',
                submit_url['url'],
                **cloudflare_kwargs
            )

        # ------------------------------------------------------------------------------- #
        # Request the original query request and return it
        # ------------------------------------------------------------------------------- #

        return self.request(resp.request.method, resp.url, **original_kwargs)

        # ------------------------------------------------------------------------------- #
        # Request the original query request and return it
        # ------------------------------------------------------------------------------- #

        # return self.request(resp.request.method, resp.url, **kwargs)
    # ------------------------------------------------------------------------------- #

    ##########################################################################################################################################################

    @classmethod
    def create_scraper(cls, sess=None, **kwargs):
        """
        Convenience function for creating a ready-to-go CloudScraper object.
        """
        scraper = cls(**kwargs)

        if sess:
            attrs = ['auth', 'cert', 'cookies', 'headers', 'hooks', 'params', 'proxies', 'data']
            for attr in attrs:
                val = getattr(sess, attr, None)
                if val:
                    setattr(scraper, attr, val)

        return scraper

    ##########################################################################################################################################################

    # Functions for integrating cloudscraper with other applications and scripts
    @classmethod
    def get_tokens(cls, url, **kwargs):
        scraper = cls.create_scraper(
            debug=kwargs.pop('debug', False),
            delay=kwargs.pop('delay', None),
            interpreter=kwargs.pop('interpreter', 'js2py'),
            allow_brotli=kwargs.pop('allow_brotli', True),
            recaptcha=kwargs.pop('recaptcha', {})
        )

        try:
            resp = scraper.get(url, **kwargs)
            resp.raise_for_status()
        except Exception:
            logging.error('"{}" returned an error. Could not collect tokens.'.format(url))
            raise

        domain = urlparse(resp.url).netloc
        # noinspection PyUnusedLocal
        cookie_domain = None

        for d in scraper.cookies.list_domains():
            if d.startswith('.') and d in ('.{}'.format(domain)):
                cookie_domain = d
                break
        else:
            raise ValueError('Unable to find Cloudflare cookies. Does the site actually have Cloudflare IUAM ("I\'m Under Attack Mode") enabled?')

        return (
            {
                '__cfduid': scraper.cookies.get('__cfduid', '', domain=cookie_domain),
                'cf_clearance': scraper.cookies.get('cf_clearance', '', domain=cookie_domain)
            },
            scraper.headers['User-Agent']
        )

    ##########################################################################################################################################################

    @classmethod
    def get_cookie_string(cls, url, **kwargs):
        """
        Convenience function for building a Cookie HTTP header value.
        """
        tokens, user_agent = cls.get_tokens(url, **kwargs)
        return '; '.join('='.join(pair) for pair in tokens.items()), user_agent


##########################################################################################################################################################

create_scraper = CloudScraper.create_scraper
get_tokens = CloudScraper.get_tokens
get_cookie_string = CloudScraper.get_cookie_string
