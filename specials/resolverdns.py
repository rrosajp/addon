# -*- coding: utf-8 -*-
# -*- CLOUDFLARE'S DNS -*-

##from lib import dns
##import dns.resolver
##from dns.resolver import override_system_resolver
##import socket
##import requests
##
##def dns_resolver():
##    res = dns.resolver.Resolver(configure=True)
##    res.nameservers = ['1.1.1.1', '2606:4700:4700::1111',
##                       '1.0.0.1', '2606:4700:4700::1001']
##    override_system_resolver(res)

## Da prevedere di aggiungere la possibilità
## di inserire i dns a piacere degli utenti!!!

from lib import dns
import dns.resolver
from dns.resolver import override_system_resolver
import dns.name
import socket
import requests

res = dns.resolver.Resolver(configure=False)

res.nameservers = ['1.1.1.1', '2606:4700:4700::1111',
                   '1.0.0.1', '2606:4700:4700::1001' ]

override_system_resolver(res)
