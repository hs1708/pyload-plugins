# -*- coding: utf-8 -*-

from module.plugins.internal.SimpleCrypter import SimpleCrypter

import pycurl
import re


class ShSt(SimpleCrypter):
    __name__    = "ShSt"
    __type__    = "crypter"
    __version__ = "0.02"

    __pattern__ = r'http://sh\.st/\w+'

    __description__ = """Sh.St decrypter plugin"""
    __license__     = "GPLv3"
    __authors__     = [("Frederik Möllers", "fred-public@posteo.de")]


    NAME_PATTERN = r'<title>(?P<N>.+?) - .+</title>'


    def decrypt(self, pyfile):
        # if we use curl as a user agent, we will get a straight redirect (no waiting!)
        self.req.http.c.setopt(pycurl.USERAGENT, "curl/7.42.1")
        # fetch the target URL
        header = self.load(self.pyfile.url, just_header = True, decode = False)
        target_url = header["location"]
        self.urls.append(target_url)
