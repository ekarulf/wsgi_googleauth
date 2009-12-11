import doctest
import wsgi_googleauth.util
import wsgi_googleauth.decorators

if __name__ == "__main__":
    doctest.testmod(wsgi_googleauth.util)
    doctest.testmod(wsgi_googleauth.decorators)
