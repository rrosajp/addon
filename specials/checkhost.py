# -*- coding: utf-8 -*-
"""
    sito con lista errori:
    https://www.evemilano.com/status-code/

    Tabella errori:
    [Errno 11001] := sito non esistente
    [Errno 11002] := sito non esistente o non raggiungibile in quel momento (DNS)

    500 := Internal Server Error
    503 := Service Unavailable

    Cloudflare:
    521 := Web Server Is Down
    522 := Connection Timed Out
    523 := Origin Is Unreachable

    ReadTimeout(ReadTimeoutError("HTTPSConnectionPool(host='italiafilm.info', port=443): Read timed out. (read timeout=7)"
    in browser diventa errore 522...Problema di cloudflare
"""

import xbmc, xbmcgui
import xbmcaddon
import json
from platformcode import logger
import requests
from requests.exceptions import HTTPError
import socket

addon = xbmcaddon.Addon()
addonname = addon.getAddonInfo('name')
addonid = addon.getAddonInfo('id')
#pluginname = 'script.module.kdicc'

LIST_SITE = ['https://www.wikipedia.it', 'https://www.google.it',
                'https://www.yahoo.it', 'https://www.debian.it']

# lista di siti che non verranno raggiunti se con i DNS del gestore
LST_SITE_CHCK_DNS = ['https://www.italia-film.pw', 'https://casacinema.space',
                     'https://filmsenzalimiti.best']

"""
        raggiungibilità dei siti in base al s.o. e gestore
        https://github.com/greko17/kdicc/wiki/Raggiungibilit%C3%A0-siti-in-base-al-so-e-gestore
"""


class Kdicc():
    
    def __init__(self, is_exit = True, check_dns = True, view_msg = True,
                 lst_urls = [], lst_site_check_dns = [], in_addon = False):

        self.ip_addr = xbmc.getIPAddress()
        self.dns = [xbmc.getInfoLabel('Network.DNS1Address'),
                    xbmc.getInfoLabel('Network.DNS2Address')]
        self.check_dns = check_dns
        self.is_exit = is_exit
        self.lst_urls = lst_urls
        self.view_msg = view_msg
        self.lst_site_check_dns = lst_site_check_dns
        self.urls = []
##        self.in_addon = in_addon
##        self.server_dns = xbmc.getInfoLabel('Network.DHCPAddress') # stringa vuota...
##        self.gateway = xbmc.getInfoLabel('Network.GatewayAddress')
##        self.subnet = xbmc.getInfoLabel('Network.SubnetMask')


    def check_Ip(self):
        """
            controllo l'ip
            se ip_addr = 127.0.0.1 o ip_addr = '' allora il device non
            e' connesso al modem/router
            
            check the ip
            if ip_addr = 127.0.0.1 or ip_addr = '' then the device does not
            is connected to the modem/router

            return: bool
        """
        if self.ip_addr == '127.0.0.1' or self.ip_addr == '':
            return False
        else:
            return True


    def check_Adsl(self):
        """
            controllo se il device raggiunge i siti
        """
        
        urls = LIST_SITE
        r = self.rqst(urls)
        http_errr = 0
        for rslt in r:
##            xbmc.log("check_Adsl rslt: %s" % rslt['code'], level=xbmc.LOGNOTICE)
            if rslt['code'] == '111':
                http_errr +=1

        if len(LIST_SITE) == http_errr:
            return False
        else:
            return True


    def check_Dns(self):
        """
            Controllo se i DNS raggiungono certi siti
        """
        if self.lst_site_check_dns == []:
            urls = LST_SITE_CHCK_DNS
        else:
            urls = self.lst_site_check_dns

        r = self.rqst(urls)
##        xbmc.log("check_Dns risultato: %s" % r, level=xbmc.LOGNOTICE)
        http_errr = 0
        for rslt in r:
##            xbmc.log("check_Dns rslt: %s" % rslt['code'], level=xbmc.LOGNOTICE)
            if rslt['code'] == '111':
                http_errr +=1

        if len(LST_SITE_CHCK_DNS) == http_errr:
            return False
        else:
            return True


    def rqst(self, lst_urls):
        """
            url deve iniziare con http(s):'
            return : (esito, sito, url, code, reurl)
        """
##        xbmc.log("LST_URLS : %s" % lst_urls, level=xbmc.LOGNOTICE)
        rslt_final = []
        
        if lst_urls == []:
            lst_urls = self.lst_urls
            
        for sito in lst_urls:
            rslt = {}
            try:
