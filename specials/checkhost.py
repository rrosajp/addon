# -*- coding: utf-8 -*-
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
import xbmc
import xbmcaddon
import json
from platformcode import logger
from kdicc import test_conn


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
