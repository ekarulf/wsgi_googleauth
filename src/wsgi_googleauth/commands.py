# Copyright 2009 - Erik Karulf - MIT License - See LICENSE.txt

def noop():
  """
  No Operation - zc.buildout requires an endpoint method
  """
  pass

def _logging():
    # Logging Configuration
    import sys
    import logging
    logger = logging.getLogger('')
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
def test_login():
    """
    Attempt authentication
    """
    _logging()
    from getpass import getpass
    from policy import check_password
    while True:
        try:
            username = raw_input("User: ")
            password = getpass()
        except KeyboardInterrupt:
            break
        result = check_password(None, username, password)
        if result is True:
            print "Password correct!"
        elif result is False:
            print "Password incorrect"
        else:
            print "User not found"
        again = raw_input("Again (yes/No)? ").lower()
        if not again == "yes":
            break
    return 0

    