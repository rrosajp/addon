# -*- coding: utf-8 -*-
# -*- OVERRIDE RESOLVE DNS -*-

from platformcode import config
from core import support

active_dns = config.get_setting('resolver_dns')

if active_dns == True:

    from lib import dns
    import dns.resolver
    from dns.resolver import override_system_resolver
    import dns.name
    import socket
    import requests

    res = dns.resolver.Resolver(configure=True)

    """
        legge le impostazioni dalla configurazione
        e setta i relativi DNS
    """
    nameservers_dns = config.get_setting('resolver_dns_service')

    if nameservers_dns == 'Google':
        res.nameservers_dns = ['8.8.8.8', '2001:4860:4860::8888',
                       '8.8.4.4', '2001:4860:4860::8844' ]
    elif nameservers_dns == 'OpenDns':
        res.nameservers_dns = ['208.67.222.222', '2620:119:35::35',
                       '208.67.222.220', '2620:119:53::53' ]
    else:# resolver_dns_service == 'Cloudflare':
        res.nameservers = ['1.1.1.1', '2606:4700:4700::1111',
                       '1.0.0.1', '2606:4700:4700::1001' ]

    override_system_resolver(res)


