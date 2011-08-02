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
from PIL import Image as PImage
import StringIO
import json

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

def view_album(request, path):
    """ Album listing. """
    view = request.GET.get("view","")
    uid, sep, imguid = path.partition("#")
    album = Album.objects.get(uid=uid)
    if not album.public and not request.user.is_authenticated():
        return HttpResponse("Error: you need to be logged in to view this album.")
    images = album.images 
    return render_to_response("images/album.html",dict(album=album,images=images,user=request.user))

@login_required
def list_album(request):
    """ Album listing. """
    albums = Album.objects(user=request.user).order_by("-created")
    albums = [ x for x in albums[:200] ]
    return render_to_response("images/list_album.html",
        dict(albums=albums,
            user=request.user,
            APP_SERVER=APP_SERVER,
    ))

@login_required
def list_image(request):
    """ Image listing. """
    images = Image.objects(user=request.user).order_by("-created")
    images = [ x for x in images[:200] ]
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
    import urllib,urllib2
    try:
        d = {}
        for k in request.GET:
            d[k] = request.GET.get(k)
        if d:
            url =  APP_SERVER+"/api/"+path+"?"+urllib.urlencode(d)
        else:
            url =  APP_SERVER+"/api/"+path
        response = urllib.urlopen(url,data=request.raw_post_data)
    except Exception,what:
        print repr(what)
    return HttpResponse( response, mimetype="application/json" )
