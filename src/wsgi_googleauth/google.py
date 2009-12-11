# Copyright 2009 - Erik Karulf - MIT License - See LICENSE.txt

import logging
import re
from gdata.contacts.service import ContactsService
from gdata.service import BadAuthentication, CaptchaRequired

class GoogleAuth(object):
    """
    Backend Authentication for using 
    """
    def __init__(self):
        pass
    
    def check_password(self, environ, user, password):
        """
        Authentication handler that checks against Google Accounts (Google Apps / Regular Google Account)
        """
        if not email_re.match(user):
            logging.info("Refusing to authenticate against Google for non-email address {0}".format(user))
            return None

        service = ContactsService(email=user, password=password)
        try:
            service.ProgrammaticLogin()
            logging.info("Successful authentication returned by Google for {0}".format(user))
            return True
        except BadAuthentication:
            logging.warn("Unsuccessful authentication returned by Google for {0}".format(user))
            return False
        except CaptchaRequired:
            logging.error("CAPTCHA request returned by Google for {0}".format(user))
        except:
            logging.error("Unknown error returned by Google for {0}".format(user))
        return None

