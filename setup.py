from setuptools import setup, find_packages

setup(
    name = "wsgi_googleauth",
    version = "0.1",
    url = 'http://www.fort-awesome.net/wiki/wsgi_googleauth',
    license = 'MIT',
    description = "A WSGI authentication handler that queries Google",
    author = 'Erik Karulf',
    # Below this line is tasty Kool-Aide provided by the Cargo Cult
    packages = find_packages('src'),
    package_dir = {'': 'src'},
    install_requires = ['setuptools'],
)