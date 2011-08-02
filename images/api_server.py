#!/usr/bin/env python
import os,sys
try:
    os.environ["DJANGO_SETTINGS_MODULE"]
except Exception,what:
    # insert parent directory into syspath
    # so that we can setup environment
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),"..")))
    from django.core.management import setup_environ
    import settings
    setup_environ(settings)

import django.contrib.auth
import django.core.handlers.wsgi

from images.models import Album,Image

import tornado.wsgi
import tornado.httpserver
import tornado.httpclient
import tornado.ioloop
import tornado.options
import tornado.web
from tornado.stack_context import StackContext
import contextlib
import json
import logging

from multiprocessing import Pool
import email.utils,datetime,time

from tornado.options import define, options
define("port", default=8888, help="run on the given port", type=int)

import api_class

class BaseHandler(tornado.web.RequestHandler):
    def get_django_session(self):
        if not hasattr(self, '_session'):
            engine = django.utils.importlib.import_module(
                settings.SESSION_ENGINE)
            session_key = self.get_cookie(django.conf.settings.SESSION_COOKIE_NAME)
            self._session = engine.SessionStore(session_key)
        return self._session

    def get_user_locale(self):
        # locale.get will use the first non-empty argument that matches a
        # supported language.
        return tornado.locale.get(
            self.get_argument('lang', None),
            self.get_django_session().get('django_language', None),
            self.get_cookie('django_language', None))

    def get_current_user(self):
        # get_user needs a django request object, but only looks at the session
        class Dummy(object): pass
        django_request = Dummy()
        django_request.session = self.get_django_session()
        user = django.contrib.auth.get_user(django_request)
        if user.is_authenticated():
            return user
        else:
            # try basic auth
            if not self.request.headers.has_key('Authorization'):
                return None
            kind, data = self.request.headers['Authorization'].split(' ')
            if kind != 'Basic':
                return None
            (username, _, password) = data.decode('base64').partition(':')
            user = django.contrib.auth.authenticate(username = username,
                                                    password = password)
            if user is not None and user.is_authenticated():
                return user
            return None

    def get_django_request(self):
        request = django.core.handlers.wsgi.WSGIRequest(
            tornado.wsgi.WSGIContainer.environ(self.request))
        request.session = self.get_django_session()

        if self.current_user:
            request.user = self.current_user
        else:
            request.user = django.contrib.auth.models.AnonymousUser()
        return request

class AlbumHandler(BaseHandler):
    def post(self,action):
        if action == "create":
            request = self.get_django_request()
            self.finish(api_class.album(request,action))

class ImageHandler(BaseHandler):#tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def post(self,action):
        if action == "weblink":
            self.action = action
            self.links = json.loads( self.request.body )
            self.data = {}
            if len(self.links)>=1:
                http = tornado.httpclient.AsyncHTTPClient()
                http.fetch(self.links[0],callback=self.on_response)
            else:
                self.finish({"status":"failed","reason":"invalid request syntax"})
        elif action == "upload":
            request = self.get_django_request()
            user = self.get_current_user()
            self.finish(api_class.image(request,action))

    def on_response(self,response):
        '''recursively fetch the links, finally finish'''
        if response.error:
            self.data[self.links[0]] = None
        else:
            self.data[self.links[0]] = response.body
        self.links = self.links[1:]
        if len(self.links)>=1:
            http = tornado.httpclient.AsyncHTTPClient()
            with StackContext(die_on_error):
                http.fetch(self.links[0],callback=self.on_response)
        else:
            request = self.get_django_request()
            response = api_class.image(request,self.action,self.data)
            self.finish(response)

def file_read(name,size,offset,processed,length):
    '''
        reading partial content from gridfs
    '''
    import pymongo,gridfs
    from settings import DB_HOST,DB_PORT,DB_NAME
    try:
        if not hasattr(file_read,'fs'):
            file_read.fs = gridfs.GridFS(pymongo.Connection("%s:%s"%(DB_HOST,DB_PORT))[DB_NAME])
        f = file_read.fs.get_version(filename=name)
        f.seek(offset+processed)
        if processed+size<length:
            processed += size
            return processed,f.read(size)
        else:
            left = length - processed
            processed = length
            return processed,f.read(left)
    except Exception,what:
        logging.error( repr(what), exc_info=True )
        return 0,''

