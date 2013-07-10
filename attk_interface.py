import os
import inspect
import config
from common import AttackTypeBase

attk_modules = {}
for mod in os.listdir(os.path.join(os.getcwd(), 'modules')):
    module_name, ext = os.path.splitext(mod)
    if (ext == '.py' or ext == '.so') and module_name[0] != '_':
        if config.debug:
            print 'attack module:', module_name, ':::', ext
        module = __import__('.'.join(['modules', module_name]), globals(), locals(), [''])
        attk_modules[module_name] = module


arg_types = {}
for mod in os.listdir(os.path.join(os.getcwd(), 'arg_types')):
    module_name, ext = os.path.splitext(mod)
    if (ext == '.py' or ext == '.so') and module_name[0] != '_':
        if config.debug:
            print 'arg types:', module_name, ':::', ext
        module = __import__('.'.join(['arg_types', module_name]), globals(), locals(), [''])
        for obj in module.__dict__.values():
            if inspect.isclass(obj) and obj is not AttackTypeBase and issubclass(obj, AttackTypeBase):
                if hasattr(obj, 'name'):
                    arg_types[obj.name] = obj
                else:
                    arg_types[obj.__name__] = obj


def get_type(type):
    if '(' in type:
        type, args = type[:-1].split('(')
        args = args.split(',')
        return arg_types[type](*args)
    else:
        return arg_types[type]


def list_modules():
    mod_names = attk_modules.keys()
    mod_names.sort()
    return tuple((mod, attk_modules[mod].__doc__) for mod in mod_names)

def arg_input(name, (type, description)):
    return get_type(type).show_input(name, description)

def arg_export(name, (type, description), value = None, split = None):
    return get_type(type).export(name, value, split)

def arg_count(name, (type, description), value, split):
    return get_type(type).count(name, value, split)

def add_local_args(start_args, attk_mod_name):
    attk_module = attk_modules[attk_mod_name]
    for arg_name in attk_module.start_args:
        arg_details = attk_module.start_args[arg_name]
        type = get_type(arg_details[0])
        if type._local:
            start_args.update(type.export(arg_name))

def parse_args(attk_module, web_args, num_clients):
    init_args = {}
    start_args_list = []
    start_args_preload = []
    for arg in web_args:
        if arg in attk_module.init_args:
            init_args.update(arg_export(arg, attk_module.init_args[arg], web_args[arg]))
        elif arg in attk_module.start_args:
            start_args_preload.append(arg)

    for arg in attk_module.init_args:
        if arg not in web_args:
            init_args.update(arg_export(arg, attk_module.init_args[arg]))

    for arg in attk_module.start_args:
        if arg not in web_args:
            start_args_preload.append(arg)

    count = 0
    for arg in start_args_preload:
        if arg in web_args:
            t_count = arg_count(arg, attk_module.start_args[arg], web_args[arg], num_clients)
        else:
            t_count = arg_count(arg, attk_module.start_args[arg], None, num_clients)
        if t_count != None:
            if count == 0:
                count = t_count
            else:
                if count != t_count:
                    raise Exception('Can not start attack, incompatible arguments.')
    if count == 0:
        count = num_clients

    start_args_preload_gens = []
    for arg in start_args_preload:
        if arg in web_args:
            start_args_preload_gens.append(arg_export(arg, attk_module.start_args[arg], web_args[arg], count))
        else:
            start_args_preload_gens.append(arg_export(arg, attk_module.start_args[arg], None, count))
    for x in xrange(count):
        start_args = {}
        for arg in start_args_preload_gens:
            start_args.update(arg.next())
        start_args_list.append(start_args)
    return (init_args, start_args_list)

