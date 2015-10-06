
# from __future__ import print_function
import sys
from .sysutils import toStr

#-------------------------------------------------------------------------------
#    Global Variables Definition
#-------------------------------------------------------------------------------

logSeverity = 0

logSeverityDct = { 'callback':-1, 'silent': 0, 'info' : 1 , 'debug' : 2, 'all' : 3}
invLogSeverityDct = dict((y, x) for (x, y) in logSeverityDct.items())
#-------------------------------------------------------------------------------
#    Functions
#-------------------------------------------------------------------------------
def setLogLevel(levelId):
    global logSeverity

    logSeverity = levelId

def getFunctionName():

    frame = sys._getframe(3)
    sFuncName = frame.f_code.co_name

    try:
        obj = frame.f_locals.get("self", None)
        if obj:

            sObjName = toStr(obj)
            if sObjName.startswith("<") and sObjName.endswith(">"):
                sObjName = obj.__class__.__name__

            sFuncName = sObjName + "." + sFuncName

        else:
            sFuncName = frame.f_globals.get('__name__', '').split('.')[1] + '.' + sFuncName

    except Exception, e:
        print e

    return sFuncName

def getStackDepth():
    i = 2
    while sys._getframe(i).f_back :
        i += 1
#        print i, sys._getframe( i ).f_code.co_name

    return (i - 1)

def __logMsg(*args, **kwargs):

    sSeverity = kwargs.get('log', 'silent')
    global logSeverity

    iSeverity = logSeverityDct[sSeverity]

    bLogMsg = (0 <= iSeverity <= logSeverity) if (logSeverity > -1) else (iSeverity == logSeverity)

    if bLogMsg:

        sJoinedArgs = " ".join(toStr(arg) for arg in args)

        if (iSeverity == 2) or (iSeverity == -1):

            if logSeverity == 3:
                __logPrint("{0}: {1}".format(invLogSeverityDct[iSeverity].upper(), sJoinedArgs), **kwargs)
            else:
                __logPrint("{0}: < {1} > {2}".format(invLogSeverityDct[iSeverity].upper(), getFunctionName(), sJoinedArgs), **kwargs)

        elif (iSeverity == 3):

            iDepth = getStackDepth()
            sStart = ''.rjust(3 * iDepth , '-')
            sEnd = (' ' + getFunctionName() + ' ').ljust(120 - (3 * (iDepth + 1)), '-')
            sToPrint = sStart + sEnd

            __logPrint("{0}: {1} {2}".format(invLogSeverityDct[iSeverity].upper(), sToPrint, sJoinedArgs) , **kwargs)

        elif (iSeverity == 1):

            __logPrint("{0}: {1}".format(invLogSeverityDct[iSeverity].upper(), sJoinedArgs), **kwargs)

        else:
            __logPrint(sJoinedArgs, **kwargs)

def __logPrint(*args, **kwargs):
    bWarning = kwargs.pop("warning", False)

    if bWarning:
        print "# Warning: " + " ".join(toStr(arg) for arg in args) + " #"
    else:
        print " ".join(toStr(arg) for arg in args)

def logMsg(*args, **kwargs):

    try:
        __logMsg(*args, **kwargs)
    except Exception, msg:
        __logPrint(toStr(msg))

def forceLog(**kwargs):

    sSeverity = kwargs.get('log', 'silent')
    iSeverity = logSeverityDct[ sSeverity ]

    def decorate(func):

        def doIt(*args, **kwargs):

            global logSeverity

            iOldSeverity = logSeverity
            logSeverity = iSeverity

            ret = func(*args, **kwargs)

            logSeverity = iOldSeverity

            return ret

        return doIt

    return decorate


def confirmMessage(sLevel, sMsg, sChoiceList):
    pass


