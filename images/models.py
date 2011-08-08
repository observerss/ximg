from mongoengine import * 
from mongoengine.django.auth import User

from datetime import datetime

import os
from settings import IMG_SERVER,APP_SERVER,WEB_SERVER
import utils
import hashlib


class Tag(Document):
    tag = StringField(max_length=50,unique=True)
    def __unicode__(self):
        return self.tag

class Comment(Document):
    user = ReferenceField(User)
    created = DateTimeField(default=datetime.now)
    edited = DateTimeField(default=datetime.now)
    content = StringField(max_length=1024)
    reply_to = ReferenceField("self")
    liked = IntField(default=0)
    disliked = IntField(default=0)

class Login(Document):
    user = ReferenceField(User)
    ip = StringField(max_length=16)
    date = DateTimeField(default=datetime.now)
    success = BooleanField(default=True)

class Album(Document):
    uid = StringField(max_length=6,primary_key=True)
    title = StringField(max_length=120,default="Untitled")
    user = ReferenceField(User)
    images = ListField(GenericReferenceField())
    #public just means searchable
    public = BooleanField(default=True)
    created = DateTimeField(default=datetime.now)
    edited = DateTimeField(default=datetime.now)
    liked = IntField(default=0)
    disliked = IntField(default=0)
    tags = ListField(ReferenceField(Tag))
    comments = ListField(ReferenceField(Comment)) 
    delhash = StringField(max_length=32)
    def __init__(self, *args, **kwargs):
        """Generate uid"""
        super(Album, self).__init__(*args, **kwargs) 
        if not self.uid:
            while True:
                self.uid = utils.random_uid(length=6,
                    codebase='beuGDya1zYohtQMU0rmgWf4nSHVcFLj8lNdv3PqiC2wIAXB5Rs9k7pOx6ZETJK')
                try:
                    Album.objects.get(uid=self.uid)
                except Album.DoesNotExist:
                    break
            self.delhash = utils.generate_delhash(self.uid)
            self.save()
    def albumurl_medium(self):
        if self.images:
            return self.images[0].imageurl_medium()
    def albumurl(self):
        return '/a/%s' % self.uid
    def __unicode__(self):
        return self.title

class Image(Document):
    uid = StringField(max_length=6,primary_key=True)
    title = StringField(max_length=120,default="Untitled")
    image = FileField()
    ext = StringField(max_length=4,default="jpg")
    mime = StringField(max_length=50,default="image/jpeg")
    width = IntField(default=0)
    height = IntField(default=0)
    tags = ListField(ReferenceField(Tag))
    albums = ListField(ReferenceField(Album))
    comments = ListField(ReferenceField(Comment)) 
    created = DateTimeField(default=datetime.now)
    edited = DateTimeField(default=datetime.now)
    liked = IntField(default=0)
    disliked = IntField(default=0)
    user = ReferenceField(User)
    ip = StringField(max_length=16)
    public = BooleanField(default=True)
    delhash = StringField(max_length=32)
    def __init__(self, *args, **kwargs):
        """Generate uid"""
        super(Image, self).__init__(*args, **kwargs) 
        if not self.uid:
            while True:
                self.uid = utils.random_uid(length=6)
                try:
                    Image.objects.get(uid=self.uid)
                except Image.DoesNotExist:
                    break
            self.delhash = utils.generate_delhash(self.uid)
            self.save()
    def save(self, *args, **kwargs):
        """Save """
        super(Image, self).save(*args, ** kwargs)
        # call image save api @IMG_SERVER
        # IMG_SERVER is responsible for generating the thumbnails
        pass
        super(Image, self).save(*args, ** kwargs)
    def imageurl_original(self):
        return self.imageurl('original')
    def imageurl_small(self):
        return self.imageurl('thumb-small')
    def imageurl_medium(self):
        return self.imageurl('thumb-medium')
    def imageurl(self,mode=''):
        if mode == '':
            return '%s/%s' % (WEB_SERVER,self.uid)
        elif mode == 'original':
            return '%s/%s.%s' % (IMG_SERVER,self.uid,self.ext)
        elif mode == 'thumb-medium':
            return '%s/%sm.%s' % (IMG_SERVER,self.uid,self.ext)
        elif mode == 'thumb-small':
            return '%s/%ss.%s' % (IMG_SERVER,self.uid,self.ext)
    def albumurls(self):
        return [ '%s/a/%s#%s' % (IMG_SERVER,a.uid,self.uid) for a in self.albums.all() ]

    def __unicode__(self):
        return self.uid + '.' + self.ext

class UserProfile(Document):
    user = ReferenceField(User)
    sex = StringField(max_length=6,default="male",choices=["male","female"])
    dob = DateTimeField(default=datetime(1970,1,1))
    avatar = ReferenceField(Image)
    signature = StringField(max_length=240)
    bookmarks = ListField(GenericReferenceField())
    logins = ListField(ReferenceField(Login))

class Log(Document):
    time_logged = DateTimeField(default=datetime.now)
    target = GenericReferenceField()
    user = ReferenceField(User)
    action = StringField(max_length=20)
    ip = StringField(max_length=16)
    referrer = StringField(max_length=256)
    location = StringField(max_length=10)
    def ___unicode__(self):
        return self.ip + ' from ' + self.location + ' visited ' + self.target

def create_thumb_and_reduce_size(img,data):
    try:
        from PIL import Image as PImage
        from StringIO import StringIO
        from settings import DB_HOST,DB_PORT,DB_NAME
        import pymongo,gridfs
        fs = gridfs.GridFS(pymongo.Connection("%s:%s"%(DB_HOST,DB_PORT))[DB_NAME])

        im = PImage.open(StringIO(data))
        img.width,img.height = im.size

        if (len(data)>500*1024) and (img.ext != "gif"):
            buff = StringIO()
            im.convert("RGB").save(buff,"jpeg",quality=75)
            data = buff.getvalue()
        else:
            data = data

        im = utils.square_crop(im)
        #medium thumb
        im.thumbnail((100,100), PImage.ANTIALIAS)
        buff = StringIO()
        im.convert("RGB").save(buff,"jpeg",quality=75)
        fs.put(buff.getvalue(),filename=img.uid+"m."+img.ext,content_type="image/jpeg")

        #small thumb
        im.thumbnail((40,40), PImage.ANTIALIAS)
        buff = StringIO()
        im.convert("RGB").save(buff,"jpeg",quality=75)
        fs.put(buff.getvalue(),filename=img.uid+"s."+img.ext,content_type="image/jpeg")
    except Exception,what:
        print repr(what)

    return data
    
    
def create_image(filename,data,request):
    '''create an image from data and request'''
    from mimetypes import guess_type
    from StringIO import StringIO
    try:
        if not utils.is_image(data):
            print 'data is not image'
            return None
        try:
            name,dot,ext = filename.partition('.')
            if len(ext)>4:
                ext = "jpg"
        except:
            ext = "jpg"
        img = Image()
        img.ext = ext
        img.mime = guess_type(filename)[0]
        img.ip = utils.get_client_ip(request)
        
        #create thumbs and reduce size if necessary
        data = create_thumb_and_reduce_size(img,data)

        img.image.put(data, filename=img.uid+"."+img.ext, content_type=img.mime)
        if request.user.is_authenticated():
            img.user = request.user
        img.save()
    except Exception,what:
        print repr(what)
        return None
    return img

