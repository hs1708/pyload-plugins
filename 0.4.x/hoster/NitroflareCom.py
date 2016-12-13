# -*- coding: utf-8 -*-

import re

from module.network.RequestFactory import getURL as get_url
from module.plugins.captcha.ReCaptcha import ReCaptcha
from module.plugins.internal.misc import json
from module.plugins.internal.SimpleHoster import SimpleHoster


class NitroflareCom(SimpleHoster):
    __name__    = "NitroflareCom"
    __type__    = "hoster"
    __version__ = "0.22"
    __status__  = "testing"

    __pattern__ = r'https?://(?:www\.)?nitroflare\.com/view/(?P<ID>[\w^_]+)'
    __config__  = [("activated"   , "bool", "Activated"                                        , True),
                   ("use_premium" , "bool", "Use premium account if available"                 , True),
                   ("fallback"    , "bool", "Fallback to free download if premium fails"       , True),
                   ("chk_filesize", "bool", "Check file size"                                  , True),
                   ("max_wait"    , "int" , "Reconnect if waiting time is greater than minutes", 10  )]

    __description__ = """Nitroflare.com hoster plugin"""
    __license__     = "GPLv3"
    __authors__     = [("sahil"         , "sahilshekhawat01@gmail.com"),
                       ("Walter Purcaro", "vuolter@gmail.com"         ),
                       ("Stickell"      , "l.stickell@yahoo.it"       ),
                       ("GammaC0de",      "nitzo2001[AT]yahoo[DOT]com")]

    INFO_PATTERN    = r'title="(?P<N>.+?)".+>(?P<S>[\d.,]+) (?P<U>[\w^_]+)'
    OFFLINE_PATTERN = r'>File doesn\'t exist'

    LINK_PREMIUM_PATTERN = LINK_FREE_PATTERN = r'(https?://[\w\-]+\.nitroflare\.com/.+?)"'
    FILE_ID_PATTERN = r'https?://(?:www\.)?nitroflare\.com/view/(?P<ID>[\w^_]+)'
    DIRECT_LINK = False

    RECAPTCHA_KEY        = "6Lenx_USAAAAAF5L1pmTWvWcH73dipAEzNnmNLgy"
    PREMIUM_ONLY_PATTERN = r'This file is available with Premium only'
    WAIT_PATTERN         = r'You have to wait (\d+ minutes)'
    # ERROR_PATTERN        = r'downloading is not possible'


    @classmethod
    def api_info(cls, url):
        info    = {}
        file_id = re.search(cls.__pattern__, url).group('ID')

        data = json.loads(get_url("https://nitroflare.com/api/v2/getFileInfo",
                                  get={'files': file_id},
                                  decode=True))

        if data['type'] == 'success':
            fileinfo = data['result']['files'][file_id]
            info['status'] = 2 if fileinfo['status'] == 'online' else 1
            info['name']   = fileinfo['name']
            info['size']   = fileinfo['size']  #: In bytes

        return info


    def handle_free(self, pyfile):
        #: Used here to load the cookies which will be required later
        self.load("http://nitroflare.com/ajax/setCookie.php",
                  post={'fileId': self.info['pattern']['ID']})

        self.load(pyfile.url, post={'goToFreePage': ""})

        self.data = self.load("http://nitroflare.com/ajax/freeDownload.php",
                              post={'method': "startTimer",
                                    'fileId': self.info['pattern']['ID']})

        self.check_errors()

        try:
            js_file   = self.load("http://nitroflare.com/js/downloadFree.js?v=1.0.1")
            var_time  = re.search(r'var time = (\d+);', js_file).group(1)
            wait_time = int(var_time)

        except Exception:
            wait_time = 60

        self.wait(wait_time)

        self.captcha = ReCaptcha(pyfile)
        response, challenge = self.captcha.challenge(self.RECAPTCHA_KEY)

        self.data = self.load("http://nitroflare.com/ajax/freeDownload.php",
                              post={'method'                   : "fetchDownload",
                                    'recaptcha_challenge_field': challenge,
                                    'recaptcha_response_field' : response})

        if "The captcha wasn't entered correctly" in self.data:
            self.retry_captcha()

        return super(NitroflareCom, self).handle_free(pyfile)


    def handle_premium(self, pyfile):
        data = json.loads(self.load("https://nitroflare.com/api/v2/getDownloadLink",
                                    get={'file'      : self.info['pattern']['ID'],
                                         'user'      : self.account.user,
                                         'premiumKey': self.account.get_login('password')}))

        if data['type'] == 'success':
            pyfile.name = data['result']['name']
            pyfile.size = int(data['result']['size'])
            self.link   = data['result']['url']