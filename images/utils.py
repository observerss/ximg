import random
import time
import os

#codebase = 'abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'

def free_space():
    s = os.statvfs(".")
    return s.f_bsize*s.f_bavail

def random_uid(length=6,codebase=None):
    ''' 
    Generate a random uid
    first 3 chars: time/l/l%l, time/l%l, time%l
    next  * chars: random strings
    '''
    if not codebase:
        codebase = 'lJcIfXzMvUjgoSaOHiK7qmPhDEGdTex1kyN8uYV4pZ59bn3RQwtBA2W0CL6rFs'
    t = int(time.time())
    l = len(codebase)
    s = [codebase[t/l/l%l],codebase[t/l%l],codebase[t%l]]
    for _ in range(length-3):
        s.append( random.choice(codebase) )
    return ''.join(s)
    
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def square_crop(im):
    width, height = im.size

    if width > height:
        delta = width - height
        left = int(delta/2)
        upper = 0
        right = height + left
        lower = height
    else:
        delta = height - width
        left = 0
        upper = int(delta/2)
        right = width
        lower = width + upper

    im = im.crop((left, upper, right, lower))
    return im

def is_image(data):
    from PIL import Image as PImage
    import StringIO
    try:
        imgbuff = StringIO.StringIO(data)
        im = PImage.open(imgbuff)
    except Exception,what:
        print "not image",what
        return False
    return True

