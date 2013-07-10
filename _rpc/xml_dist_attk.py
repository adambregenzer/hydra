from common import XMLModel, debug
from xmlrpclib import Fault, Binary
from web import storage
import attk_server
import attk_client
import config
import cPickle



@XMLModel()
def registerClient(password, client_id, url, client_password):
    """Test connection."""
    if password == config.password:
        attk_server.add_client(client_id, url, client_password)
        debug('client registered, returning server id: %s' % config.client_id)
        return config.client_id
    return False


@XMLModel()
def finishAttack(attack_id, client_id, status):
    debug('xml.finishAttack ATTACK-%s CLIENT-%s' % (attack_id, client_id))
    if client_id in attk_server.clients:
        client = attk_server.clients[client_id]
        status = storage(status)
        return client.process_callback(attack_id, status)
    else:
        return False


@XMLModel()
def ping():
    """Test connection."""
    debug('xml.PING')
    return 'pong'


@XMLModel()
def isWorking(attack_id):
    """Checks to see if the attack is still running."""
    debug('xml.isWorking %s' % repr(attack_id in attk_client.attacks))
    return attack_id in attk_client.attacks


@XMLModel()
def startAttack(attack_id, attack_module, init_args, attack_args):
    init_args = cPickle.loads(init_args.data)
    attack_args = cPickle.loads(attack_args.data)
    debug('xml.startAttack args %s %s %s %s' % (repr(attack_id), repr(attack_module), repr(init_args), repr(attack_args)))
    try:
        if attack_id not in attk_client.attacks:
            attk_client.start_attack(attack_id, attack_module, init_args, attack_args)
            return True
        elif attk_client.attacks[attack_id].running == False:
            del attk_client.attacks[attack_id]
            attk_client.start_attack(attack_id, attack_module, init_args, attack_args)
            return True
        else:
            raise err_running()
    except Fault: raise


@XMLModel()
def stopAttack(attack_id):
    debug('xml.stopAttack %s' % repr(attack_id in attk_client.attacks))
    try:
        if attack_id in attk_client.attacks:
            attk_client.attacks[attack_id].stop()
            return True
        else:     raise err_not_running()
    except Fault: raise


@XMLModel()
def resetAttack(attack_id):
    debug('xml.resetAttack %s' % attack_id)
    try:
        if attack_id in attk_client.attacks:
            if attk_client.attacks[attack_id].running == False:
                del attk_client.attacks[attack_id]
                return True
            else:
                  raise err_running()
        else:     raise err_not_running()
    except Fault: raise


@XMLModel()
def checkAttack(attack_id):
    debug('xml.checkAttack %s' % attack_id)
    try:
        if attack_id in attk_client.attacks:
            return attk_client.attacks[attack_id].check()
        else:     raise err_not_running()
    except Fault: raise







def err_running():      raise Fault(1000, 'Attack is running')
def err_not_running():  raise Fault(1001, 'Attack is not running')
def err_not_start():    raise Fault(1002, 'Could not start attack')
def err_not_stop():     raise Fault(1003, 'Could not stop attack')
