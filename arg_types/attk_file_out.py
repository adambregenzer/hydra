import config
from common import AttackTypeBase, ValidationError
from web import websafe
import os

class attk_file_out(AttackTypeBase):
    name = 'file_out'

    def __init__(self, type):
        self.type = type

    def validate(self, test_value):
        try:    test_value = str(test_value)
        except: raise ValidationError('Must be a string.')
        if os.path.sep in test_value:
            raise ValidationError('Prefix cannot contain sub-directories.')
        return test_value

    def export(self, name, value, split = None):
        value = self.validate(value)
        file_path_name, file_order_name = name.split(':')

        if split is None:
            return {
                file_path_name: os.path.join(config.file_out_path, value) + '-00.' + self.type,
                file_order_name: 0
            }
        else:
            def _yield_func():
                for x in xrange(split):
                    yield {
                        file_path_name: os.path.join(config.file_out_path, value) + '-%02i.' % x + self.type,
                        file_order_name: x
                    }
            return _yield_func()

    def show_input(self, name, description):
        retval  = """<td>Save File</td><td>Prefix: <input name="%s" />""" % name
        retval += """</td><td>%s</td>""" % description
        return retval
