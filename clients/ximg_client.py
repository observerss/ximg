#!/usr/bin/env python
#coding:utf-8
'''
    This is a python client library for ximg api call
    Usage:
        ximg = XimgClient(host,username,password)
        ximg.clone( [http://....jpg, http://....png, ...] ) # return XimgResponse
        ximg.group( [uid1,uid2,...] ) # return XimgResponse
        //ximg.upload( data, format, title="" ) # return XimgResponse
'''
import urllib,urllib2,cookielib
import re
import json

class XimgResponse:
    def __init__(self):
        self.status = "undefined" #ok/failed
        self.reason = ""
        self.type = "" #image/album
        self.uids = []
        self.urls = []

class XimgClient:
    def __init__(self,host,username,password):
        self.host,self.username,self.password = host,username,password
        cookie_support = urllib2.HTTPCookieProcessor( cookielib.CookieJar() )
        self.opener = urllib2.build_opener( cookie_support )
        self.login()

    def login(self): 
        url = "http://%s/accounts/login/" % self.host
        page = self.opener.open( url ).read()
        csrf = re.compile(r"name='csrfmiddlewaretoken' value='(.*?)'").search(page).group(1)
        data = urllib.urlencode( {"csrfmiddlewaretoken":csrf,"username":self.username,"password":self.password,"next":""} ) 
        return self.opener.open( url, data=data ).read()

    def clone(self,image_links):
        if type(image_links) == str:
            image_links = [ image_links ]
        if image_links == []:
            return XimgResponse()
        data = json.dumps(image_links)
        response = self.opener.open("http://%s/api/image/weblink"%self.host, data=data)
        ret = XimgResponse()
        d = json.loads(response.read())
        for x in d["result"]:
            ret.uids.append( x.get("uid","") )
            ret.urls.append( "http://i.ximg.in/"+x.get("uid","")+"."+x.get("ext","") )
        return ret

    def group(self,uids,title=None):
        if type(uids) == str:
            uids = [ uids ]
        data = json.dumps(uids)
        response = self.opener.open("http://%s/api/album/create"%self.host, data=data)
        ret = XimgResponse()
        d = json.loads(response.read())
        ret.uids.append( d["result"].get("aid","") )
        ret.urls.append( d["result"].get("link","") )
        if title:
            self.album_title(ret.uids[0],title)
        return ret
                    
    def album_title(self,uid,title):
        data = json.dumps( { "uid":uid, "title":title } )
        response = self.opener.open("http://%s/api/album/title"%self.host, data=data)
        ret = XimgResponse()
        return ret

if __name__ == "__main__":
    ximg = XimgClient("localhost:8000","tgsk","tgsk")
    ret = ximg.clone(["http://ximg.in/static/logo-large.gif","http://ximg.in/static/logo-large.gif"])
    ret = ximg.group(ret.uids,title="haha")
    print ret.uids,ret.urls

