# -*- coding: utf-8 -*-
import os
import ssl

import xbmc

from core import jsontools
from lib.requests_toolbelt.adapters import host_header_ssl

from lib import requests, doh
from platformcode import logger, config
import re
try:
    import _sqlite3 as sql
except:
    import sqlite3 as sql

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

db = os.path.join(config.get_data_path(), 'kod_db.sqlite')

class session(requests.Session):
    def __init__(self):
        self.conn = sql.connect(db)
        self.cur = self.conn.cursor()
        super(session, self).__init__()

    def getIp(self, domain):
        import time
        t = time.time()
        ip = None
        try:
            self.cur.execute('select ip from dnscache where domain=?', (domain,))
            ip = self.cur.fetchall()[0][0]
        except:
            pass
        if not ip:  # not cached
            try:
                ip = doh.query(domain)[0]
                logger.info('Query DoH: ' + domain + ' = ' + str(ip))
                self.writeToCache(domain, ip)
            except Exception:
                logger.error('Failed to resolve hostname, fallback to normal dns')
                import traceback
                logger.error(traceback.print_exc())
                ip = [domain]
        logger.info('tempo getIP: ' + str(time.time()-t))
        return ip

    def writeToCache(self, domain, ip):
        try:
            self.cur.execute('insert into dnscache values(?,?)', (domain, ip))
        except:
            self.cur.execute("""CREATE TABLE IF NOT EXISTS dnscache(
                    "domain"	TEXT NOT NULL UNIQUE,
                    "ip"	TEXT NOT NULL,
                    PRIMARY KEY("domain")
                );""")
        self.conn.commit()

    def flushDns(self, method, realUrl, domain, **kwargs):
        self.cur.execute('delete from dnscache where domain=?', (domain,))
        self.conn.commit()
        return self.request(method, realUrl, flushedDns=True, **kwargs)

    def request(self, method, url, headers=None, flushedDns=False, **kwargs):
        import time
        t = time.time()
        protocol, domain, port, resource = re.match(r'^(http[s]?:\/\/)?([^:\/\s]+)(?::([^\/]*))?([^\s]*)$', url, flags=re.IGNORECASE).groups()
        self.mount('https://', CipherSuiteAdapter(domain, cipherSuite="ALL"))
        realUrl = url
        ip = self.getIp(domain)

        if headers:
            headers["Host"] = domain
        else:
            headers = {"Host": domain}

        ret = None
        tryFlush = False
        url = protocol + ip + (':' + port if port else '') + resource
        try:
            ret = super(session, self).request(method, url, headers=headers, **kwargs)
        except:
            logger.info('Request for ' + domain + ' with ip ' + ip + ' failed')
            tryFlush = True
        if (tryFlush or not ret) and not flushedDns:  # re-request ips and update cache
            logger.info('Flushing dns cache for ' + domain)
            return self.flushDns(method, realUrl, domain, **kwargs)
        logger.info('tempo dns: ' + str(time.time()-t))
        return ret
