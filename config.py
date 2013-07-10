import web
from uuid import uuid4
from urllib import urlopen


# Attack options
threads = 10
file_in_path = '/home/attk/files'
file_out_path = '/home/attk/files/out'


# Distributed options
client_id = str(uuid4())
#url = 'http://' + urlopen('http://169.254.169.254/latest/meta-data/public-hostname').read() + ':8080/'
#server_url = 'http://127.0.0.1:8080/'
#server_password = 'testing'
url = 'http://127.0.0.1:8080/'
password = 'testing'
server_url = None
server_password = None


# Web options
prefix = ''


# Internal options
web.webapi.internalerror = web.debugerror
# middleware = [web.reloader]
# cache = False
middleware = []
cache = True
realm = 'hydra'
debug = True

