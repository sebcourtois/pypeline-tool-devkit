
import os
import sys
import time
from collections import Iterable
import copy
import inspect
from functools import partial
import math
import string

import locale
import codecs

LOCALE_ENCODING = locale.getlocale()[1]
if not LOCALE_ENCODING:
    locale.setlocale(locale.LC_ALL, '')
    LOCALE_ENCODING = locale.getlocale()[1]

LOCALE_CODEC = codecs.lookup(LOCALE_ENCODING)
UTF8_CODEC = codecs.lookup("utf-8")

#-------------------------------------------------------------------------------
#    Decorators
#-------------------------------------------------------------------------------

def timer(func):

    def closure(*args, **kwargs):

        startTime = time.time()

        try:
            ret = func(*args, **kwargs)
        except Exception:
            delta = time.time() - startTime
            print '\n"{0}" failed in {1:f} seconds.'.format(func.__name__, delta)
            raise

        delta = time.time() - startTime
        print('\n"{0}" finished in {1:f} seconds.'.format(func.__name__, delta))
        return ret

    return closure
''
#-------------------------------------------------------------------------------
#    Converting
#-------------------------------------------------------------------------------


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
        if fmt == "" or fmt[-2:].lower() not in ["em", "sm", "cm"]:
            if fmt[-1].lower() in ['b', 'c', 'd', 'o', 'x', 'n', 'e', 'f', 'g', '%']:
                # Numeric format.
                return long(self).__format__(fmt)
            else:
                return str(self).__format__(fmt)

        # work out the scale, suffix and base
        factor, suffix = (8, "b") if fmt[-1] in string.lowercase else (1, "B")
        base = 1024 if fmt[-2] in ["e", "c"] else 1000

        # Add the i for the IEC format
        suffix = "i" + suffix if fmt[-2] == "e" else suffix

        mult = ["", "K", "M", "G", "T", "P"]

        val = float(self) * factor
        i = 0 if val < 1 else int(math.log(val, base)) + 1
        v = val / math.pow(base, i)
        v, i = (v, i) if v > 0.5 else (v * base, i - 1)

        # Identify if there is a width and extract it
        width = "" if fmt.find(".") == -1 else fmt[:fmt.index(".")]
        precis = fmt[:-2] if width == "" else fmt[fmt.index("."):-2]

        # do the precision bit first, so width/alignment works with the suffix
        t = ("{0:{1}f} " + mult[i] + suffix).format(v, precis)

        return "{0:{1}}".format(t, width) if width != "" else t


def toStr(value):

    if isinstance(value, str):
        return value
    elif isinstance(value, unicode):
        value = LOCALE_CODEC.encode(value)[0]
    else:
        try:
            value = str(value)
        except UnicodeEncodeError:
            value = toStr(toUnicode(value))

    return value

def toUnicode(value):

    if isinstance(value, unicode):
        return value
    elif isinstance(value, str):
        value = LOCALE_CODEC.decode(value)[0]
    else:
        try:
            value = unicode(value)
        except UnicodeDecodeError:
            value = unicode(value, LOCALE_ENCODING)

    return value

def toUtf8(value):

    value = toUnicode(value)

    if LOCALE_CODEC.name != UTF8_CODEC.name:
        value, _ = UTF8_CODEC.encode(value)

    return value

def listForNone(arg):
    return [] if arg is None else arg

def isIterable(value):
    return isinstance(value, Iterable)

def _argToSequence(seqType, arg):

    if seqType not in (tuple, list, set):
        raise ValueError, "Invalid container type: {0}.".format(seqType)

    if isinstance(arg, seqType):
        return arg
    elif arg in (None, ""):
        return seqType()
    elif isinstance(arg, basestring):
        return seqType((arg,))
    elif isinstance(arg, Iterable):
        return seqType(arg)
    else:
        return seqType((arg,))

def argToList(arg):
    return _argToSequence(list, arg)

def argToTuple(arg):
    return _argToSequence(tuple, arg)

def argToSet(arg):
    return _argToSequence(set, arg)

''
#-------------------------------------------------------------------------------
#    Functions
#-------------------------------------------------------------------------------

def getCaller(**kwargs):

    depth = kwargs.pop("depth", 2)

    try:
        frame = sys._getframe(depth)
    except:
        frame = None

    if frame is None:
        return None

    sFuncName = frame.f_code.co_name

    if ('closure' in sFuncName) or (sFuncName == "doIt"):
        sFuncName = getCaller(depth=depth + 2, **kwargs)

    if kwargs.get('functionOnly', kwargs.get('fo', True)):
        return sFuncName

    obj = frame.f_locals.get("self", None)
    if obj:
        sObjName = str(obj)
        if sObjName.startswith("<") and sObjName.endswith(">"):
            sObjName = obj.__class__.__name__

        sCaller = sObjName + "." + sFuncName
    else:
        sCaller = frame.f_globals.get('__name__', '').split('.')[-1] + '.' + sFuncName

    return sCaller

def isOfType(pyObj, pyClassInfo , strict=False):

    if strict:
        if isinstance(pyClassInfo, tuple):
            return type(pyObj) in pyClassInfo
        else:
            return type(pyObj) is pyClassInfo
    else:
        return isinstance(pyObj, pyClassInfo)

def copyOf(value):

    if isinstance(value, (tuple, list)):
        return value[:]
    elif isinstance(value, (dict, set)):
        return value.copy()
    else:
        return value

def deepCopyOf(value):

    if isinstance(value, (tuple, list)):
        return copy.deepcopy(value)
    elif isinstance(value, (dict, set)):
        return copy.deepcopy(value)
    else:
        return value

def importModule(sModuleName):

    __import__(sModuleName)
    modobj = sys.modules.get(sModuleName)

    return modobj

def isClassOfModule(sModuleName, cls):
    return inspect.isclass(cls) # and (cls.__module__ == sModuleName)

def listClassesFromModule(sModuleName):

    return inspect.getmembers(sys.modules[sModuleName], partial(isClassOfModule, sModuleName))

def isQtApp():

    try:
        from PySide import QtGui
    except ImportError:
        return False
    else:
        return (QtGui.qApp is not None)


def inDevMode():
    s = os.getenv("DEV_MODE_ENV", "0")
    return eval(s) if s else False
