# Copyright 2009 - Erik Karulf - MIT License - See LICENSE.txt
import re

try:
    import cPickle as pickle
except ImportError:
    import pickle

# email_re copied from Django 1.1
# Copyright (c) Django Software Foundation and individual contributors.
email_re = re.compile(
    r"((?:^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(?:\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"  # dot-atom
    r'|^"(?:[\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"' # quoted-string
    r'))@((?:[A-Z0-9]+(?:-*[A-Z0-9]+)*\.)+[A-Z]{2,6}$)', re.IGNORECASE)  # domain

def valid_email(user):
    """
    Returns True if email matches a regular expression, False otherwise
    >>> valid_email('erik@example.com')
    True
    >>> valid_email('@example.com')
    False
    >>> valid_email(';')
    False
    """
    return email_re.match(user) is not None

def parse_email(user):
    """
    Returns (username, domain) if the user is a valid email address, None otherwise
    >>> parse_email('erik@example.com')
    ('erik', 'example.com')
    >>> parse_email('erik@.com')
    >>> parse_email(';')
    """
    match = email_re.match(user)
    if match is not None:
        return match.group(1, 2)
    else:
        return None

def encode_value(obj):
    return pickle.dumps(obj)

def decode_value(buf):
    return pickle.loads(str(buf))
