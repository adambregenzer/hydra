from xmlrpclib import ServerProxy, Error, Binary
from urlparse import urlsplit, urlunsplit
from threading import Thread
from uuid import uuid4
from common import debug
from datetime import datetime
from decimal import Decimal
import cPickle
import time


MAX_DISPATCH_SLEEP_TIME     = 10
START_DISPATCH_SLEEP_TIME   = 1
STATUS_SLEEP_TIME           = 1


clients = {}
def add_client(id, url, password):
    global clients
    debug('adding client %s (%s)' % (url, id))
    clients[id] = attk_client(id, url, password)


running_attack = None
def start_attack(attack_module, init_args, start_args_list):
    global running_attack
    debug('dispatching attack from server - %s' % attack_module)
    running_attack = attk_dispatcher(str(uuid4()), attack_module, init_args, start_args_list[::-1])
    running_attack.start()



class attk_dispatcher(object):
    def __init__(self, attack_id, attack_module, init_args, start_args_list):
        self.attack_id = attack_id
        self.attack_module = attack_module
        self.init_args = init_args
        self.start_args_list = start_args_list
        self.total_blocks = len(start_args_list)
        self.empty = self.total_blocks == 0
        self.blocks = {}
        self.result = None


    def start(self):
        self.end_time = None
        self.start_time = datetime.now()
        self.dispatch_thread = Thread(target = self.run_dispatch_attacks)
        self.dispatch_thread.setDaemon(False)
        self.dispatch_thread.start()
        self.check_thread = Thread(target = self.run_attack_status)
        self.check_thread.setDaemon(False)
        self.check_thread.start()


    def reset(self):
        global clients, running_attack
        if self.end_time is not None:
            for client in clients.values():
                client.reset()
            running_attack = None


    def run_attack_status(self):
        global clients
        while True:
            running = False
            for client in clients.values():
                running |= client.is_active()
                if client.attack_id == self.attack_id and client.is_active():
                    debug('STATUS CLIENT: %s (%s)' % (repr(client), repr(client.status)))
                    client.get_status()
            if self.empty and not running:
                self.end_time = datetime.now()
                break
            time.sleep(STATUS_SLEEP_TIME)


    def run_dispatch_attacks(self):
        block_id = 0
        sleep_time = START_DISPATCH_SLEEP_TIME
        debug('dispatching %i attacks' % len(self.start_args_list))
        debug('init args %s' % repr(self.init_args))
        while len(self.start_args_list) > 0:
            start_args = self.start_args_list.pop()
            debug('dispatching arg %s' % repr(start_args))
            for client in clients.values():
                debug('attempting to start attack on client %s' % (client.id))
                if not client.is_active():
                    debug('client is not active')
                    client.reset()
                    if client.ping():
                        debug('client is responding to pings')
                        result = client.start(self.attack_id, block_id, self.attack_module, self.init_args, start_args)
                        if result == True:
                            self.blocks[block_id] = [client, None]
                            block_id += 1
                            sleep_time = START_DISPATCH_SLEEP_TIME
                            break
            else:
                debug('could not dispatch block, restarting')
                self.start_args_list.append(start_args)
                time.sleep(sleep_time)
                if sleep_time < MAX_DISPATCH_SLEEP_TIME:
                    sleep_time += 1

        debug('dispatch complete')
        self.empty = True


    def status(self):
        blocks_completed = 0
        records_completed = 0L
        for block in self.blocks.values():
            if block[0] is None:
                blocks_completed += 1
            if block[1] is not None:
                records_completed += block[1]['records_tested']

        if self.end_time is None:
            time_delta = datetime.now() - self.start_time
        else:
            time_delta = self.end_time - self.start_time
        diff_seconds  = time_delta.days * (60 * 60 * 24)
        diff_seconds += time_delta.seconds
        diff_seconds += Decimal(time_delta.microseconds) / Decimal(1000000)

        return {
            'total_blocks': self.total_blocks,
            'blocks_started': len(self.blocks),
            'blocks_completed': blocks_completed,
            'seconds_elapsed': diff_seconds,
            'records_completed': records_completed,
            'rps': Decimal(records_completed) / Decimal(diff_seconds),
        }


    def is_empty(self): return self.empty


class attk_client(object):
    def __init__(self, id, url, password):
        self.id = id
        self.block_id = None
        self.password = password
        self.url = url
        self.xml = ServerProxy(self._make_url())
        self.attack_id = None
        self.status = None


    def _make_url(self):
        url = list(urlsplit(self.url))
        url[1] = 'x:' + self.password + '@' + url[1]
        url[2] = url[2] + 'RPC2'
        return urlunsplit(url)


    def start(self, attack_id, block_id, attack_module, init_args, start_args):
        try:
            result = self.xml.startAttack(attack_id, attack_module, Binary(cPickle.dumps(init_args)), Binary(cPickle.dumps(start_args)))
            if result == True:
                self.block_id = block_id
                self.attack_id = attack_id
                return True
            else:
                return False
        except Error, e:
            debug('ERROR: %s' % e)
            return False


    def get_status(self):
        global running_attack

        if self.attack_id is not None:
            if self.status is not None:
                return self.status

            try:
                status = self.xml.checkAttack(self.attack_id)
                if self.block_id is not None:
                    running_attack.blocks[self.block_id][1] = status
                return status
            except Error, e:
                debug('ERROR: %s' % e)

        return None


    def stop(self):
        if self.attack_id is not None and self.status is None:
            try:
                return self.xml.stopAttack(attack_id)
            except Error, e:
                debug('ERROR: %s' % e)

        return None


    def process_callback(self, attack_id, status):
        global running_attack

        if attack_id == self.attack_id:
            self.status = status
            if self.block_id is not None:
                running_attack.blocks[self.block_id][0] = None
                running_attack.blocks[self.block_id][1] = status
                self.block_id = None
            if not (status['result'] == '' or status['result'] == None):
                running_attack.result = status['result']
            return True
        else:
            return False


    def reset(self):
        if self.is_active(): raise Exception('Can not reset until attack stops.')
        if self.attack_id is not None:
            self.xml.resetAttack(self.attack_id)
        self.attack_id = None
        self.status = None
        if self.block_id is not None:
            running_attack.blocks[self.block_id][0] = None
        self.block_id = None


    def ping(self):
        return self.xml.ping() == 'pong'


    def is_active(self):
        return self.attack_id is not None and self.status is None
