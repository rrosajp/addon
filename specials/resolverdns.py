# -*- coding: utf-8 -*-
# -*- OVERRIDE RESOLVE DNS -*-

from platformcode import config

if config.get_setting('resolver_dns'):
    import xbmc
    from lib import dns
    from dns import resolver, name
    from dns.resolver import override_system_resolver
    from core import support

    support.log("platform Android: {}".format(xbmc.getCondVisibility('System.Platform.Android')))
    if xbmc.getCondVisibility('System.Platform.Android') == True:
        res = resolver.Resolver(filename='/system/etc/resolv.conf', configure=True)
        #res = resolver.Resolver(filename='/system/etc/dhcpcd/dhcpcd-hooks/20-dns.conf', configure=True)
    else:
        res = resolver.Resolver(configure=True)
    #legge le impostazioni dalla configurazione e setta i relativi DNS
    if config.get_setting('resolver_dns_custom') and not config.get_setting('resolver_dns_service_choose'):
        res.nameservers = [config.get_setting('resolver_dns_custom1'),config.get_setting('resolver_dns_custom2')]
    else:
        nameservers_dns = config.get_setting('resolver_dns_service')
        if nameservers_dns == 1:# 'Google'
            res.nameservers = ['8.8.8.8', '2001:4860:4860::8888',
                               '8.8.4.4', '2001:4860:4860::8844']
        elif nameservers_dns == 2:#'OpenDns Home ip(v4)'
            res.nameservers = ['208.67.222.222', '208.67.222.220']
        elif nameservers_dns == 3:#'OpenDns Family Shield ip(v4)':
            res.nameservers = ['208.67.222.123', '208.67.220.123']
        elif nameservers_dns == 4:#'OpenDns ip(v6)'
            #https://support.opendns.com/hc/en-us/articles/227986667-Does-OpenDNS-Support-IPv6-
            res.nameservers = ['2620:119:35::35', '2620:119:53::53']
        else:#if nameservers_dns == 0:#'Cloudflare'
            res.nameservers = ['1.1.1.1', '2606:4700:4700::1111',
                               '1.0.0.1', '2606:4700:4700::1001']
    # log di verifica dei DNS impostati, d'aiuto quando gli utenti smanettano...
    support.log("NAME SERVER: {}".format(res.nameservers))

    override_system_resolver(res)