class RootHandler(BaseHandler):
    ''' 
        Read a file/image from mongodb's gridfs, asynchronously return chunks 
        to avoid loading all content into memory
        
        HTTP 1.1 Resumable Transfer syntax, ie Range Syntax, is partially supported
        Simple Range header is supported (eg. "Range: 1-","Range: -500","Range: 34-445")
        Ranges seprated by comma is not supported (eg. "Range: 1-100,200-300")
    '''
    @tornado.web.asynchronous
    def get(self,path):
        import pymongo,gridfs
        from settings import DB_HOST,DB_PORT,DB_NAME
        name = path
        try:
            if not hasattr(RootHandler,'fs'):
                RootHandler.fs = gridfs.GridFS(pymongo.Connection("%s:%s"%(DB_HOST,DB_PORT))[DB_NAME])
        except:
            self.set_status(503)
            self.finish("503: Mongodb Unaccessiable")
            return
        try:
            self.f = RootHandler.fs.get_version(filename=name)
        except:
            self.set_status(404)
            self.finish("404: Not Found")
            return

        #content type control
        try:
            self.set_header("Content-Type",self.f.content_type)
        except:
            self.set_header("Content-Disposition","attachment; filename=%s"%name)

        #cache control
        self.set_header("Last-Modified",self.f.upload_date)
        self.set_header("Cache-Control", "public")
        ims_value = self.request.headers.get("If-Modified-Since")
        if ims_value is not None:
            date_tuple = email.utils.parsedate(ims_value)
            if_since = datetime.datetime.fromtimestamp(time.mktime(date_tuple))
            d = self.f.upload_date
            last_modified = datetime.datetime(d.year,d.month,d.day,d.hour,d.minute,d.second)
            print if_since,last_modified
            if if_since >= last_modified:
                self.set_status(304)
                self.finish()
                return
        
        #range control
        self.size = self.f.chunk_size
        self.processed = 0
        self.set_header("Accept-Ranges","bytes")
        if self.request.headers.has_key('Range'):
            if ',' in self.request.headers['Range']:
                self.set_status(501)
                self.finish("501: Complex Range Requecontent_typemplemented")
                return
            offset1,offset2 = self.request.headers['Range'][6:].split('-')
            if not offset2:
                offset2 = self.f.length-1
            if not offset1:
                offset1 = self.f.length-int(offset2)
                offset2 = self.f.length-1
            self.offset,self.length = int(offset1),int(offset2)-int(offset1)+1
            self.set_status(206)
            self.set_header("Content-Range", self.request.headers['Range'])
        else:
            self.offset,self.length = 0,self.f.length
        self.set_header("Content-Length","%d"%self.length)

        self.name = name
        self.f.seek(self.offset)
        self.p = self.application.settings.get('pool')
        self.p.apply_async(file_read,(self.name,self.size,self.offset,self.processed,self.length),callback=self.async_callback(self.on_read))

    def on_read(self,data):
        self.processed,rtn = data
        if self.processed == 0:
            self.set_status(503)
            self.finish('503: Mongodb Unaccessiable')
            return
        if self.processed == self.length:
            self.write(rtn)
            self.flush()
            self.finish()
            return
        else:
            self.write(rtn)
            self.flush()
            self.p.apply_async(file_read,(self.name,self.size,self.offset,self.processed,self.length),callback=self.async_callback(self.on_read))

@contextlib.contextmanager
def die_on_error():
    try:
        pass
    except:
        logging.error("exception in asynchronous operation",exc_info=True)
        sys.exit(1)

def main():
    tornado.options.parse_command_line()
    application = tornado.web.Application([
        (r"/api/album/(.*)", AlbumHandler),
        (r"/api/image/(.*)", ImageHandler),
        (r"/(.*)", RootHandler),
    ],pool=Pool(2), xheaders=True)
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()

