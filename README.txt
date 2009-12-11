===============
wsgi_googleauth
===============

A simple mod_wsgi authentication handler that queries Google Accounts. This includes "Google Apps" accounts as well as regular Google Accounts (gmail.com)

It is unclear to the author if this is a very stable polished hack or a terrible program. It works well enough for most people.

Background
----------
I originally wrote this for mod_python to authenticate Subversion users against Google Apps for the Washington University Aerospace Systems Laboratory  (http://asl.wustl.edu). The traditional / preferred methods of using web authentication would not work as the Subversion clients only support HTTP authentication.

Throughout 2009 I continued deploying the mod_python authentication script for various labs and small companies. Eventually in December 2009, I decided to clean up the code and formally open source the application.

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

The following is the authentication file we use in the lab::

  from wsgi_googleauth import GoogleAuth
  from wsgi_googleauth.decorators import *
  
  backend = GoogleAuth()
  
  @RequireDomain("asl.wustl.edu")
  @Cache(timeout=60.0*15) # 15 minutes
  def check_password(environ, username, password):
    return backend.check_password(environ, username, password)

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

Decorators
----------
Think of the decorators as short cuts. They are broken down to be as small as possible while still retaining usefulness. There are four built-in decorators. If you find yourself writing the same code over and over again, I would suggest creating a decorator. Bonus points are awarded for submitting your decorator back to me so others may benefit.

Decorators are simply just wrapping functions. They can wrap a regular function or another decorator. This allows decorators to operate just like any other call stack. For this reason, the order of decorators may be important.

Here is a brief description of each of the four decorators. Each decorator has a docstring with example usage.

* Cache - Stores a mapping of arguments (username / password) to a result (True/False). Cache items automatically expire after a fixed timeout.
* DefaultDomain - If the username does not include a valid email address, it attempts to use a specified domain name to create a valid email address. Future decorators / method calls will receive the completed email address if applicable.
* RequireDomain - Requires both the username to be a valid email and the domain name to match a specified value. If not successful, it will return immediately.
* RequireValidEmail - Requires a valid email address. If not successful, it will return immediately.

