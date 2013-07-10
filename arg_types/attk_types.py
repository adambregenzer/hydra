from common import AttackTypeBase, ValidationError
from binascii import unhexlify
import config
from web import websafe

class attk_integer(AttackTypeBase):
    name = 'integer'
    _default = 0

    @classmethod
    def validate(cls, test_value):
        try:    return long(test_value)
        except: raise ValidationError("Must be an integer.")

    @classmethod
    def show_input(cls, name, description):
        return """
<td>%s</td><td><input name="%s" value="%s"></td><td>%s</td>
""" % (name, name, cls._default, description)



class attk_string(AttackTypeBase):
    name = 'string'
    _default = ''

    @classmethod
    def validate(cls, test_value):
        try:    return str(test_value)
        except: raise ValidationError("Must be a string.")

    @classmethod
    def show_input(cls, name, description):
        return """
<td>%s</td><td><input name="%s" value="%s"></td><td>%s</td>
""" % (name, name, cls._default, description)



class attk_hex(AttackTypeBase):
    name = 'hex'
    _default = ''

    @classmethod
    def validate(cls, test_value):
        try:    retval = str(test_value)
        except: raise ValidationError("Must be a string.")
        if len(retval) / 2 * 2 != len(retval):
            raise ValidationError("Must have an even length.")
        for x in retval:
            if x not in '0123456789abcdefABCDEF':
                raise ValidationError("Must be hexadecimal (0-9A-Fa-f).")
        return retval

    @classmethod
    def export(cls, name, value, split = None):
        if split is None:
            return {name: unhexlify(cls.validate(value))}
        else:
            def _yield_func():
                for x in xrange(split):
                    yield {name: unhexlify(cls.validate(value))}
            return _yield_func()

    @classmethod
    def show_input(cls, name, description):
        return """
<td>%s</td><td><input name="%s" value="%s"></td><td>%s</td>
""" % (name, name, cls._default, description)



class attk_threads(AttackTypeBase):
    name = 'threads'
    _default = 2
    _local = True

    @classmethod
    def validate(cls, test_value):
        try:    return int(test_value)
        except: raise ValidationError('Number of threads must be an integer')

    @classmethod
    def export(cls, name, value = None, split = None):
        try:    num_threads = cls.validate(config.threads)
        except: num_threads = cls._default
        if split is None:
            return {name: num_threads}
        else:
            def _yield_func():
                for x in xrange(split):
                    yield {name: num_threads}
            return _yield_func()

    @classmethod
    def show_input(cls, name, description):
        return None
