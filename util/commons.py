import re
import json
import os
from datetime import datetime
from pprint import pprint
from time import sleep
import numpy as np
from random import random
import code  # code.interact(local=dict(globals(), **locals()))
'''
These regular expression are used to verify that the experiment parameters,
encoded in the log filename, comply with an expected format (or belong to a closed set of options)
'''
namesurnamecode = re.compile("^[a-zA-Z]{1,20}$")
capcode = re.compile("^[0-9]{5}$")
alphanumeric = re.compile("\w+$")
access_technologies = ['3G', '4G', '5G', 'FTTC', 'FTTH', 'ADSL', 'FWA']
points_of_access = ['HOME', 'MOBILE', 'UNIBS', 'OTHER']
local_techs = ['WIFI', 'ETHERNET', 'HOTSPOT', 'TETHERING']
countrycode = re.compile("^[A-Z]{2}$")

QDNregex = re.compile("([\w-]+\.)+\w+")
IPv4regex = re.compile("([0-9]+.[0-9]+.[0-9]+.[0-9]+)")
IPv6regex = re.compile("(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$|^(([a-zA-Z]|[a-zA-Z][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z]|[A-Za-z][A-Za-z0-9\-]*[A-Za-z0-9])$|^\s*((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))(%.+)?\s*")

class Pingable:
    def __init__(self, ip, fqdn, countryCode, more, qdn=None):
        if not fqdn:
            fqdn = "Unknown"
        if not qdn:
            qdn = "Unknown"
        self.ip = ip
        self.fqdn = fqdn
        self.countryCode = countryCode
        self.more = more
        self.qdn = qdn

    def __str__(self):
        return "{}--> {}\t({})".format(self.ip.ljust(16), self.qdn.ljust(26), self.countryCode)

    def nickname(self):
        string = self.ip
        for ch in ['.',':']: 
            if ch in string:
                string = string.replace(ch, "-")
        return string