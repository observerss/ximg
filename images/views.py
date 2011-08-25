# Create your views here.
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.contrib.auth.decorators import login_required
from django.core.context_processors import csrf
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.forms import ModelForm
from django.db.models import Q
from settings import MEDIA_URL,MEDIA_ROOT,STATIC_URL,STATIC_ROOT,APP_SERVER,IMG_SERVER
from django.views.decorators.csrf import csrf_exempt, csrf_protect

from models import *
import utils

from mimetypes import guess_type
import Image as PImage
import StringIO
import json

#reload database decorator
def mongodb_autoreload(func):
    count = 5
    while count>=0:
        try:
            count -= 1
            return func
        except Exception:
            import time
            time.sleep(1)

@mongodb_autoreload
def view_image(request, path):
    """Image viewing"""
    uid,sep,ext = path.partition('.')
    suffix = uid[6:]
    uid = uid[:6]
    if ext:
        return redirect(IMG_SERVER+"/"+uid+"."+ext)
    else:
        try:
            image = Image.objects.get(uid=uid)
            if not image.public:
                if not request.user.is_authenticated():
                    return HttpResponse('404')
            albums = image.albums[:3]
            urls = []
            for a in albums:
                if a.images:
                    urls.append( (a.albumurl(), a.images[0].imageurl('thumb-medium'),a.title) )
            urls = urls[:3]
        except (Image.DoesNotExist,IOError):
            return HttpResponse('404')
        return render_to_response("images/image.html",dict(image=image,albums=albums,urls=urls,user=request.user,height=image.height and image.height*500/image.width or 0))

@mongodb_autoreload
def view_index(request):
    """Main listing."""
    list_count = 10
    images = Image.objects
    if not request.user.is_authenticated():
        images = images.filter(public=True)
    imagelist = images.order_by('-created')[:list_count]
    return render_to_response("images/index.html", 
            dict(
                user=request.user,
                imagelist=[ x for x in imagelist ],
                APP_SERVER=APP_SERVER
            ))

def view_search(request):
    return ''

@mongodb_autoreload
def view_album(request, path):
    """ Album listing. """
    view = request.GET.get("view","")
    uid, sep, imguid = path.partition("#")
    album = Album.objects.get(uid=uid)
    if not album.public and not request.user.is_authenticated():
        return HttpResponse("Error: you need to be logged in to view this album.")
    images = album.images 
    return render_to_response("images/album.html",dict(album=album,images=images,user=request.user))

@mongodb_autoreload
@login_required
def list_album(request):
    """ Album listing. """
    albums = Album.objects.filter(user=request.user).order_by("-created")
    albums = [ {"uid":x.uid,"title":x.title,"delhash":x.delhash,"albumurl":x.albumurl(),"cover":x.coverurl} for x in albums[:10] ]
    return render_to_response("images/list_album.html",
        dict(albums=albums,
            user=request.user,
            APP_SERVER=APP_SERVER,
    ))

@mongodb_autoreload
@login_required
def list_image(request):
    """ Image listing. """
    images = Image.objects.filter(user=request.user).order_by("-created")
    images = [ x for x in images[:20] ]
    return render_to_response("images/list_image.html",
        dict(images=images,
            user=request.user,
            APP_SERVER=APP_SERVER,
    ))

@csrf_exempt
def api(request,path):
    ''' 
        Synchronoused image upload APIs
        Will be blocked and waiting IOs, so:
          Please only call this method under development environment
          under deployment environment, url should be dispatched to api_server services directly
    '''
    import urllib,httplib
    try:
        conn = httplib.HTTPConnection(APP_SERVER[7:])
        #processing headers
        def format_header_name(name):
            return "-".join([ x[0].upper()+x[1:] for x in name[5:].lower().split("_") ])
        headers = dict([ (format_header_name(k),v) for k,v in request.META.items() if k.startswith("HTTP_") ])
        headers["Cookie"] = "; ".join([ k+"="+v for k,v in request.COOKIES.items()])
        #post request
        conn.request(
            request.method,
            str(request.get_full_path()),
            request.raw_post_data,
            headers
        )
        response = conn.getresponse()
        if response.status == 200:
            response = response.read()
        else:
            response = { "status":"failed","code":response.status,"reason":response.reason }
    except Exception,what:
        print repr(what)[:200]
    return HttpResponse( response, mimetype="application/json" )
