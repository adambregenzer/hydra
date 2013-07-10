from common import AttackTypeBase, ValidationError
from web import websafe, storage
from attk_types import *
from math import ceil

class attk_brute_force(AttackTypeBase):
    name = 'brute_force'
    _default = ''
    _options = {
'loweralpha':                   """abcdefghijklmnopqrstuvwxyz""",
'loweralpha-space':             """abcdefghijklmnopqrstuvwxyz """,
'loweralpha-numeric':           """abcdefghijklmnopqrstuvwxyz0123456789""",
'loweralpha-numeric-space':     """abcdefghijklmnopqrstuvwxyz0123456789 """,
'loweralpha-numeric-symbol14':  """abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()-_+=""",
'loweralpha-numeric-all':       """abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()-_+=~`[]{}|\:;"'<>,.?/""",
'loweralpha-numeric-all-space': """abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()-_+=~`[]{}|\:;"'<>,.?/ """,
'mixalpha':                     """abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ""",
'mixalpha-space':               """abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ """,
'mixalpha-numeric':             """abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789""",
'mixalpha-numeric-space':       """abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 """,
'mixalpha-numeric-symbol14':    """abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_+=""",
'mixalpha-numeric-all':         """abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_+=~`[]{}|\:;"'<>,.?/""",
'mixalpha-numeric-all-space':   """abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_+=~`[]{}|\:;"'<>,.?/ """,
'numeric':                      """0123456789""",
'numeric-space':                """0123456789 """,
'upperalpha':                   """ABCDEFGHIJKLMNOPQRSTUVWXYZ""",
'upperalpha-space':             """ABCDEFGHIJKLMNOPQRSTUVWXYZ """,
'upperalpha-numeric':           """ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789""",
'upperalpha-numeric-space':     """ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 """,
'upperalpha-numeric-symbol14':  """ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_+=""",
'upperalpha-numeric-all':       """ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_+=~`[]{,}|\:;"'<>,.?/""",
'upperalpha-numeric-all-space': """ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_+=~`[]{}|\:;"'<>,.?/ """,
               }

    @classmethod
    def validate(cls, test_value):
        ret_val = storage()
        for arg in ('beginning', 'end', 'alpha'):
            try:    ret_val[arg] = str(test_value[arg])
            except: raise ValidationError(arg + ' must be a string.')

        if test_value.alpha in cls._options:
            ret_val.alpha = cls._options[test_value.alpha]
        else:
            if test_value.alpha == 'custom':
                try:    ret_val.alpha = str(test_value.custom_alpha)
                except: raise ValidationError('custom_alpha must be a string.')
            else:
                raise ValidationError('Must be a valid alphabet.')
        return ret_val

    @classmethod
    def count(cls, name, value, split):
        value = cls.validate(value)
        bf_len = bf_count(value.beginning, value.end, value.alpha)
        if bf_len > split:
            return None

        return bf_len

    @classmethod
    def export(cls, name, value, split):
        beg_name, end_name, alpha_name = name.split(':')
        value = cls.validate(value)

        if split == 1:
            yield {
                beg_name: value.beginning,
                end_name: value.end,
                alpha_name: value.alpha
            }
        else:
            bf_len = bf_count(value.beginning, value.end, value.alpha)
            # Hack, but shouldn't be noticed :)
            chunk_size = (bf_len / split) + 1

            records = 0
            beginning = value.beginning
            while records < bf_len:
                if (bf_len - records) < chunk_size:
                    chunk_size = bf_len - records

                end = bf_add(beginning, value.end, value.alpha, chunk_size - 1)
                yield {
                    beg_name: beginning,
                    end_name: end,
                    alpha_name: value.alpha
                }
                beginning = bf_add(end, value.end, value.alpha, 1)
                records += chunk_size


    @classmethod
    def show_input(cls, name, description):
        retval = """
<td>Brute Force</td>
<td>from: <input name="%s[beginning]" value="" size="17" /><br />
to: <input name="%s[end]" value="" size="17" /><br />
using: <select onchange="this.form.bf_custom.disabled = !(this.options[this.selectedIndex].value == 'custom');(this.options[this.selectedIndex].value == 'custom') && this.form.bf_custom.focus();" name="%s[alpha]">
""" % (name, name, name)
        ops = cls._options.keys()
        ops.sort()
        for op in ops:
            retval += '<option value="%s">%s</option>' % (websafe(op), op)
        retval += """
<option value="custom">custom</option>
</select> <input id="bf_custom" disabled="true" name="%s[custom_alpha]" value="" size="17" />
</td><td>%s</td>""" % (name, description)
        return retval

