#!/usr/bin/env python
from mongoengine import * 
import os,sys
try:
    os.environ["DJANGO_SETTINGS_MODULE"]
except Exception,what:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),".."))) 
    from django.core.management import setup_environ
    import settings
    setup_environ(settings)


from settings import MEDIA_ROOT
from images.models import Image,Album,create_image
from images.utils import is_image,get_client_ip

import json
import utils

def delete_image(uid,delhash):
    try:
        im = Image.objects.get(uid=uid)
        if delhash and im.delhash == delhash:
            im.delete()
        return True
    except Exception,what:
        print repr(what)
        return False

def append_image_to_album(image_info,album_info):
    i_uid,i_delhash = image_info
    a_uid,a_delhash = album_info
    try:
        im = Image.objects.get(uid=i_uid)
        alb = Album.objects.get(uid=a_uid)
        if im.delhash == i_delhash and alb.delhash == a_delhash:
            im.albums.append(alb)
            al.images.append(im)
            return True
        else:
            return False
    except Exception,what:
        print repr(what)
        return False

def remove_image_from_album(image_info,album_info):
    i_uid,i_delhash = image_info
    a_uid,a_delhash = album_info
    try:
        im = Image.objects.get(uid=i_uid)
        alb = Album.objects.get(uid=a_uid)
        if im.delhash == i_delhash and alb.delhash == a_delhash:
            im.albums.remove(alb)
            al.images.remove(im)
            return True
        else:
            return False
    except Exception,what:
        print repr(what)
        return False

def album(request,action,data=None):
    response = {"status":"403","reason":"undefined operation"}
    try:
        if action == "create":
            ids = json.loads( request.raw_post_data )
            album = Album()
            if request.user.is_authenticated():
                album.user=request.user
            album.save()
            images = Image.objects.filter(uid__in=ids)
            for img in images:
                img.albums.append(album)
                album.images.append(img)
                img.save()
            album.save()
            response["status"] = "ok"
            del response["reason"]
            response["result"] = {
                "aid": album.uid,
                "link": album.albumurl()
            }
        elif action == "delete":
            pairs = json.loads( request.raw_post_data )
            response["status"] = "ok"
            del response["reason"]
            response["success"] = []
            for uid,delhash in pairs:
                try:
                    alb = Album.objects.get(uid=uid)
                    if alb.delhash == delhash:
                        ims = alb.images
                        for im in ims:
                            try:
                                im.delete()
                                #delete_image(im.uid,im.delhash)
                            except Exception,what:
                                #in case there're invalid references
                                print repr(what)
                        alb.delete()
                        response["success"].append( (True,None) )
                    else:
                        response["success"].append( (False,"Invalid Hash") )
                except Exception,what:
                    print repr(what)
                    response["success"].append( (False,repr(what)) )
        elif action == "append_image":
            image_info,album_info = json.loads( request.raw_post_data )
            response["status"] = "ok"
            del response["reason"]
            response["success"] = append_image_to_album(image_info,album_info)
        elif action == "remove_image":
            image_info,album_info = json.loads( request.raw_post_data )
            response["status"] = "ok"
            del response["reason"]
            response["success"] = remove_image_from_album(image_info,album_info)
    except Exception,what:
        response["reason"] = repr(what)
    return response

def image(request,action,datas=None):
    response = {"status":"403","reason":"undefined operation"}
    try:
        if action == "upload":
            data = request.raw_post_data
            filename = request.GET.get('qqfile','unknown.jpg')
            img = create_image(filename,data,request)
            img.save()
            response["status"] = "ok"
            del response["reason"]
            response["result"] = { 
                "id":img.uid,
                "ext":img.ext,
                "link":img.imageurl(),
                "thumblink":img.imageurl('thumb-small'),
            }
        elif action == "weblink":
            links = json.loads( request.raw_post_data )
            result = []
            for link in links:
                data = datas[link]
                if data:
                    filename = link.rsplit('/',1)[-1]
                    img = create_image(filename,data,request)
                    img.save()
                    result.append({
                        "success":True,
                        "uid":img.uid,
                        "ext":img.ext,
                        "link":img.imageurl(),
                        "thumblink":img.imageurl('thumb-small'),
                        "size":len(data),
                    })
                else:
                    result.append({"success":False})
            response["status"] = "ok"
            del response["reason"]
            response["result"] = result
        elif action == "delete":
            uid,delhash = json.loads( request.raw_post_data )
            response["status"] = "ok"
            del response["reason"]
            response["success"] = delete_image(uid,delhash)
        elif action == "append_to_album":
            image_info,album_info = json.loads( request.raw_post_data )
            response["status"] = "ok"
            del response["reason"]
            response["success"] == append_image_to_album(image_info,album_info)
        elif action == "remove_from_album":
            image_info,album_info = json.loads( request.raw_post_data )
            response["status"] = "ok"
            del response["reason"]
            response["success"] = remove_image_from_album(image_info,album_info)
    except Exception,what:
        print repr(what)
        response["reason"] = repr(what)
    return response