##                r = requests.get(sito, allow_redirects=True)
                r = requests.head(sito, allow_redirects = True, timeout=7)
                if r.url.endswith('/'):
                    r.url = r.url[:-1]
                if str(sito) != str(r.url):
                    is_redirect = True
                else:
                    is_redirect = False
                #xbmc.log("rslt json : %s " %  (r.json()), level=xbmc.LOGNOTICE)

                rslt['code'] = r.status_code
                rslt['url'] = str(sito)
                rslt['rdrcturl'] = str(r.url)
                rslt['isRedirect'] = is_redirect
                rslt['history'] = r.history
##                xbmc.log("Risultato nel try: %s" %  (r,), level=xbmc.LOGNOTICE)
            except requests.exceptions.HTTPError as http_err:
                # 522 Server Error: Origin Connection Time-out for url: https://italiafilm.info/
                # Errore : 404 Client Error: NOT FOUND for url: http://httpbin.org/status/404
##                xbmc.log("http_err : %s " % http_err, level=xbmc.LOGNOTICE)

                rslt['code'] = r.status_code    
                rslt['url'] = str(sito)
                rslt['http_err'] = http_err
                rslt['history'] = r.history
                
            except requests.exceptions.ConnectionError as conn_errr:
                # HTTPSConnectionPool(host='www.yahoo.minkia', port=443): Max retries
                # exceeded with url: /(Caused by NewConnectionError
                # ('<urllib3.connection.VerifiedHTTPSConnection object at 0x7f96f7506d50>:
                # Failed to establish a new connection: [Errno -2] Name or service not known',))
##                xbmc.log("conn_errr : %s " % conn_errr, level=xbmc.LOGNOTICE)
                
                if '[Errno -2]' in str(conn_errr) or 'Errno 7' in str(conn_errr) \
                    or 'Errno 11001' in str(conn_errr):
                    # il sito non esiste!!!
                    # Failed to establish a new connection: [Errno 7] errore android
                    rslt['code'] = '-2'
                    rslt['url'] = str(sito)
                    rslt['http_err'] = 'unknown host'

                elif '[Errno 110]' in str(conn_errr):
                    rslt['code'] = '110'
                    rslt['url'] = str(sito)
                    rslt['http_err'] = 'Connection timed out'

                # Errno 10061 per s.o. win
                # gli Errno 10xxx e 11xxx saranno da compattare in qualche modo?
                # gli errori vengono inglobati in code = '111' in quanto in quel momento
                # non vengono raggiunti per una qualsiasi causa
                elif '[Errno 111]' in str(conn_errr) or 'Errno 10061' in str(conn_errr) \
                     or 'ConnectTimeoutError' in str(conn_errr) \
                     or 'Errno 11002' in str(conn_errr) or 'ReadTimeout' in str(conn_errr) \
                     or 'Errno 11001' in str(conn_errr):
                    # nei casi in cui vogliamo raggiungere certi siti...
                    rslt['code'] = '111'
                    rslt['url'] = str(sito)
                    rslt['http_err'] = 'Connection refused'
                else:
                    rslt['code'] = conn_errr
                    rslt['url'] = str(sito)
                    rslt['http_err'] = 'Connection refused'
##                    rslt['history'] = r.history

            except requests.exceptions.RequestException as other_err:
##                xbmc.log("other_err: %s " % other_err, level=xbmc.LOGNOTICE)
                rslt['code'] = other_err
                rslt['url'] = str(sito)
##                rslt['history'] = r.history

            rslt_final.append(rslt)
##        xbmc.log("rslt_final: %s " % rslt_final, level=xbmc.LOGNOTICE)
##        if self.check_dns == True:
##            return rslt_final
        return rslt_final


    def view_Advise(self, txt = '' ):
        """
            Avviso per utente
            testConnected
        """
        ip = self.check_Ip()
        if ip:
            txt += '\nIP: %s\n' % self.ip_addr
            txt += '\nDNS: %s\n' % (self.dns)
        else:
            # inserire codice lingua
            txt += '\nIP: %s' % self.ip_addr

##        if self.in_addon == False and self.view_msg == True:
        dialog = xbmcgui.Dialog()
        dialog.textviewer(addonname, txt)

