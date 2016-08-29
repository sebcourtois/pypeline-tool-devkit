
import os
import os.path as osp
import sys
import time
import calendar
from collections import Iterable
import itertools
import inspect
import subprocess
from functools import partial
from importlib import import_module
import locale
import codecs
import imp
from modulefinder import ModuleFinder
from itertools import islice

LOCALE_ENCODING = locale.getlocale()[1]
if not LOCALE_ENCODING:
    locale.setlocale(locale.LC_ALL, '')
    LOCALE_ENCODING = locale.getlocale()[1]

LOCALE_CODEC = codecs.lookup(LOCALE_ENCODING)
UTF8_CODEC = codecs.lookup("utf-8")

''
#===============================================================================
# Decorators
#===============================================================================

def timer(func):

    def closure(*args, **kwargs):

        startTime = time.time()

        try:
            ret = func(*args, **kwargs)
        except Exception:
            delta = time.time() - startTime
            print "<{}> failed in {:f} seconds.".format(func.__name__, delta)
            raise

        delta = time.time() - startTime
        print "<{}> finished in {:f} seconds.".format(func.__name__, delta)
        return ret

    return closure

''
#===============================================================================
# Convertion
#===============================================================================

def toStr(value):

    if isinstance(value, str):
        return value
    elif isinstance(value, unicode):
        value = LOCALE_CODEC.encode(value)[0]
    elif isinstance(value, Exception):
        return toStr(value.args[-1])
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
    elif isinstance(value, Exception):
        return toUnicode(value.args[-1])
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

def fromUtf8(value):

    if isinstance(value, str):
        return UTF8_CODEC.decode(value)[0]
    else:#unicode
        return UTF8_CODEC.encode(value)[0]

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

def chunkate(iterable, chunkSize):

    iterLen = len(iterable)
    n = iterLen / chunkSize
    m = iterLen % chunkSize
    if m:
        n += 1

    for i in xrange(n):
        start = i * chunkSize
        if i == (n - 1):
            stop = start + m
        else:
            stop = ((i + 1) * chunkSize)
        #print start, stop
        yield islice(iterable, start, stop)

def grouper(n, iterable, **kwargs):
    "grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return itertools.izip_longest(*args, **kwargs)

''
#===============================================================================
# Others
#===============================================================================

CREATE_NO_WINDOW = 0x8000000

def callCmd(cmdArgs, catchStdout=False, shell=False, inData=None, noCmdWindow=False):

    iCreationFlags = CREATE_NO_WINDOW if noCmdWindow else 0

    pipe = subprocess.Popen(cmdArgs, shell=shell,
                            stdout=subprocess.PIPE if catchStdout else None,
                            stderr=subprocess.STDOUT if catchStdout else None,
                            creationflags=iCreationFlags)
    if catchStdout:
        outData, errData = pipe.communicate(inData)
        if errData and errData.strip():
            print cmdArgs
            raise subprocess.CalledProcessError(errData)
        return outData
    else:
        return pipe.wait()

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

#def copyOf(value):
#
#    if isinstance(value, (tuple, list)):
#        return value[:]
#    elif isinstance(value, (dict, set)):
#        return value.copy()
#    else:
#        return value
#
#def deepCopyOf(value):
#
#    if isinstance(value, (tuple, list)):
#        return copy.deepcopy(value)
#    elif isinstance(value, (dict, set)):
#        return copy.deepcopy(value)
#    else:
#        return value

def qtGuiApp():
    qApp = qtApp()
    return qApp if isQtGui(qApp) else None

def isQtGui(qApp=None):

    if not qApp:
        qApp = qtApp()
        if not qApp:
            return False

    from PySide import QtGui
    return (qApp.type() != QtGui.QApplication.Tty)

def qtApp():

    qApp = None

    try:
        from PySide import QtGui
    except ImportError:
        return False
    else:
        qApp = QtGui.qApp
        if not qApp:
            qApp = QtGui.QApplication.instance()

    return qApp

def inDevMode():
    s = os.getenv("DEV_MODE_ENV", "0")
    return eval(s) if s else False

def hostApp():
    p, _ = osp.splitext(sys.executable)
    app = osp.basename(p).lower()
    return "" if app == "python" else app

def hostSetEnvFunc():

    func = None
    if "maya" in hostApp():
        try:
            from pymel.util import putEnv
        except ImportError:
            pass
        else:
            func = putEnv

    return func

def updEnv(sVar, in_value, conflict='replace', usingFunc=None):

    opts = ('add', 'replace', 'keep', 'fail')
    if conflict not in opts:
        raise ValueError("Invalid value for 'conflict' arg: '{}'. Try {}"
                         .format(conflict, opts))

    newValue = in_value
    sMsgFmt = " - {} {} : '{}'"
    sAction = "set"
    if sVar in os.environ:
        if conflict == "keep":
            return
        elif conflict == "fail":
            raise EnvironmentError("Env. variable already defined: '{}'='{}'"
                                   .format(sVar, os.environ[sVar]))
        elif conflict == 'add':
            prevValue = os.environ[sVar]
            if in_value in prevValue:
                return
            newValue = os.pathsep.join((prevValue, in_value)) if prevValue else in_value
            sAction = "add"
        else:
            sAction = "upd"

    print sMsgFmt.format(sAction, sVar, in_value)
    if usingFunc:
        usingFunc(sVar, newValue)
    else:
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

#    m = sys.modules.get(sModuleName)
#    if m:
#        print "---------- found", sModuleName, sys.modules[sModuleName]
#        reload(m)
#        return m

    m = import_module(sModuleName)
    reload(m)

    return m


def isClassOfModule(sModuleName, cls):
    return inspect.isclass(cls) # and (cls.__module__ == sModuleName)

def listClassesFromModule(sModuleName):

    return inspect.getmembers(sys.modules[sModuleName], partial(isClassOfModule, sModuleName))


class TdModuleFinder(ModuleFinder):

    def __init__(self, path=None, debug=0, excludes=[], replace_paths=[], **kwargs):

        ModuleFinder.__init__(self, path, debug, excludes, replace_paths)

        self.loadedModules = []

        self.moduleTypes = kwargs.pop("types", (imp.PY_SOURCE, imp.PY_COMPILED))

    def load_module(self, fqname, fp, pathname, fileInfo):

        _, _, iFileType = fileInfo

        m = ModuleFinder.load_module(self, fqname, fp, pathname, fileInfo)

        if iFileType in self.moduleTypes:
            m.__file__ = os.path.normpath(m.__file__).replace("\\", "/")
            self.loadedModules.append(m)

        return m

def reloadModule(m):

    if isinstance(m, basestring):
        m = sys.modules[m]

    sFile = m.__file__[:-1] if m.__file__.endswith(".pyc") else m.__file__

    excluded = [ "Crypto", "git", "async", "PyQt4", "PySide", "MySQLdb",
                "pymel", "maya", "requests", "ecdsa", "paramiko", "shotgun_api3" ]

    finder = TdModuleFinder(debug=0, excludes=excluded)
    finder.load_file(sFile)

    print "\nReloading '{0}':".format(m.__name__)
    for lm in finder.loadedModules[:-1]:
        print "\t", lm.__name__
        if lm.__name__ in sys.modules:
            reload(sys.modules[lm.__name__])

    print "\t", m.__name__
    reload(m)


