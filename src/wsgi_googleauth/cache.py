# Copyright 2009 - Erik Karulf - MIT License - See LICENSE.txt

import time
import logging
import collections
import random
from functools import wraps
from hashlib import sha1 as sha1_constructor

def cache(**options):
    salt = random.random()
    cache = collections.deque()
    # Options
    self.timeout = options.get('timeout', 60*30) # 30 minutes
    self.ignore_environ = options.get('ignore_environ', True) # by default, ignore the environment variables
    self.cache_true_only = options.get('cache_true_only', True)
    def wrap(f):
        @wraps(f)
        def wrapper(*args):
            now = time.time()
            hash_args = args[1:] if ignore_environ else args
            checksum = sha_constructor(repr((salt, hash_args))).hexdigest()
            result = None
            for cache_checksum, cache_expiration, cache_result in cache:
                if cache_expiration < now:
                    try:
                        cache.remove((cache_checksum, cache_expiration, cache_result))
                    except ValueError:
                        pass
                    continue
                elif cache_checksum == checksum:
                    result = cache_result
                if result is not None and cache_expiration > now:
                    # We have what we are looking for and we are done pruning
                    break
            if result is None:
                # Cache-Miss: Let's query the function
                result = f(*args)
                if cache_true_only and result:
                    cache.append((checksum, now + timeout, result))
            return result
        return wrapper
    return wrap
