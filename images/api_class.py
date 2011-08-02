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


def album(request,action,data=None):
    response = {"status":"403","reason":"undefined operation"}
    try:
        if action == "create":
            ids = json.loads( request.raw_post_data )
            album = Album()
            if user.is_authenticated():
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
    except Exception,what:
        print repr(what)
        response["reason"] = repr(what)
    return response
