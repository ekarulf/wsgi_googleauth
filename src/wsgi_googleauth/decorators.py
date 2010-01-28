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
import sqlite3
import os
from functools import wraps
from hashlib import sha256
from wsgi_googleauth.util import valid_email, parse_email, encode_value, decode_value

class Cache(object):
    """
    Caches the result of the mod_wsgi authorization functions for a given
    amount of time. This uses an internal datastructure instead of an external
    key-value store like memcached or redis.
    
    >>> import time
    >>> 
    >>> @Cache(":memory:", timeout=10.0)
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
    SALT_NAME = 'salt'
    
    def _normalize_filename(self, filename):
        if filename[0:2] == '~/':
            # Relative to policy file
            import policy
            filename = os.path.join(os.path.join(os.path.dirname(policy.__file__), '..'), filename[2:])
        return os.path.abspath(filename)
    
    def __init__(self, filename, **options):
        # Options
        self.timeout = options.get('timeout', 60*30) # 30 minutes
        self.ignore_environ = options.get('ignore_environ', True) # by default, ignore the environment variables
        self.cache_true_only = options.get('cache_true_only', True)
        self.salt = None
        
        # Connect to the database
        if not filename == ':memory:':
            filename = self._normalize_filename(filename)
        # TODO: Enforce 0600 perms on UNIX?
        self.conn = sqlite3.connect(filename)
        c = self.conn.cursor()
        try:
            c.execute("CREATE TABLE cache (key TEXT UNIQUE, value TEXT, expiration INTEGER);")
        except sqlite3.OperationalError:
            # Cache table exists
            c.execute('DELETE FROM cache WHERE expiration < ?;', (time.time(),))
            c.execute("SELECT value FROM cache WHERE key = ? LIMIT 1", (Cache.SALT_NAME, ))
            for row in c:
                self.salt = decode_value(row[0])
        else:
            # Cache table just created
            self.salt = os.urandom(128)
            c.execute("CREATE INDEX IF NOT EXISTS expiration ON cache (expiration ASC);")
            c.execute('INSERT INTO cache(key, value) VALUES (?, ?);', (Cache.SALT_NAME, encode_value(self.salt)))
        self.conn.commit()
        assert self.salt is not None, "wsgi_googleauth Error: Salt not initialized"

    def __call__(self, f):
        @wraps(f)
        def wrapper(*args):
            # Invariant: cache is sorted by timeout
            # Requirement: time.time is a monotonically increasing function
            c = self.conn.cursor()

            # Generate Key
            # TODO: Use a more secure alternative like scrypt or PBKDF2
            hash_args = args[1:] if self.ignore_environ else args[:]
            hash_args = (self.salt,) + hash_args
            key = sha256(encode_value(hash_args)).hexdigest()

            # Cache Lookup
            found = False
            c.execute("SELECT value FROM cache WHERE key = ? AND expiration > ? LIMIT 1;", (key, time.time()))
            for row in c:
                result = decode_value(row[0])
                found = True

            # Query Function
            if not found:
                result = f(*args)
                if not self.cache_true_only or (self.cache_true_only and result is True):
                    timeout = time.time() + self.timeout
                    try:
                        c.execute("INSERT INTO cache(key, value, expiration) VALUES (?, ?, ?);", (key, encode_value(result), timeout))
                    except sqlite3.IntegrityError:
                        c.execute("UPDATE cache SET expiration = ? WHERE key = ?;", (timeout, key))
                    self.conn.commit()
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
                new_name = "%s@%s" % (name, self.domain)
                if valid_email(new_name):
                    logging.info("Defaulting username %s to %s" % (name, new_name))
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
                logging.info("Ignoring username %s as it does not match domain %s" % (name, self.domain))
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
                logging.info("Ignoring username %s as it is not a valid email")
                return None
        return wrapper

