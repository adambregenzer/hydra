#!/usr/bin/env python
"""
From: http://webpy.org/tricks/xmlrpc
"""

import web
from SimpleXMLRPCServer import SimpleXMLRPCDispatcher

def get_handler(methodlist):
    dispatcher = SimpleXMLRPCDispatcher(False, None)
    for method in web.group(methodlist, 2):
        dispatcher.register_function(method[1], method[0])
    class rpc:
        def GET(self):
            web.header('Content-Type', 'text/html')
            print get_doc(dispatcher)

        def POST(self):
            response = dispatcher._marshaled_dispatch(web.webapi.data())
            web.header('Content-Type', 'text/xml')
            web.header('Content-length', str(len(response)))
            print response
    return rpc


def get_doc(dispatcher):
    methods = dispatcher.system_listMethods()
    retval = ''
    retval += "<body><h1>Error!</h1>"
    retval += "Method GET is not alowed for XMLRPC requests"
    retval += "List of available methods:"
    retval += "<ul>"
    for method in methods:
        help =  dispatcher.system_methodHelp(method)
        retval += "<li><b>%s</b>: %s</li>" % (method, help)
    retval += "</ul>"
    retval += "</body>"

    return retval
