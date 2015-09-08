
import os
import os.path as osp
import sys
import time
import calendar
from collections import Iterable
import copy
import inspect
from functools import partial

import locale
import codecs

from .utiltypes import TdModuleFinder

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
#===============================================================================
# Converting
#===============================================================================

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

def toTimestamp(dateTime, timeZone="local"):

    if timeZone == "utc":
        #convert utc time back to utc timestamp
        iUtcStamp = calendar.timegm(dateTime.timetuple())
    else:
        #convert local time back to utc timestamp
        iUtcStamp = time.mktime(dateTime.timetuple())

    return iUtcStamp

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
#===============================================================================
# Functions
#===============================================================================

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

def hostApp():
    p, _ = osp.splitext(sys.executable)
    app = osp.basename(p).lower()
    return "" if app == "python" else app

def updEnv(sVar, value, conflict='replace'):

    opts = ('add', 'replace', 'keep', 'fail')
    if conflict not in opts:
        raise ValueError("Invalid value for 'conflict' arg: '{}'. Try {}"
                         .format(conflict, opts))

    newValue = value
    sMsg = " - set {} : '{}'".format(sVar, value)
    if sVar in os.environ:
        if conflict == "keep":
            sMsg = sMsg.replace("set", "keep")
            print sMsg
            return
        elif conflict == "fail":
            raise EnvironmentError("Env. variable already defined: '{}'='{}'"
                                   .format(sVar, os.environ[sVar]))
        elif conflict == 'add':
            prevValue = os.environ[sVar]
            newValue = os.pathsep.join((prevValue, value)) if prevValue else value
            sMsg = sMsg.replace("set", "add")
        else:
            sMsg = sMsg.replace("set", "upd")

    print sMsg
    os.environ[sVar] = newValue

''
#===============================================================================
# Module utils
#===============================================================================

def importClass(sFullName, in_globals=None, in_locals=None):

    sMod, sClass = sFullName.rsplit(".", 1)
    sImport = "from {} import {}".format(sMod, sClass)
    exec(sImport, in_globals, in_locals)
    return eval(sClass, in_globals, in_locals)

def importModule(sModuleName):

    __import__(sModuleName)
    modobj = sys.modules.get(sModuleName)

    return modobj

def isClassOfModule(sModuleName, cls):
    return inspect.isclass(cls) # and (cls.__module__ == sModuleName)

def listClassesFromModule(sModuleName):

    return inspect.getmembers(sys.modules[sModuleName], partial(isClassOfModule, sModuleName))

def reloadModule(m):

    if isinstance(m, basestring):
        m = sys.modules[m]

    sFile = m.__file__[:-1] if m.__file__.endswith(".pyc") else m.__file__

    excluded = [ "Crypto", "git", "async", "PyQt4", "PySide", "MySQLdb",
                "pymel", "maya" ]

    finder = TdModuleFinder(debug=0, excludes=excluded)
    finder.load_file(sFile)

    print "\nReloading '{0}':".format(m.__name__)
    for lm in finder.loadedModules[:-1]:
        print "\t", lm.__name__
        if lm.__name__ in sys.modules:
            reload(sys.modules[lm.__name__])

    print "\t", m.__name__
    reload(m)


