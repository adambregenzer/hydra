import attk_interface
from urlparse import urlsplit, urlunsplit
from xmlrpclib import ServerProxy
import config
from common import debug


server = None


def register(password, url):
    global server
    debug('registering server %s' % url)
    server = attk_server(password, url)
    server.register()


attacks = {}


def start_attack(attack_id, attack_module, init_args, attack_args):
    debug('starting attack on client - %s %s' % (attack_id, attack_module))
    attacks[attack_id] = attack_wrapper(
        attack_id,
        attack_module,
        init_args,
        attack_args,
    )


class attack_wrapper(object):
    def __init__(self, attack_id, attack_module, init_args, attack_args):
        self.attack_id = attack_id
        self.attk_mod_name = attack_module
        self.attk_mod = attk_interface.attk_modules[attack_module].attack_class()
        attk_interface.add_local_args(attack_args, self.attk_mod_name)
        debug('starting module %s' % repr(self.attk_mod))
        self.attk_mod.callback = self.callback
        debug('callback set')
        self.attk_mod.initialize(**init_args)
        debug('initialized')
        self.attk_mod.start(**attack_args)
        debug('started')
        self.running = True
        self.status = None

    def callback(self, **status):
        global server

        debug('client callback %s' % repr(status))
        self.status = status
        self.running = False
        server.finish_attack(self.attack_id, self.status)

    def stop(self):
        debug('client stopping')
        return self.attk_mod.stop()

    def check(self):
        debug('client check')
        self.status = self.attk_mod.check()
        return self.status


class attk_server(object):
    def __init__(self, password, url):
        self.id = None
        self.password = password
        self.url = url
        self.xml = ServerProxy(self._make_url())

    def _make_url(self):
        url = list(urlsplit(self.url))
        url[1] = 'x:' + self.password + '@' + url[1]
        url[2] = url[2] + 'RPC2'
        return urlunsplit(url)

    def ping(self):
        debug('client pinging server')
        return self.xml.ping() == 'pong'

    def finish_attack(self, attack_id, status):
        debug('client finishing attack with server')
        self.xml.finishAttack(attack_id, config.client_id, status)

    def register(self):
        debug('client registering with server')
        retval = self.xml.registerClient(
            self.password,
            config.client_id,
            config.url,
            config.password,
        )
        if retval is not False:
            self.id = retval
