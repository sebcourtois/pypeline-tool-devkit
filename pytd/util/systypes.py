

import math
import string
import locale
from pytd.util.sysutils import toUnicode

THOUSAND_SEP = locale.localeconv()['thousands_sep']

class MemSize(long):
    """ define a size class to allow custom formatting
        format specifiers supported : 
            em : formats the size as bits in IEC format i.e. 1024 bits (128 bytes) = 1Kib 
            eM : formats the size as Bytes in IEC format i.e. 1024 bytes = 1KiB
            sm : formats the size as bits in SI format i.e. 1000 bits = 1kb
            sM : formats the size as bytes in SI format i.e. 1000 bytes = 1KB
            cm : format the size as bit in the common format i.e. 1024 bits (128 bytes) = 1Kb
            cM : format the size as bytes in the common format i.e. 1024 bytes = 1KB
    """
    def __format__(self, fmt):
        # is it an empty format or not a special format for the size class
        if fmt in ("", "n"):
            sSep = 'n' if THOUSAND_SEP else ','
            if THOUSAND_SEP and isinstance(fmt, unicode):
                return toUnicode(long(self).__format__(sSep))
            else:
                return long(self).__format__(sSep)

        elif fmt[-2:].lower() not in ["em", "sm", "cm"]:
            if fmt[-1].lower() in ['b', 'c', 'd', 'o', 'x', 'e', 'f', 'g', '%']:
                return long(self).__format__(fmt)
            else:
                return long(self).__format__(',').__format__(fmt)

        # work out the scale, suffix and base
        factor, suffix = (8, "b") if fmt[-1] in string.lowercase[:26] else (1, "B")
        base = 1024 if fmt[-2] in ["e", "c"] else 1000

        # Add the i for the IEC format
        suffix = "i" + suffix if fmt[-2] == "e" else suffix

        mult = ["", "K", "M", "G", "T", "P"]

        val = float(self) * factor
        i = 0 if val < 1 else int(math.log(val, base))# + 1
        v = val / math.pow(base, i)
        v, i = (v, i) if v > 0.5 else (v * base, i - 1)

        # Identify if there is a width and extract it
        width = "" if fmt.find(".") == -1 else fmt[:fmt.index(".")]
        precis = fmt[:-2] if width == "" else fmt[fmt.index("."):-2]

        # do the precision bit first, so width/alignment works with the suffix
        t = ("{0:{1}f} " + mult[i] + suffix).format(v, precis)

        return "{0:{1}}".format(t, width) if width != "" else t

    def __repr__(self):
        try:
            return '{:n} Bytes'.format(self)
        except Exception:# as e:
            return long.__repr__(self)
