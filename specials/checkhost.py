# -*- coding: utf-8 -*-
import xbmc, xbmcgui
import xbmcaddon
import json
from platformcode import config, logger
import requests
from requests.exceptions import HTTPError

addon = xbmcaddon.Addon()
addonname = addon.getAddonInfo('name')
addonid = addon.getAddonInfo('id')

LIST_SITE = ['https://www.google.com', 'https://www.google.it',
                'http://www.ansa.it/', 'https://www.debian.org/']

# lista di siti che non verranno raggiunti con i DNS del gestore
LST_SITE_CHCK_DNS = ['https://www.italia-film.pw', 'https://casacinema.space',
                     'https://filmsenzalimiti.best']


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
            xbmc.log("check_Adsl rslt: %s" % rslt['code'], level=xbmc.LOGNOTICE)
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
        xbmc.log("check_Dns risultato: %s" % r, level=xbmc.LOGNOTICE)
        http_errr = 0
        for rslt in r:
            xbmc.log("check_Dns rslt: %s" % rslt['code'], level=xbmc.LOGNOTICE)
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
        rslt_final = []
        
        if lst_urls == []:
            lst_urls = self.lst_urls
            
        for sito in lst_urls:
            rslt = {}
            try:
                r = requests.head(sito, allow_redirects = True, timeout=7)
                if r.url.endswith('/'):
                    r.url = r.url[:-1]
                if str(sito) != str(r.url):
                    is_redirect = True
                else:
                    is_redirect = False

                rslt['code'] = r.status_code
                rslt['url'] = str(sito)
                rslt['rdrcturl'] = str(r.url)
                rslt['isRedirect'] = is_redirect
                rslt['history'] = r.history
                xbmc.log("Risultato nel try: %s" %  (r,), level=xbmc.LOGNOTICE)
                
            except requests.exceptions.ConnectionError as conn_errr:
                # Errno 10061 per s.o. win
                # gli Errno 10xxx e 11xxx saranno da compattare in qualche modo?
                # gli errori vengono inglobati in code = '111' in quanto in quel momento
                # non vengono raggiunti per una qualsiasi causa
                if '[Errno 111]' in str(conn_errr) or 'Errno 10061' in str(conn_errr) \
                     or 'ConnectTimeoutError' in str(conn_errr) \
                     or 'Errno 11002' in str(conn_errr) or 'ReadTimeout' in str(conn_errr) \
                     or 'Errno 11001' in str(conn_errr): # questo errore è anche nel code: -2
                    # nei casi in cui vogliamo raggiungere certi siti...
                    rslt['code'] = '111'
                    rslt['url'] = str(sito)
                    rslt['http_err'] = 'Connection refused'
                else:
                    rslt['code'] = conn_errr
                    rslt['url'] = str(sito)
                    rslt['http_err'] = 'Connection refused'
            rslt_final.append(rslt)

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
            txt += '\nIP: %s' % self.ip_addr

##        if self.in_addon == False and self.view_msg == True:
        dialog = xbmcgui.Dialog()
        dialog.textviewer(addonname, txt)

"""
    def richiamato in launcher.py
"""
def test_conn(is_exit, check_dns, view_msg,
              lst_urls, lst_site_check_dns, in_addon):
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
            # inserire codice lingua
            ktest.view_Advise(config.get_localized_string(70720))
        if ktest.is_exit == True:
            exit()

    elif not ktest.check_Adsl():
        if view_msg == True:
            # inserire codice lingua
            ktest.view_Advise(config.get_localized_string(70721))
        if ktest.is_exit == True:
            exit()

    elif ktest.check_dns:
        if not ktest.check_Dns():
            if view_msg == True:
                # inserire codice lingua
                ktest.view_Advise(config.get_localized_string(70722))
##            if ktest.is_exit == True:
##                exit()

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
