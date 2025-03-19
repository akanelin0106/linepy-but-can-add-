# -*- coding: utf-8 -*-
class Callback(object):

    def __init__(self, callback):
        self.callback = callback

    def PinVerified(self, pin):
        self.callback("朱音API登入驗證碼: " + pin )

    def QrUrl(self, url, showQr=False):
        if showQr:
            notice='or scan this QR '
        else:
            notice=''
        self.callback('Login ' + notice + 'URL:\n' + url)
        if showQr:
            try:
                import pyqrcode
                url = pyqrcode.create(url)
                self.callback(url.terminal('green', 'white', 1))
            except:
                pass

    def default(self, str):
        self.callback(str)