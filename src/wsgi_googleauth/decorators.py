# Copyright 2009 - Erik Karulf - MIT License - See LICENSE.txt

"""
A collection of useful decorators. When combined these decorators allow an
administartor to setup a failry precise authentication system.

These Decorators are designed specifically to work with the access control
mechanisms in mod_wsgi. 

The following assumptions are made:
 * Wrapped functions' argument lists are of the format: (environ, user, ...)
 * Wrapped functions are assumed to return True, False, or None
"""

import time
import logging
import collections
import random
from functools import wraps
from hashlib import sha1
from wsgi_googleauth.util import valid_email, parse_email

class Cache(object):
    """
    Caches the result of the mod_wsgi authorization functions for a given
    amount of time. This uses an internal datastructure instead of an external
    key-value store like memcached or redis.
    
    >>> import time
    >>> 
    >>> @Cache(timeout=10.0)
    ... def test(environ, user, password):
    ...     time.sleep(5.0)
    ...     return password == 'password'
    ... 
    >>> # cache miss
    ... cache_begin = begin = time.time()
    >>> result = test(None, 'user', 'password')
    >>> assert result
    >>> time.time() - begin < 1.0
    False
    >>> 
    >>> # cache hit
    ... begin = time.time()
    >>> result = test(None, 'user', 'password')
    >>> assert result
    >>> time.time() - begin < 1.0
    True
    >>> 
    >>> # cache miss
    ... begin = time.time()
    >>> result = test(None, 'user', 'password2')
    >>> assert not result
    >>> time.time() - begin < 1.0
    False
    >>> 
    >>> # wait for timeout
    ... while time.time() - cache_begin < 20.0:
    ...     time.sleep(1.0)
    ... 
    >>> # cache miss
    ... begin = time.time()
    >>> result = test(None, 'user', 'password')
    >>> assert result
    >>> time.time() - begin < 1.0
    False
    >>> 
    """
    def __init__(self, **options):
        # Options
        self.timeout = options.get('timeout', 60*30) # 30 minutes
        self.ignore_environ = options.get('ignore_environ', True) # by default, ignore the environment variables
        self.cache_true_only = options.get('cache_true_only', True)
        # Cache Structure
        self.salt = random.random()
        self.cache = collections.deque()
        
    def __call__(self, f):
        @wraps(f)
        def wrapper(*args):
            # Invariant: cache is sorted by timeout
            # Requirement: time.time is a monotonically increasing function
            # FIXME: If cache_true_only is False and the result is None, it is always a cache miss
            now = time.time()
            hash_args = args[1:] if self.ignore_environ else args
            checksum = sha1(repr((self.salt, hash_args))).hexdigest()
            result = None
            prune_list = []
            for cache_checksum, cache_expiration, cache_result in self.cache:
                if cache_expiration < now:
                    prune_list.append((cache_checksum, cache_expiration, cache_result))
                    continue
                if cache_checksum == checksum:
                    result = cache_result
                if result is not None and cache_expiration > now:
                    # We have what we are looking for and we are done pruning
                    break
            for cache_entry in prune_list:
                try:
                    self.cache.remove(cache_entry)
                except ValueError:
                    pass
            if result is None:
                # Cache-Miss: Let's query the function
                result = f(*args)
                if not self.cache_true_only or (self.cache_true_only and result is True):
                    self.cache.append((checksum, time.time() + self.timeout, result))
            return result
        return wrapper

class DefaultDomain(object):
    """
    Fills in a domain name if none is none is specified. If this does not yield
    a valid email address it passes the username through unchanged.
    
    Example:
    >>> @DefaultDomain('example.com')
    ... def test(environ, name, password):
    ...     print name
    ... 
    >>> test(None, 'erik', None)
    erik@example.com
    >>> test(None, 'erik@karulf.com', None)
    erik@karulf.com
    >>> test(None, ';', None)
    ;
    >>> 
    """
    def __init__(self, domain):
        self.domain = domain
    
    def __call__(self, f):
        @wraps(f)
        def wrapper(environ, name, *args):
            if not valid_email(name):
                new_name = "{0}@{1}".format(name, self.domain)
                if valid_email(new_name):
                    name = new_name
            return f(environ, name, *args)
        return wrapper

class RequireDomain(object):
    """
    Requires both the username to be a valid email and the domain name to match
    a value given at initialization.
    
    Example:
    >>> @RequireDomain('example.com')
    ... def test(environ, name, password):
    ...     return True
    ... 
    >>> test(None, 'erik', None)
    >>> test(None, 'erik@karulf.com', None)
    >>> test(None, 'erik@example.com', None)
    True
    >>> 
    """
    def __init__(self, domain):
        self.domain = domain
    
    def __call__(self, f):
        @wraps(f)
        def wrapper(environ, name, *args):
            match = parse_email(name)
            if match is not None and match[1] == self.domain:
                return f(environ, name, *args)
            else:
                return None
        return wrapper

class RequireValidEmail(object):
    """
    Requires a valid email address

    Example:
    >>> @RequireValidEmail()
    ... def test(environ, user, password):
    ...     return True
    ... 
    >>> test(None, 'erik', 'password')
    >>> test(None, 'erik@example.com', 'password')
    True
    """
    def __init__(self):
        pass

    def __call__(self, f):
        @wraps(f)
        def wrapper(environ, name, *args):
            if valid_email(name):
                return f(environ, name, *args)
            else:
                return None
        return wrapper

