#!/usr/local/bin/python

from wsgi_googleauth import GoogleAuth
from wsgi_googleauth.decorators import *

backend = GoogleAuth()

@RequireDomain("example.org")
@Cache("~/config/cache.db", timeout=60*15) # 15 minutes
def check_password(environ, username, password):
    return backend.check_password(environ, username, password)

