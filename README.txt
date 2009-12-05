===============
wsgi_googleauth
===============

A simple mod_wsgi authentication handler that queries Google Accounts. This includes "Google Apps" accounts as well as regular Google Accounts (gmail.com)

Background
----------
I originally wrote this for mod_python to authenticate Subversion users against Google Apps for the Washington University Aerospace Systems Laboratory  (http://asl.wustl.edu). The traditional / preferred methods of using web authentication would not work as the Subversion clients only support HTTP authentication.

The new version, written in December 2009, has been updated to `Link mod_wsgi http://code.google.com/p/modwsgi/` and Python 2.6. Back-porting to earlier versions of Python should be fairly straightforward, my reason for using Python 2.6 is just to improve clarity.

Setup
-----
wsgi_googleauth uses `Link zc.buildout http://www.buildout.org/` to simplify the installation.::

  python bootstrap.py
  ./bin/buildout

This will install the `Link gdata http://code.google.com/p/gdata-python-client/` dependency automatically.

Usage
-----
Rather than introducing a configuration file, wsgi_googleauth asks you to write a tiny amount of Python code. I promise it won't be painful.

The following is an example file::

  from wsgi_googleauth import GoogleAuth
  from wsgi_googleauth.decorators import *
  
  auth = GoogleAuth()
  
  @DefaultDomain("asl.wustl.edu")
  @Cache(timeout=60*15)
  def check_password(environ, username, password):
    return auth.check_password(environ, username, password)

Let's take this step-by-step.
#. We are creating a default GoogleAuth object
#. We are specifying two decorators, DefaultDomain and Cache. Decorators will be explained in more depth later.
#. We define a method, check_password, that simply returns what the GoogleAuth object tells us.

mod_wsgi looks for a method named check_password with three arguments, environ, username, and password. More information can be found in the mod_wsgi wiki under `Link AccessControlMechanisms http://code.google.com/p/modwsgi/wiki/AccessControlMechanisms`.

Group Authorization
-------------------
The example above handles user authentication, but often we want to control access at a group level. There are many ways of accomplishing this, but we have found that mailing lists in Google Apps work wonderfully. This implies a certain style of group membership but we find this works well.

It should be noted that the account does not need to be authenticated by wsgi_googleauth to be accepted into a group. The example here is if you maintain a separate htpasswd file with email addresses as usernames, you will still allow access to those accounts. We use this often when adding people from other companies to our lab.

Security
--------
wsgi_googleauth provides a reasonable assurance of security, but it does not replace enterprise systems. The following are known limitations:

* Google will require CAPTCHA verification if you trigger some unknown condition. In practice, this has not been an issue. I attempt to minimize the threat with the Cache and LimitFailures decorators
* When Google goes down obviously your authentication system goes down as well. In practice, this has never been problem.
* The Cache decorator will allows a finite window where an old password will still work. In practice, this has never been an issue but my workaround would be restarting apache to manually flush the cache.

If you find yourself concerned about these limitations, you might need a more mature solution.