"""
    def richiamato in launcher.py
"""
def test_conn(self, is_exit = True, check_dns = True, view_msg = True,
                 lst_urls = [], lst_site_check_dns = [], in_addon = False):
    # debug
    # import web_pdb; web_pdb.set_trace()
    
    ktest = Kdicc(is_exit, check_dns, view_msg, lst_urls, lst_site_check_dns, in_addon)
    # se non ha l'ip lo comunico all'utente
    # è utile nelle richieste di aiuto per l'addon che non funziona
    # If you don't have an ip, I'll let you know.
    # Is useful in requests for help for the addon that does not work
    risultato = []

    if not ktest.check_Ip():
        # non permetto di entrare nell'addon
        # I don't let you get into the addon
        # inserire codice lingua
        if view_msg == True:
            ktest.view_Advise('Gentile Utente,\nAttualmente non risulti connesso a nessun modem/router. \
Non puoi accedere a KOD poichè i canali non saranno raggiungibili! \
Ti consigliamo di controllare quanto meno che il modem/router \
sia acceso e/o il tuo dispositivo connesso.\n')
        if ktest.is_exit == True:
            exit()

    elif not ktest.check_Adsl():
        if view_msg == True:
            ktest.view_Advise('Gentile Utente, sembra tu abbia problemi con l\'ADSL! \
Non puoi accedere a KOD poichè i canali non saranno raggiungibili! \
Ti consigliamo di chiamare il numero verde del tuo gestore o di controllare \
quanto meno che il modem/router sia acceso e/o il tuo dispositivo connesso.\n')
        if ktest.is_exit == True:
            exit()

    elif ktest.check_dns:
        if not ktest.check_Dns():
            if view_msg == True:
                ktest.view_Advise('Gentile Utente, i tuoi DNS attuali non ti permettono di raggiungere tutti i siti \
 ergo, non tutti i Canali funzioneranno. Ti consigliamo per usufruire di un maggior numero \
 di canali di impostare i DNS. Cerca su google o contatta ALHAZIEL per una consulenza gratuita!\n')
            if ktest.is_exit == True:
                exit()

##    else:
    # Lasciando solo else al posto dell'if sotto, l'else non viene considerato!
##    if ktest.check_Ip() and ktest.check_Adsl() and ktest.check_Dns():
##        # tutto ok! entro nell'addon
##        if view_msg == True and in_addon == False:
##            ktest.view_Advise('Configurazione rete OK!\n')

##    for ris in ktest.rqst(lst_urls):
##        risultato.append(ris)

    return risultato

# def per la creazione del file channels.json
"""
    leggo gli host dei canali dal file channels.json
    li controllo
    scrivo il file channels-test.json
    con i codici di errore e i nuovi url in caso di redirect

    gli url DEVONO avere http(s)

    Durante il controllo degli url vengono rieffettuati
    i controlli di ip, asdl e dns.
    Questo perchè può succedere che in un qualsiasi momento
    la connessione può avere problemi.
    Nel caso accada un problema, il controllo e relativa scrittura del file viene interrotto
    con messaggio di avvertimento

"""
def check(item):
    logger.info()

    folderJson = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('path')).decode('utf-8')
    fileJson = 'channels.json'    

    with open(folderJson+'/'+fileJson) as f:
        data = json.load(f)
##    logger.info("DATA :%s" % data)

    risultato = {}

    for chann, host in sorted(data.items()):
        ris = []
        logger.info("check #### INIZIO #### channel - host :%s - %s " % (chann, host))

        #lst_host = []
        #lst_host.append(host)
        lst_host = [host]

        rslt = test_conn(is_exit = True, check_dns = False, view_msg = True,
                         lst_urls = lst_host, lst_site_check_dns = [], in_addon = True)

        logger.info("check #### FINE #### rslt :%s  " % (rslt))
        rslt = rslt[0]
        # tutto ok
        if rslt['code'] == 200 and rslt['isRedirect'] == False:
            risultato[chann] = host
        # redirect
        elif rslt['code'] == 200 and rslt['isRedirect'] == True: 
            risultato[chann] = str(rslt['code']) +' - '+ rslt['rdrcturl']
        # sito inesistente
        elif rslt['code'] == -2:
            risultato[chann] = 'Host Sconosciuto - '+ str(rslt['code']) +' - '+ host
        else:
            # altri tipi di errore
            risultato[chann] = 'Errore Sconosciuto - '+str(rslt['code']) +' - '+ host

    fileJson_test = 'channels-test.json'
    # scrivo il file aggiornato
    with open(folderJson+'/'+fileJson_test, 'w') as f:
        data = json.dump(risultato, f, sort_keys=True, indent=4)
        logger.info(data)
