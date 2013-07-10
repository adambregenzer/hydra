import web
from web import storage
import config
from common import Model, view, inputd
import attk_interface
import attk_server
import attk_client


class reset(Model):
    url = '/reset'

    def GET(self):
        if attk_server.running_attack is not None:
            attk_server.running_attack.reset()
        web.seeother('/')


class index(Model):
    url = '/'

    def GET(self):
        modules = attk_interface.list_modules()

        if config.server_url is None:
            if attk_server.running_attack is None:
                print view.index(modules, attk_server.clients)
            else:
                block_ids = attk_server.running_attack.blocks.keys()
                block_ids.sort()
                print view.running_index(attk_server.running_attack, storage(attk_server.running_attack.status()), block_ids, attk_server.clients)
        else:
            for attack in attk_client.attacks.values():
                attack.check()
            print view.client_index(attk_client.server, attk_client.attacks)


    def POST(self):
        attk_mod_name = web.input('attk_mod')['attk_mod']
        attk_module = attk_interface.attk_modules[attk_mod_name]

        print view.set_args(attk_module.init_args, attk_module.start_args, attk_mod_name)


class set_args(Model):
    url = '/set_args'

    def GET(self):
        web.seeother('/')

    def POST(self):
        attk_mod_name = web.input('attk_mod')['attk_mod']
        attk_module = attk_interface.attk_modules[attk_mod_name]

        web_args = inputd()
        num_clients = len(attk_server.clients)
        init_args, start_args_list = attk_interface.parse_args(attk_module, web_args, num_clients)

        attk_server.start_attack(attk_mod_name, init_args, start_args_list)
        web.seeother('/')
