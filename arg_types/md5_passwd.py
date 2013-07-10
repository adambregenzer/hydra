from common import AttackTypeBase, ValidationError
from web import websafe, storage
from attk_types import *
import web
import struct
from common import debug


itoa64_str = "./0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


class md5_passwd(AttackTypeBase):
    name = 'md5_passwd'
    _default = ''

    @classmethod
    def validate(cls, test_value):
        ret_val = storage()
        try:    ret_val = str(test_value)
        except: raise ValidationError('Must be a string.')

        pieces = ret_val.split('$')[1:]
        if len(pieces) != 3 or pieces[0] != '1' or len(pieces[1]) > 8 or len(pieces[2]) != 22:
            raise ValidationError('Not a recognized md5 password hash.')

        for x in pieces[1]:
            if x not in itoa64_str:
                raise ValidationError('Invalid characters.')
        for x in pieces[2]:
            if x not in itoa64_str:
                raise ValidationError('Invalid characters.')

        return ret_val

    @classmethod
    def export(cls, name, value, split = None):
        salt_name, cryptext_name = name.split(':')
        _, _, salt, cryptext = cls.validate(value).split('$')

        if split is None:
            return {
                salt_name: salt,
                cryptext_name: atoi64(cryptext)
            }
        else:
            def _yield_func():
                for x in xrange(split):
                    yield {
                        salt_name: salt,
                        cryptext_name: atoi64(cryptext)
                    }
            return _yield_func()

    @classmethod
    def show_input(cls, name, description):
        return """
<td>MD5 hash</td><td><input name="%s" value="%s"></td><td>%s</td>
""" % (name, cls._default, description)



def chunkify(string_, chunk_size):
  return map(''.join, web.group(string_, chunk_size))

def atoi64(cryptext):
    final_str = ''
    for chunk in chunkify(cryptext + '..', 4):
        pieces = list(itoa64_str.index(x) for x in chunk)
        new_val = 0L
        new_val |= (pieces[3] & 0x3f) << 18
        new_val |= (pieces[2] & 0x3f) << 12
        new_val |= (pieces[1] & 0x3f) <<  6
        new_val |= (pieces[0] & 0x3f)
        final_str += chr((new_val >> 16) & 0xff)
        final_str += chr((new_val >>  8) & 0xff)
        final_str += chr(new_val & 0xff)

    final_str = final_str[:-3] + final_str[-1]
    new_final_str = ''
    for x in [0,3,6,9,12,14,1,4,7,10,13,15,2,5,8,11]:
        new_final_str += final_str[x]
    final_str = new_final_str

    return new_final_str
