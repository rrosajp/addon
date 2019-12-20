# -*- coding: utf-8 -*-
import ssl

from requests_toolbelt.adapters import host_header_ssl

from lib import requests, doh
from platformcode import logger
import re

class CustomSocket(ssl.SSLSocket):
    def __init__(self, *args, **kwargs):
        super(CustomSocket, self).__init__(*args, **kwargs)

class CustomContext(ssl.SSLContext):
    def __init__(self, protocol, hostname, *args, **kwargs):
        self.hostname = hostname
        super(CustomContext, self).__init__(protocol)
    def wrap_socket(self, sock, server_side=False,
                    do_handshake_on_connect=True,
                    suppress_ragged_eofs=True,
                    server_hostname=None):
        return CustomSocket(sock=sock, server_side=server_side,
                         do_handshake_on_connect=do_handshake_on_connect,
                         suppress_ragged_eofs=suppress_ragged_eofs,
                         server_hostname=self.hostname,
                         _context=self)

class CipherSuiteAdapter(host_header_ssl.HostHeaderSSLAdapter):

    def __init__(self, hostname, *args, **kwargs):
        self.ssl_context = kwargs.pop('ssl_context', None)
        self.cipherSuite = kwargs.pop('cipherSuite', None)
        self.hostname = hostname

        if not self.ssl_context:
            self.ssl_context = CustomContext(ssl.PROTOCOL_TLS, hostname)
            self.ssl_context.set_ciphers(self.cipherSuite)

        super(CipherSuiteAdapter, self).__init__(**kwargs)

    # ------------------------------------------------------------------------------- #

    def init_poolmanager(self, *args, **kwargs):
        kwargs['ssl_context'] = self.ssl_context
        return super(CipherSuiteAdapter, self).init_poolmanager(*args, **kwargs)

    # ------------------------------------------------------------------------------- #

    def proxy_manager_for(self, *args, **kwargs):
        kwargs['ssl_context'] = self.ssl_context
        return super(CipherSuiteAdapter, self).proxy_manager_for(*args, **kwargs)

# ------------------------------------------------------------------------------- #

class session(requests.Session):
    def request(self, method, url,
            params=None, data=None, headers=None, cookies=None, files=None,
            auth=None, timeout=None, allow_redirects=True, proxies=None,
            hooks=None, stream=None, verify=None, cert=None, json=None):
        protocol, domain, port, resource = re.match('^(http[s]?:\/\/)?([^:\/\s]+)(?::([^\/]*))?([^\s]+)$', url, flags=re.IGNORECASE).groups()
        self.mount('https://', CipherSuiteAdapter(domain, cipherSuite="ALL"))
        try:
            ip = doh.query(domain)
            logger.info('Query DoH: ' + domain + ' = ' + str(ip))
            url = protocol + ip[0] + (':' + port if port else '') + resource
        except Exception:
            logger.error('Failed to resolve hostname, fallback to normal dns')
            import traceback
            logger.error(traceback.print_exc())
        if headers:
            headers["Host"] = domain
        else:
            headers = {"Host": domain}
        return super(session, self).request(method, url,
                                        params, data, headers, cookies, files,
                                        auth, timeout, allow_redirects, proxies,
                                        hooks, stream, verify, cert, json)
