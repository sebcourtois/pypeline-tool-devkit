
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
from encodings import aliases
import imp
from modulefinder import ModuleFinder
from itertools import islice
#from pprint import pprint

SYSTEM_ENCODING = locale.getlocale()[1]
if not SYSTEM_ENCODING:
    #locale.setlocale(locale.LC_ALL, '')
    SYSTEM_ENCODING = locale.getdefaultlocale()[1]

SYSTEM_ENCODING = aliases.aliases.get(SYSTEM_ENCODING, SYSTEM_ENCODING)
SYSTEM_CODEC = codecs.lookup(SYSTEM_ENCODING)
UTF8_CODEC = codecs.lookup("utf_8")

ALL_CODEC_ALIASES = {}
for sAlias, sCodec in aliases.aliases.iteritems():
    ALL_CODEC_ALIASES.setdefault(sCodec, []).append(sAlias)
del sAlias, sCodec

#pprint(ALL_CODEC_ALIASES)
#pprint(aliases.aliases)

SYS_CODEC_ALIASES = [SYSTEM_ENCODING] + ALL_CODEC_ALIASES[SYSTEM_ENCODING]
UTF8_CODEC_ALIASES = ["utf_8"] + ALL_CODEC_ALIASES["utf_8"]

SYS_EXEC_PREFIX = sys.exec_prefix.replace("\\", "/").rstrip("/") + "/"


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

def toStr(value, encoding=SYSTEM_ENCODING):

    if isinstance(value, unicode):
        return str_(value, encoding)

    if isinstance(value, Exception):
        return toStr(value.args[-1] if value.args else str(value))

    if isinstance(value, str):
        return value

    try:
        return str(value)
    except UnicodeEncodeError:
        return toStr(toUnicode(value))

def str_(value, encoding=SYSTEM_ENCODING):

    if encoding in SYS_CODEC_ALIASES:
        return SYSTEM_CODEC.encode(value)[0]
    elif encoding in UTF8_CODEC_ALIASES:
        return UTF8_CODEC.encode(value)[0]
    else:
        return value.encode(encoding)

def toUnicode(value, encoding=SYSTEM_ENCODING):

    if isinstance(value, str):
        return unicode_(value, encoding)

    if isinstance(value, Exception):
        return toUnicode(value.args[-1] if value.args else str(value))

    if isinstance(value, unicode):
        return value

    try:
        return unicode(value)
    except UnicodeDecodeError:
        return unicode(value, SYSTEM_ENCODING)

def unicode_(value, encoding=SYSTEM_ENCODING):

    if encoding in SYS_CODEC_ALIASES:
        return SYSTEM_CODEC.decode(value)[0]
    elif encoding in UTF8_CODEC_ALIASES:
        return UTF8_CODEC.decode(value)[0]
    else:
        return value.decode(encoding)

def fromUtf8(value):

    if isinstance(value, str):
        return UTF8_CODEC.decode(value)[0]
    else:#unicode
        return UTF8_CODEC.encode(value)[0]

def toTimestamp(dateTime, timeZone="local"):

    if timeZone == "utc":
        #convert utc time back to utc timestamp
        return calendar.timegm(dateTime.timetuple())
    else:
        #convert local time back to utc timestamp
        return time.mktime(dateTime.timetuple())

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

def qtGuiApp():
    qApp = qtApp()
    return qApp if isQtGui(qApp) else None

def isQtGui(in_qApp=None):

    qApp = in_qApp if in_qApp else qtApp()
    if not qApp:
        return False

    from PySide import QtGui

    if not isinstance(qApp, QtGui.QApplication):
        return False

    return (qApp.type() != QtGui.QApplication.Tty)

def qtApp():
    try:
        from PySide import QtGui
    except ImportError:
        return

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

def updEnv(sVar, in_value, conflict='replace', usingFunc=None, record=None):

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

    if record is not None:
        record[sVar] = newValue

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
            p = os.path.normpath(m.__file__).replace("\\", "/")
            if not osp.normcase(p).startswith(osp.normcase(SYS_EXEC_PREFIX)):
                m.__file__ = p
                self.loadedModules.append(m)

        return m

def reloadModule(m=None, p=None):

    if m:
        if isinstance(m, basestring):
            m = sys.modules[m]
        sFile = m.__file__
    elif p:
        sFile = p

    if sFile.endswith(".pyc"):
        sFile = sFile[:-1]

    excluded = [ "Crypto", "git", "async", "PyQt4", "PySide", "MySQLdb",
                "pymel", "maya", "requests", "ecdsa", "paramiko", "shotgun_api3" ]

    finder = TdModuleFinder(debug=0, excludes=excluded)
    finder.load_file(sFile)

    sReloaded = m.__name__ if m else p

    print "\nReloading '{0}':".format(sReloaded)
    for lm in finder.loadedModules[:-1]:
        print "\t", lm.__name__
        if lm.__name__ in sys.modules:
            reload(sys.modules[lm.__name__])

    if m:
        print "\t", sReloaded
        reload(m)


