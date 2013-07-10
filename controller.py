#!/usr/bin/env python
import os
import web, config, common
import webxml
import attk_client
import attk_server
from common import debug
from threading import Timer

for mod in os.listdir(os.path.join(os.getcwd(), '_rpc')):
    module_name, ext = os.path.splitext(mod)
    debug('xmlrpc file: ' + module_name)
    if module_name.startswith('xml_') and ext == '.py':
        module = __import__(os.path.join('_rpc', module_name))


for mod in os.listdir(os.path.join(os.getcwd(), '_cgi')):
    module_name, ext = os.path.splitext(mod)
    debug('cgi file: ' + module_name)
    if module_name.startswith('cgi_') and ext == '.py':
        module = __import__(os.path.join('_cgi', module_name))


if '/RPC2' in common.urls:
    raise Exception('xmlrpc url already defined, remove reference to /RPC2 to enable xmlrpc')
urls = [ '/RPC2', 'webxml_rpc' ] + common.urls
webxml_rpc = webxml.get_handler(common.xml_urls)


def add_prefix(func):
    def insert_prefix(url, *largs, **kwargs):
        return func(config.prefix + url, *largs, **kwargs)
    return insert_prefix
web.redirect = add_prefix(web.redirect)
web.found = add_prefix(web.found)
web.seeother = add_prefix(web.seeother)
web.tempredirect = add_prefix(web.tempredirect)


def initialize():
    debug('my id %s' % config.client_id)
    if config.server_url is not None:
        debug('registering with server %s' % config.server_url)
        attk_client.register(config.server_password, config.server_url)
    else:
        debug('registering myself as a client')
        attk_client.register(config.password, config.url)
initializer = Timer(1.0, initialize)


if __name__ == "__main__":
    initializer.start()
    web.run(urls, globals(), *config.middleware)
