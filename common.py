import config, sys, web
import cPickle, random, sha, time, urlparse, os
from time import gmtime, strftime
from datetime import datetime, date
from decimal import Decimal
from base64 import b64decode
from web import storage
from xml.etree.cElementTree import ElementTree
from datetime import datetime
now = datetime.now

urls = [ ]
class ActionMetaClass(type):
    def __init__(klass, name, bases, attrs):
        if 'url' in attrs:
            if isinstance(attrs['url'], (list, tuple)):
                for url_item in attrs['url']:
                    urls.append(config.prefix + url_item)
                    urls.append('%s.%s' % (klass.__module__, name))
            else:
                urls.append(config.prefix + attrs['url'])
                urls.append('%s.%s' % (klass.__module__, name))


class Model(object):
    __metaclass__ = ActionMetaClass
    def __init__(self):
        # Check for credentials
        password = ''
        if 'HTTP_AUTHORIZATION' in web.ctx.environ:
            auth = web.ctx.environ['HTTP_AUTHORIZATION'].split(' ')[1]
            password = b64decode(auth).split(':', 1)[1]

        # Check password
        if password != config.password:
            web.ctx.status = '401 Unauthorized'
            web.ctx.output = ''
            web.header('Content-Type', 'text/html')
            web.header('WWW-Authenticate', 'Basic realm="%s"' % config.realm)

            for attribute in dir(self):
                method = getattr(self, attribute)
                if callable(method) and attribute == attribute.upper():
                    setattr(self, attribute, lambda :'')

        # Disable caching the response
        web.header('Expires', 'Tue, 1 Jan 1980 12:00:00 GMT')
        web.header('Last-Modified', strftime('%a, %d %b %Y %H:%M:%S GMT', gmtime()))
        web.header('Cache-Control', 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, no-transform')
        web.header('Pragma', 'no-cache')

xml_urls = [ ]
def XMLModel(name = None):
    def decorate(func):
        if name is None:
            func_name = func.__name__
        else:
            func_name = name
        if func_name in xml_urls:
            raise Exception('url already added')
        xml_urls.append(func_name)
        xml_urls.append(func)
        return func
    return decorate



class ValidationError(Exception): pass

class AttackTypeBase(object):
    name = None
    _default = None
    _local = False

    def __str__(self):
        return str(self.value)

    @classmethod
    def count(cls, name, value, split):
        return None

    @classmethod
    def export(cls, name, value, split = None):
        if split is None:
            return {name: cls.validate(value)}
        else:
            def _yield_func():
                for x in xrange(split):
                    yield {name: cls.validate(value)}
            return _yield_func()

    @classmethod
    def validate(cls, test_value):
        raise ValidationError('Can not call base class directly.')

    @classmethod
    def show_input(cls, name, description):
        raise Exception('Can not call base class directly.')



def inputd():
    input_dict = {}
    input = web.input()
    for i in input:
        if '[' in i and i[-1] == ']':
            name, sub_name = i[:-1].split('[')
            if name not in input_dict:
                input_dict[name] = storage()
            input_dict[name][sub_name] = input[i]
        else:
            input_dict[i] = input[i]
    return storage(input_dict)


def file_scanner(path):
    file_groups = {}
    for root, dirs, files in os.walk(path):
        for name in files:
            if name[-4:] == '.xml':
                fg = file_group(path, os.path.join(root, name)[len(path)+1:])
                if fg.type != None:
                    if fg.type not in file_groups: file_groups[fg.type] = {}
                    file_groups[fg.type][fg.path] = fg
    return file_groups


class file_group(object):
    def __init__(self, root, path):
        self.root = root
        self.path = path
        try:
            root = ElementTree().parse(os.path.join(root, path))
            self.type = root.get('type').lower()
            self.description = root.get('description')
            self.files = tuple(storage(x.attrib) for x in root)
            self.records = sum(int(x.record_count) for x in self.files)
        except:
            self.type = None
            self.files = tuple()
            self.records = 0
    def fullPath(self):
        return os.path.join(self.root, self.path)
    def dirPath(self):
        return os.path.dirname(self.fullPath())



def gcd(x, y):
    """Return the greatest common denominator of x and y
    """
    while y != 0:
        x, y = y, x % y
    return x

def lcm(x, y):
    """Return the least common multiple of x and y
    """
    return x * y / gcd(x,y)

def remainder(x, y):
    if x < y: x,y = y,x
    return x - ((x / y) * y)

def debug(str_):
    if config.debug:
        sys.stderr.write('DEBUG: %s  - %s\n' % (now().isoformat(' '), str_))

def moneyfmt(value, places=2, curr='$', sep=',', dp='.', pos='', neg='-', trailneg=''):
    """Convert Decimal to a money formatted string.
    places:  required number of places after the decimal point
    curr:    optional currency symbol before the sign (may be blank)
    sep:     optional grouping separator (comma, period, space, or blank)
    dp:      decimal point indicator (comma or period)
             only specify as blank when places is zero
    pos:     optional sign for positive numbers: '+', space or blank
    neg:     optional sign for negative numbers: '-', '(', space or blank
    trailneg:optional trailing minus indicator:  '-', ')', space or blank
    """

    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    q = Decimal((0, (1,), -places))    # 2 places --> '0.01'
    sign, digits, exp = value.quantize(q).as_tuple()
    assert exp == -places
    result = []
    digits = map(str, digits)
    build, next = result.append, digits.pop
    if sign:
        build(trailneg)
    for i in range(places):
        if digits:
            build(next())
        else:
            build('0')
    build(dp)
    i = 0
    while digits:
        build(next())
        i += 1
        if i == 3 and digits:
            i = 0
            build(sep)
    if i == 0:
        build('0')
    build(curr)
    if sign:
        build(neg)
    else:
        build(pos)
    result.reverse()
    return ''.join(result)



view = web.template.render('templates/', cache=config.cache)

import attk_interface
web.template.Template.globals['arg_input'] = attk_interface.arg_input
web.template.Template.globals['date'] = date
web.template.Template.globals['int'] = int
web.template.Template.globals['isinstance'] = isinstance
web.template.Template.globals['len'] = len
web.template.Template.globals['moneyfmt'] = moneyfmt
web.template.Template.globals['prefix'] = config.prefix
web.template.Template.globals['repr'] = repr
web.template.Template.globals['str'] = str
web.template.Template.globals['tuple'] = tuple
web.template.Template.globals['unicode'] = unicode
web.template.Template.globals['web'] = web
web.template.Template.globals['xrange'] = xrange
web.template.Template.globals['zip'] = zip
