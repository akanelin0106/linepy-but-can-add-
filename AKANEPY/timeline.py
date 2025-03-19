# -*- coding: utf-8 -*-
from datetime import datetime
from .channel import Channel
from .config import Config
import json, time, base64,copy,random,os,requests,hashlib

def loggedIn(func):
    def checkLogin(*args, **kwargs):
        if args[0].isLogin:
            return func(*args, **kwargs)
        else:
            args[0].callback.default('You want to call the function, you must login to LINE')
    return checkLogin
    
class Timeline(Channel):

    def __init__(self):
        if not self.channelId:
            self.channelId = self.server.CHANNEL_ID['LINE_TIMELINE']
        Channel.__init__(self, self.channel, self.channelId, False)
        self.tl = self.getChannelResult()
        self.__loginTimeline()
        
    def __loginTimeline(self):
        self.server.setTimelineHeadersWithDict({
            'Content-Type': 'application/json; charset=UTF-8',
            'User-Agent': 'androidapp.line/11.5.1 (Linux; U; Android 7.0; en-GB; Redmi Note 4 Build/NRD90M)',
            'X-Line-Mid': self.profile.mid,
            'X-Line-Carrier': self.server.CARRIER,
            'X-LSR': 'ID',
            'X-LPV': '1',
            'X-Line-Application': 'ANDROID 11.5.1 Android OS 7.0',
            'Accept-Encoding': 'gzip',
            'X-Line-ChannelToken': self.tl.channelAccessToken
        })
        self.LineLegyDomain = "https://legy-jp-addr.line.naver.jp"
        self.LineHostDomain = "https://ga2.line.naver.jp"
        self.LineGwzDomain  = "https://gwz.line.naver.jp"
        self.LineObsDomain  = "https://obs-sg.line-apps.com"
        self.LineLiffDomain = "https://api.line.me/message/v3/share"
        self.LinePermission = "https://access.line.me/dialog/api/permissions"
        self.profileDetail = self.getProfileDetail()
        

    """Timeline"""

    @loggedIn
    def getFeed(self, postLimit=10, commentLimit=1, likeLimit=1, order='TIME'):
        params = {'postLimit': postLimit, 'commentLimit': commentLimit, 'likeLimit': likeLimit, 'order': order}
        url = self.server.urlEncode(self.server.LINE_TIMELINE_API, '/v45/feed/list.json', params)
        r = self.server.getContent(url, headers=self.server.timelineHeaders)
        return r.json()

    @loggedIn
    def getHomeProfile(self, mid=None, postLimit=10, commentLimit=1, likeLimit=1):
        if mid is None:
            mid = self.profile.mid
        params = {'homeId': mid, 'postLimit': postLimit, 'commentLimit': commentLimit, 'likeLimit': likeLimit, 'sourceType': 'LINE_PROFILE_COVER'}
        url = self.server.urlEncode(self.server.LINE_TIMELINE_API, '/v45/post/list.json', params)
        r = self.server.getContent(url, headers=self.server.timelineHeaders)
        return r.json()
    @loggedIn
    def getProfileDetail(
        self, mid, styleMediaVersion="v2", storyVersion="v7", timelineVersion="v57"
    ):
        params = {
            "homeId": mid,
            "styleMediaVersion": styleMediaVersion,
            "storyVersion": storyVersion,
            "timelineVersion": timelineVersion,
            "profileBannerRevision": 0,
        }
        hr = self.server.additionalHeaders(
            self.server.timelineHeaders,
            {
                "x-lhm": "GET",
                # why get follow count with this?
                "x-line-global-config": "discover.enable=true; follow.enable=true",
            },
        )
        LINE_HOST_DOMAIN = "https://ga2.line.naver.jp"
        url = self.server.urlEncode(
            LINE_HOST_DOMAIN, "/hm/api/v1/home/profile.json", params
        )
        r = self.server.postContent(url, headers=hr, data="")
        return r.json()
    @loggedIn
    def getProfileDetail1(self, mid=None):
        if mid is None:
            mid = self.profile.mid
        params = {'userMid': mid}
        url = self.server.urlEncode(self.server.LINE_TIMELINE_API, '/v1/userpopup/getDetail.json', params)
        r = self.server.getContent(url, headers=self.server.timelineHeaders)
        return r.json()

    @loggedIn
    def updateProfileCoverById(self, objid, isVideo=False):
        data = {
            "homeId": self.profile.mid,
            "coverObjectId": objid,
            "storyShare": False,
            "meta": {}
        }
        if isVideo:
            data['videoCoverObjectId'] = objid
        headers = self.server.additionalHeaders(self.server.timelineHeaders, {
            'x-lhm': "POST",
        })
        r = self.server.postContent(self.LineHostDomain+ '/hm/api/v1/home/cover.json', headers=headers, data=json.dumps(data))
        return r.json()
    @loggedIn
    def genOBSParamsV2(self, params):
        return base64.b64encode(json.dumps(params).encode('utf-8'))
    @loggedIn
    def genObjectId(self):
        random.seed = (os.urandom(1024))
        return ''.join(random.choice("abcdef1234567890") for i in range(32))
    @loggedIn
    def updateCover(self, picture):
        oid = self.genObjectId()
        print(oid)
        headers = copy.deepcopy(self.server.timelineHeaders)
        headers["X-Line-PostShare"] = "false"
        headers["X-Line-StoryShare"] = "false"
        headers["X-Line-Signup-Region"] = "TH"
        headers["Content-Type"] = "cover.png"
        print(headers)
        obs = self.genOBSParamsV2(
            {"name": picture, "oid": oid, "type": "image", "userid": self.profile.mid, "ver": "2.0"})
        headers["x-obs-params"] = obs
        result = requests.post(
            "https://obs-sg.line-apps.com" + "/r/myhome/c/" + oid, headers=headers, data=open(picture, 'rb'))
        if result.status_code != 201:
            raise Exception("[ Error ] Fail change cover")
        print(result.text)
        self.updateProfileCoverById(oid)
        return
    @loggedIn
    def getProfileCoverId(self, mid=None):
        if mid is None:
            mid = self.profile.mid
        home = self.getProfileDetail(mid)
        return home['result']['objectId']
    @loggedIn
    def getProfileCoverDetail(self, mid):
        LINE_HOST_DOMAIN  = 'https://ga2.line.naver.jp'
        params = {"homeId": mid}
        hr = self.server.additionalHeaders(
            self.server.timelineHeaders,
            {
                "x-lhm": "GET",
            },
        )
        url = self.server.urlEncode(
            LINE_HOST_DOMAIN, "/hm/api/v1/home/cover.json", params
        )
        r = self.server.postContent(url, headers=hr)
        return r.json()

    @loggedIn
    def getProfileCoverURL(self, mid=None):
        if mid is None:
            mid = self.profile.mid
        home = self.getProfileDetail(mid)
        params = {'userid': mid, 'oid': home['result']['objectId']}
        return self.server.urlEncode(self.server.LINE_OBS_DOMAIN, '/myhome/c/download.nhn', params)

    """Post"""

    @loggedIn
    def createPost(self, text, holdingTime=None):
        params = {'homeId': self.profile.mid, 'sourceType': 'TIMELINE'}
        url = self.server.urlEncode(self.server.LINE_TIMELINE_API, '/v45/post/create.json', params)
        payload = {'postInfo': {'readPermission': {'type': 'ALL'}}, 'sourceType': 'TIMELINE', 'contents': {'text': text}}
        if holdingTime != None:
            payload["postInfo"]["holdingTime"] = holdingTime
        data = json.dumps(payload)
        r = self.server.postContent(url, data=data, headers=self.server.timelineHeaders)
        return r.json()

    @loggedIn
    def sendPostToTalk(self, mid, postId):
        if mid is None:
            mid = self.profile.mid
        params = {'receiveMid': mid, 'postId': postId}
        url = self.server.urlEncode(self.server.LINE_TIMELINE_API, '/v45/post/sendPostToTalk.json', params)
        r = self.server.getContent(url, headers=self.server.timelineHeaders)
        return r.json()

    @loggedIn
    def createComment(self, mid, postId, text):
        if mid is None:
            mid = self.profile.mid
        params = {'homeId': mid, 'sourceType': 'TIMELINE'}
        url = self.server.urlEncode(self.server.LINE_TIMELINE_API, '/v45/comment/create.json', params)
        data = {'commentText': text, 'activityExternalId': postId, 'actorId': mid}
        data = json.dumps(data)
        r = self.server.postContent(url, data=data, headers=self.server.timelineHeaders)
        return r.json()

    @loggedIn
    def deleteComment(self, mid, postId, commentId):
        if mid is None:
            mid = self.profile.mid
        params = {'homeId': mid, 'sourceType': 'TIMELINE'}
        url = self.server.urlEncode(self.server.LINE_TIMELINE_API, '/v45/comment/delete.json', params)
        data = {'commentId': commentId, 'activityExternalId': postId, 'actorId': mid}
        data = json.dumps(data)
        r = self.server.postContent(url, data=data, headers=self.server.timelineHeaders)
        return r.json()

    @loggedIn
    def likePost(self, mid, postId, likeType=1001):
        if mid is None:
            mid = self.profile.mid
        if likeType not in [1001,1002,1003,1004,1005,1006]:
            raise Exception('Invalid parameter likeType')
        params = {'homeId': mid, 'sourceType': 'TIMELINE'}
        url = self.server.urlEncode(self.server.LINE_TIMELINE_API, '/v45/like/create.json', params)
        data = {'likeType': likeType, 'activityExternalId': postId, 'actorId': mid}
        data = json.dumps(data)
        r = self.server.postContent(url, data=data, headers=self.server.timelineHeaders)
        return r.json()

    @loggedIn
    def unlikePost(self, mid, postId):
        if mid is None:
            mid = self.profile.mid
        params = {'homeId': mid, 'sourceType': 'TIMELINE'}
        url = self.server.urlEncode(self.server.LINE_TIMELINE_API, '/v45/like/cancel.json', params)
        data = {'activityExternalId': postId, 'actorId': mid}
        data = json.dumps(data)
        r = self.server.postContent(url, data=data, headers=self.server.timelineHeaders)
        return r.json()

    """Group Post"""

    @loggedIn
    def createGroupPost(self, mid, text):
        payload = {'postInfo': {'readPermission': {'homeId': mid}}, 'sourceType': 'TIMELINE', 'contents': {'text': text}}
        data = json.dumps(payload)
        r = self.server.postContent(self.server.LINE_TIMELINE_API + '/v45/post/create.json', data=data, headers=self.server.timelineHeaders)
        return r.json()

    @loggedIn
    def createGroupAlbum(self, mid, name):
        data = json.dumps({'title': name, 'type': 'image'})
        params = {'homeId': mid,'count': '1','auto': '0'}
        url = self.server.urlEncode(self.server.LINE_TIMELINE_MH, '/album/v3/album.json', params)
        r = self.server.postContent(url, data=data, headers=self.server.timelineHeaders)
        if r.status_code != 201:
            raise Exception('Create a new album failure.')
        return True

    @loggedIn
    def deleteGroupAlbum(self, mid, albumId):
        params = {'homeId': mid}
        url = self.server.urlEncode(self.server.LINE_TIMELINE_MH, '/album/v3/album/%s' % albumId, params)
        r = self.server.deleteContent(url, headers=self.server.timelineHeaders)
        if r.status_code != 201:
            raise Exception('Delete album failure.')
        return True
    
    @loggedIn
    def getGroupPost(self, mid, postLimit=10, commentLimit=1, likeLimit=1):
        params = {'homeId': mid, 'commentLimit': commentLimit, 'likeLimit': likeLimit, 'sourceType': 'TALKROOM'}
        url = self.server.urlEncode(self.server.LINE_TIMELINE_API, '/v45/post/list.json', params)
        r = self.server.getContent(url, headers=self.server.timelineHeaders)
        return r.json()

    """Group Album"""

    @loggedIn
    def getGroupAlbum(self, mid):
        params = {'homeId': mid, 'type': 'g', 'sourceType': 'TALKROOM'}
        url = self.server.urlEncode(self.server.LINE_TIMELINE_MH, '/album/v3/albums.json', params)
        r = self.server.getContent(url, headers=self.server.timelineHeaders)
        return r.json()

    @loggedIn
    def changeGroupAlbumName(self, mid, albumId, name):
        data = json.dumps({'title': name})
        params = {'homeId': mid}
        url = self.server.urlEncode(self.server.LINE_TIMELINE_MH, '/album/v3/album/%s' % albumId, params)
        r = self.server.putContent(url, data=data, headers=self.server.timelineHeaders)
        if r.status_code != 201:
            raise Exception('Change album name failure.')
        return True

    @loggedIn
    def addImageToAlbum(self, mid, albumId, path):
        file = open(path, 'rb').read()
        params = {
            'oid': int(time.time()),
            'quality': '90',
            'range': len(file),
            'type': 'image'
        }
        hr = self.server.additionalHeaders(self.server.timelineHeaders, {
            'Content-Type': 'image/jpeg',
            'X-Line-Mid': mid,
            'X-Line-Album': albumId,
            'x-obs-params': self.genOBSParams(params,'b64')
        })
        r = self.server.getContent(self.server.LINE_OBS_DOMAIN + '/album/a/upload.nhn', data=file, headers=hr)
        if r.status_code != 201:
            raise Exception('Add image to album failure.')
        return r.json()

    @loggedIn
    def getImageGroupAlbum(self, mid, albumId, objId, returnAs='path', saveAs=''):
        if saveAs == '':
            saveAs = self.genTempFile('path')
        if returnAs not in ['path','bool','bin']:
            raise Exception('Invalid returnAs value')
        hr = self.server.additionalHeaders(self.server.timelineHeaders, {
            'Content-Type': 'image/jpeg',
            'X-Line-Mid': mid,
            'X-Line-Album': albumId
        })
        params = {'ver': '1.0', 'oid': objId}
        url = self.server.urlEncode(self.server.LINE_OBS_DOMAIN, '/album/a/download.nhn', params)
        r = self.server.getContent(url, headers=hr)
        if r.status_code == 200:
            self.saveFile(saveAs, r.raw)
            if returnAs == 'path':
                return saveAs
            elif returnAs == 'bool':
                return True
            elif returnAs == 'bin':
                return r.raw
        else:
            raise Exception('Download image album failure.')