def bf_count(beg, end, alpha):
    # Calculate the total number of records
    total_records = 1
    beg_len = len(beg)
    beg_rev = beg[::-1]
    end_len = len(end)
    end_rev = end[::-1]
    alp_len = len(alpha)
    r_alpha = alpha[::-1]
    r_alpha_dict = dict((x, r_alpha.index(x)) for x in r_alpha)

    # Calculate number of records to finish start string
    for counter, beg_c in zip(xrange(len(beg_rev)), beg_rev):
        t_len = r_alpha_dict[beg_c]
        t_len *= long(pow(len(alpha), counter))
        total_records += t_len

    # Calculate number of records to reach end's length
    for x in xrange(len(end) - len(beg)):
        total_records += long(pow(alp_len, beg_len + x + 1))

    # Remove possibilities that will not be generated
    for counter, end_c in zip(xrange(len(end_rev)), end_rev):
        t_len = r_alpha_dict[end_c]
        t_len *= long(pow(len(alpha), counter))
        total_records -= t_len

    return total_records



def bf_add(beg, end, alpha, count):
    new_beg = beg
    if count < 0: raise Exception('Can not subtract')
    if count == 0: return new_beg
    if beg == end: raise Exception('Already at the end')
    # TODO: Check for beg > end based on alpha

    beg_len = len(beg)
    beg_rev = beg[::-1]
    end_len = len(end)
    end_rev = end[::-1]
    alp_len = len(alpha)
    r_alpha = alpha[::-1]
    r_alpha_dict = dict((x, r_alpha.index(x)) for x in r_alpha)

    continue_at = 0
    last_total = total_records = 0
    for i, beg_c in zip(xrange(len(beg_rev)), beg_rev):
        t_len  = r_alpha_dict[beg_c]
        t_len *= long(pow(len(alpha), i))
        total_records += t_len
        if total_records <= count:
            new_beg = rcharswap(new_beg,
                                alpha[-1],
                                i)

            if total_records == count:
                return new_beg
        else:
            new_beg = new_beg[:-(i + 1)] + alpha[alpha.index(beg_c) + 1] + alpha[0] * i
            last_total += 1
            continue_at = i
            break

        last_total = total_records

    if total_records < count:
        for x in xrange(len(end) - len(beg)):
            total_records += long(pow(alp_len, beg_len + x + 1))
            if total_records <= count:
                new_beg += alpha[-1]
                if total_records == count:
                    return new_beg
            else:
                new_beg = alpha[0] * (len(new_beg) + 1)
                continue_at = len(new_beg) - 1
                last_total += 1
                break
            last_total = total_records



    if count == last_total:
        return new_beg

    if total_records > count and last_total < count:
        i = continue_at
        total_records = last_total
        while i >= 0:
            add_one_total = long(pow(len(alpha), i))
            while (total_records + add_one_total) <= count:
                beg_c = new_beg[-(i+1)]
                new_beg = rcharswap(new_beg,
                                    alpha[alpha.index(beg_c) + 1],
                                    i)
                total_records += add_one_total
            i -= 1

        if total_records < count:
            raise Exception('WTF? (%i) (%i)' % (total_records, count))
    else:
        raise Exception('Adding past end')

    return new_beg



def rcharswap(value, char, pos):
    """ Swaps character at position [pos] from the end of the string with [char]
    """
    return value[:-(pos + 1)] + char + value[-(pos + 1):][1:]
