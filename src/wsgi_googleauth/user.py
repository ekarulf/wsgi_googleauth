import logging
from gdata.contacts.service import ContactsService
from gdata.service import BadAuthentication, CaptchaRequired

def check_password(environ, user, password):
    """
    Authentication handler that checks against Google Accounts (Google Apps / Regular Google Account)
    """
    service = ContactsService(email=user, password=password)
    try:
        service.ProgrammaticLogin()
        logging.info("Successful authentication returned by Google for %s@%s" % (user, domain_name))
        return True
    except BadAuthentication:
        logging.warn("Unsuccessful authentication returned by Google for %s@%s" % (user, domain_name))
        return False
    except CaptchaRequired:
        logging.error("CAPTCHA request returned by Google for %s@%s" % (user, domain_name))
    except:
        logging.error("Unknown error returned by Google for %s@%s" % (user, _domain_name))
    return None

