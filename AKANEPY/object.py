# -*- coding: utf-8 -*-
from datetime import datetime
import json, time, ntpath
import hashlib
import time
from base64 import b64encode
import uuid
import urllib
import httpx
def loggedIn(func):
    def checkLogin(*args, **kwargs):
        if args[0].isLogin:
            return func(*args, **kwargs)
        else:
            args[0].callback.default('You want to call the function, you must login to LINE')
    return checkLogin
    
class Object(object):

    def __init__(self):
        if self.isLogin == True:
            pass

    """Group"""

    @loggedIn
    def updateGroupPicture(self, groupId, path):
        files = {'file': open(path, 'rb')}
        data = {'params': self.genOBSParams({'oid': groupId,'type': 'image'})}
        r = self.server.postContent(self.server.LINE_OBS_DOMAIN + '/talk/g/upload.nhn', data=data, files=files)
        if r.status_code != 201:
            raise Exception('Update group picture failure.')
        return True

    """Personalize"""

    @loggedIn
    def updateProfilePicture(self, path, type='p'):
        files = {'file': open(path, 'rb')}
        params = {'oid': self.profile.mid,'type': 'image'}
        if type == 'vp':
            params.update({'ver': '2.0', 'cat': 'vp.mp4'})
        data = {'params': self.genOBSParams(params)}
        r = self.server.postContent(self.server.LINE_OBS_DOMAIN + '/talk/p/upload.nhn', data=data, files=files)
        if r.status_code != 201:
            raise Exception('Update profile picture failure.')
        return True
        
    @loggedIn
    def updateProfileVideoPicture(self, path):
        try:
            from ffmpy import FFmpeg
            files = {'file': open(path, 'rb')}
            data = {'params': self.genOBSParams({'oid': self.profile.mid,'ver': '2.0','type': 'video','cat': 'vp.mp4'})}
            r_vp = self.server.postContent(self.server.LINE_OBS_DOMAIN + '/talk/vp/upload.nhn', data=data, files=files)
            if r_vp.status_code != 201:
                raise Exception('Update profile video picture failure.')
            path_p = self.genTempFile('path')
            ff = FFmpeg(inputs={'%s' % path: None}, outputs={'%s' % path_p: ['-ss', '00:00:2', '-vframes', '1']})
            ff.run()
            self.updateProfilePicture(path_p, 'vp')
        except:
            raise Exception('You should install FFmpeg and ffmpy from pypi')

    @loggedIn
    def updateVideoAndPictureProfile(self, path_p, path, returnAs='bool'):
        if returnAs not in ['bool']:
            raise Exception('Invalid returnAs value')
        files = {'file': open(path, 'rb')}
        data = {'params': self.genOBSParams({'oid': self.profile.mid,'ver': '2.0','type': 'video','cat': 'vp.mp4'})}
        r_vp = self.server.postContent(self.server.LINE_OBS_DOMAIN + '/talk/vp/upload.nhn', data=data, files=files)
        if r_vp.status_code != 201:
            raise Exception('Update profile video picture failure.')
        self.updateProfilePicture(path_p, 'vp')
        if returnAs == 'bool':
            return True
    @loggedIn
    def updateProfileCover(self, path, storyShare=False):
        hstr = "DearSakura_%s" % int(time.time() * 1000)
        objId = hashlib.md5(hstr.encode()).hexdigest()
        obsPath = f"myhome/c/{objId}"
        oType = "IMAGE"
        filename = f"{objId}.jpg"
        params = None
        try:
            objId, objHash, respHeaders = self.uploadObjectForService(
                path, oType, obsPath, "1341209850", params, filename=filename
            )
            print(respHeaders)
        except Exception as e:
            raise Exception(e)
        home = self.updateProfileCoverById(objId, storyShare=storyShare)
        return home
    @loggedIn
    def updateProfileCover1(self, path, returnAs='bool'):
        if returnAs not in ['objId','bool']:
            raise Exception('Invalid returnAs value')
        objId = self.uploadObjHome(path, type='image', returnAs='objId')
        home = self.updateProfileCoverById(objId)
        if returnAs == 'objId':
            return objId
        elif returnAs == 'bool':
            return True

    """Object"""

    @loggedIn
    def uploadObjSquare(self, squareChatMid, path, type='image', returnAs='bool', name=None):
        if returnAs not in ['bool']:
            raise Exception('Invalid returnAs value')
        if type not in ['image','gif','video','audio','file']:
            raise Exception('Invalid type value')
        try:
            import magic
        except ImportError:
            raise Exception('You must install python-magic from pip')
        mime = magic.Magic(mime=True)
        contentType = mime.from_file(path)
        data = open(path, 'rb').read()
        params = {
            'name': '%s' % str(time.time()*1000),
            'oid': 'reqseq',
            'reqseq': '%s' % str(self.revision),
            'tomid': '%s' % str(squareChatMid),
            'type': '%s' % str(type),
            'ver': '1.0'
        }
        if type == 'video':
            params.update({'duration': '60000'})
        elif type == 'audio':
            params.update({'duration': '60000'})
        elif type == 'gif':
            params.update({'type': 'image', 'cat': 'original'})
        elif type == 'file':
            params.update({'name': name})
        headers = self.server.additionalHeaders(self.server.Headers, {
            'Content-Type': contentType,
            'Content-Length': str(len(data)),
            'x-obs-params': self.genOBSParams(params,'b64'),
            'X-Line-Access': self.squareObsToken
        })
        r = self.server.postContent(self.server.LINE_OBS_DOMAIN + '/r/g2/m/reqseq', data=data, headers=headers)
        if r.status_code != 201:
            raise Exception('Upload %s failure.' % type)
        if returnAs == 'bool':
            return True

    @loggedIn
    def uploadObjTalk(self, path, type='image', returnAs='bool', objId=None, to=None, name=None):
        if returnAs not in ['objId','bool']:
            raise Exception('Invalid returnAs value')
        if type not in ['image','gif','video','audio','file']:
            raise Exception('Invalid type value')
        headers=None
        files = {'file': open(path, 'rb')}
        if type == 'image' or type == 'video' or type == 'audio' or type == 'file':
            e_p = self.server.LINE_OBS_DOMAIN + '/talk/m/upload.nhn'
            data = {'params': self.genOBSParams({'oid': objId,'size': len(open(path, 'rb').read()),'type': type, 'name': name})}
        elif type == 'gif':
            e_p = self.server.LINE_OBS_DOMAIN + '/r/talk/m/reqseq'
            files = None
            data = open(path, 'rb').read()
            params = {
                'name': '%s' % str(time.time()*1000),
                'oid': 'reqseq',
                'reqseq': '%s' % str(self.revision),
                'tomid': '%s' % str(to),
                'cat': 'original',
                'type': 'image',
                'ver': '1.0'
            }
            headers = self.server.additionalHeaders(self.server.Headers, {
                'Content-Type': 'image/gif',
                'Content-Length': str(len(data)),
                'x-obs-params': self.genOBSParams(params,'b64')
            })
        r = self.server.postContent(e_p, data=data, headers=headers, files=files)
        if r.status_code != 201:
            raise Exception('Upload %s failure.' % type)
        if returnAs == 'objId':
            return objId
        elif returnAs == 'bool':
            return True

    @loggedIn
    def uploadObjHome(self, path, type='image', returnAs='bool', objId=None):
        if returnAs not in ['objId','bool']:
            raise Exception('Invalid returnAs value')
        if type not in ['image','video','audio']:
            raise Exception('Invalid type value')
        if type == 'image':
            contentType = 'image/jpeg'
        elif type == 'video':
            contentType = 'video/mp4'
        elif type == 'audio':
            contentType = 'audio/mp3'
        if not objId:
            objId = int(time.time())
        file = open(path, 'rb').read()
        params = {
            'name': '%s' % str(time.time()*1000),
            'userid': '%s' % self.profile.mid,
            'oid': '%s' % str(objId),
            'type': type,
            'ver': '1.0'
        }
        hr = self.server.additionalHeaders(self.server.timelineHeaders, {
            'Content-Type': contentType,
            'Content-Length': str(len(file)),
            'x-obs-params': self.genOBSParams(params,'b64')
        })
        r = self.server.postContent(self.server.LINE_OBS_DOMAIN + '/myhome/c/upload.nhn', headers=hr, data=file)
        if r.status_code != 201:
            raise Exception('Upload object home failure.')
        if returnAs == 'objId':
            return objId
        elif returnAs == 'bool':
            return True

    @loggedIn
    def downloadObjectMsg(self, messageId, returnAs='path', saveAs=''):
        if saveAs == '':
            saveAs = self.genTempFile('path')
        if returnAs not in ['path','bool','bin']:
            raise Exception('Invalid returnAs value')
        params = {'oid': messageId}
        url = self.server.urlEncode(self.server.LINE_OBS_DOMAIN, '/talk/m/download.nhn', params)
        r = self.server.getContent(url)
        if r.status_code == 200:
            self.saveFile(saveAs, r.raw)
            if returnAs == 'path':
                return saveAs
            elif returnAs == 'bool':
                return True
            elif returnAs == 'bin':
                return r.raw
        else:
            raise Exception('Download object failure.')
    def uploadObjectForService(
        self,
        pathOrBytes: any,
        oType: str = "image",
        obsPath: str = "myhome/h",
        issueToken4ChannelId: str = None,
        params: dict = None,
        talkMeta: str = None,
        filename: str = None,
        additionalHeaders: dict = None,
    ):
        obs_path = f"/r/{obsPath}"
        self.Headers = {}
        Hraders4Obs = {
            "User-Agent": self.server.Headers["User-Agent"],
            "X-Line-Access": self.authToken,
            "X-Line-Application": self.server.Headers["x-line-application"],
            "X-Line-Mid": self.mid,
            "x-lal": self.LINE_LANGUAGE,
        }
        obsConn = httpx.Client(http2=True, timeout=None)
        hr = self.Hraders4Obs
        data = None
        files = None
        oType = oType.lower()
        isDebugOnly = True
        if isinstance(pathOrBytes, str):
            if pathOrBytes.startswith("http"):
                # URL
                with httpx.Client() as hc:
                    data = hc.get(pathOrBytes).content
            else:
                # FILE
                files = {"file": open(pathOrBytes, "rb")}
                filename = files["file"].name if filename is None else filename
                filename = filename.split("\\")[-1]
                with open(pathOrBytes, "rb") as f:
                    data = f.read()
        else:
            # BYTES
            data = pathOrBytes
        filename = str(uuid.uuid1()) if filename is None else filename
        base_params = {
            "type": oType,
            "ver": "2.0",
            "name": filename,
        }
        if params:
            base_params.update(params)
        params = base_params
        if files is not None:
            # FORM DATA
            data = {"params": json.dumps(params)}
            params = None
        else:
            # POST DATA
            files = None
            if len(data) == 0:
                raise ValueError("No data to send: %s" % data)
            hr = self.server.additionalHeaders(
                hr,
                {
                    "Content-Type": "image/gif",  # but...
                    "Content-Length": str(len(data)),
                    "X-Obs-Params": self.genOBSParams(params, "b64"),
                },
            )
        if issueToken4ChannelId is not None:
            hr = self.server.additionalHeaders(
                hr,
                {
                    "X-Line-ChannelToken": self.checkAndGetValue(
                        self.approveChannelAndIssueChannelToken(issueToken4ChannelId),
                        "channelAccessToken",
                        5,
                    ),
                },
            )
        if params is not None:
            hr = self.server.additionalHeaders(
                hr,
                {
                    "X-Obs-Params": self.genOBSParams(params, "b64").decode(),
                },
            )
        if talkMeta is not None:
            hr = self.server.additionalHeaders(hr, {"X-Talk-Meta": talkMeta})
        if additionalHeaders is not None:
            hr.update(additionalHeaders)
        self.log(f"Starting uploadObjectForService...", isDebugOnly)
        self.log(f"data: {str(data)[:200]}", isDebugOnly)
        self.log(f"files: {files}", isDebugOnly)
        self.log(f"obsPath: {obs_path}", isDebugOnly)
        self.log(f"params: {params}", isDebugOnly)
        self.log(f"files: {files}", isDebugOnly)
        self.log(f"hr: {hr}", isDebugOnly)
        r = self.postPackDataAndGetUnpackRespData(
            f"/oa{obs_path}",
            data,
            0,
            0,
            headers=hr,
            expectedRespCode=[200, 201],
            conn=self.obsConn,
            files=files,
        )
        # r = self.obsConn.post(self.LINE_GW_HOST_DOMAIN + f'/oa{obs_path}', data=data, headers=hr, files=files)
        # expectedRespCode:
        # - 200: image cache on obs server
        # - 201: image created success
        objId = r.headers["x-obs-oid"]
        objHash = r.headers["x-obs-hash"]  # for view on cdn
        self.log(f"Ended uploadObjectForService!", isDebugOnly)
        return objId, objHash, r.headers
    @loggedIn
    def forwardObjectMsg(self, to, msgId, contentType='image'):
        if contentType not in ['image','video','audio']:
            raise Exception('Type not valid.')
        data = self.genOBSParams({'oid': 'reqseq','reqseq': self.revision,'type': contentType,'copyFrom': '/talk/m/%s' % msgId},'default')
        r = self.server.postContent(self.server.LINE_OBS_DOMAIN + '/talk/m/copy.nhn', data=data)
        if r.status_code != 200:
            raise Exception('Forward object failure.')
        return True
