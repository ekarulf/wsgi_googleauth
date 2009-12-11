# Copyright 2009 - Erik Karulf - MIT License - See LICENSE.txt

import logging
from wsgi_googleauth.util import valid_email
from gdata.contacts.service import ContactsService
from gdata.service import BadAuthentication, CaptchaRequired

class GoogleAuth(object):
    """
    Backend using Google Accounts as an authentication source
    """
    def __init__(self):
        pass
    
    def check_password(self, environ, user, password):
        """
        Authentication handler that checks against Google Accounts (Google Apps / Regular Google Account)
        """
        if not valid_email(user):
            logging.info("Refusing to authenticate against Google for non-email address {0}".format(user))
            return None

        service = ContactsService(email=user, password=password)
        try:
            service.ProgrammaticLogin()
        except BadAuthentication:
            logging.warn("Unsuccessful authentication returned by Google for {0}".format(user))
            return False
        except CaptchaRequired:
            logging.error("CAPTCHA request returned by Google for {0}".format(user))
        except:
            logging.error("Unknown error returned by Google for {0}".format(user))
        else:
            logging.info("Successful authentication returned by Google for {0}".format(user))
            return True
        return None

