import config
import os
from common import AttackTypeBase, ValidationError, file_scanner, lcm, remainder
from web import websafe
from math import ceil

class attk_file_in(AttackTypeBase):
    name = 'file_in'

    def __init__(self, type):
        self.type = type

    def validate(self, test_value):
        try:    test_value = str(test_value)
        except: raise ValidationError('Must be a string.')

        files = file_scanner(config.file_in_path)
        file_paths = files[self.type].keys()

        if test_value not in file_paths:
            raise ValidationError('Must be a file group.')

        return test_value

    def count(self, name, value, split):
        value = self.validate(value)

        file_groups = file_scanner(config.file_in_path)
        file_group = file_groups[self.type][value]

        file_path_name, skip_records_name, count_records_name = name.split(':')

        if len(file_group.files) == split:
            return split
        elif len(file_group.files) >= split:
            return len(file_group.files)
        else:
            return lcm(split, len(file_group.files))

    def export(self, name, value, split):
        value = self.validate(value)
        file_groups = file_scanner(config.file_in_path)
        file_group = file_groups[self.type][value]
        file_path_name, skip_records_name, count_records_name = name.split(':')
        num_files = len(file_group.files)

        if num_files == split:
            for attk_file in file_group.files:
                yield {
                    file_path_name: os.path.join(file_group.dirPath(), attk_file.src),
                    skip_records_name: 0,
                    count_records_name: 0
                }
        elif num_files < split and remainder(split, num_files) == 0:
            for attk_file in file_group.files:
                attk_file.record_count = long(attk_file.record_count)
                records = 0
                chunk_size = long(ceil(1.0 * attk_file.record_count / (split / len(file_group.files))))
                while records < attk_file.record_count:
                    if (attk_file.record_count - records) < chunk_size:
                        chunk_size = attk_file.record_count - records
                    yield {
                        file_path_name: os.path.join(file_group.dirPath(), attk_file.src),
                        skip_records_name: records,
                        count_records_name: chunk_size
                    }
                    records += chunk_size
        else:
            raise Exception("Can not split.")

    def show_input(self, name, description):
        retval = """<td>File</td><td><select name="%s">""" % name
        files = file_scanner(config.file_in_path)
        files = files[self.type].values()
        for file in files:
            retval += '<option value="%s">%s</option>' % (websafe(file.path), file.description)
        retval += """</select></td><td>%s</td>""" % description
        return retval
