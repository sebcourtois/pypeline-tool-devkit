
import os
import sys

import maya.cmds as mc
import pymel.core as pm

from pytd.util.fsutils import pathJoin


def listForNone(arg):
    return [] if arg is None else arg

def PyNone(arg):
    if arg:
        if isinstance(arg, basestring):
            return pm.PyNode(arg)
    return arg

def argsToPyNode(*argList):

    newArgList = []
    #print argList
    for arg in argList:
        if isinstance(arg, (tuple, list)):
            newAList = map(PyNone, listForNone(arg))
            newArgList.append(newAList)
        else:
            newArgList.append(PyNone(arg))
    #print newArgList
    if len(newArgList) > 1:
        return newArgList
    else:
        return newArgList[0]

def argToStr(arg, bNodeName=True):

    if isinstance(arg, str):
        return arg
    elif arg is None:
        return ""
    elif isinstance(arg, pm.PyNode):
        return arg.nodeName() if bNodeName else arg.name()
    elif isinstance(arg, pm.Attribute):
        return arg.name()
    else:
        return str(arg)

def pynodeToStr(arg):

    if isinstance(arg, (tuple, list, set)):
        return tuple(argToStr(a, False) for a in arg)
    else:
        return argToStr(arg)

def currentMayapy():

    if sys.platform == "win32":
        p = pathJoin(os.environ["MAYA_LOCATION"], "bin", "mayapy.exe")
    else:
        raise NotImplementedError("Platform not supported yet: '{}'".format(sys.platform))

    if not os.path.exists(p):
        raise EnvironmentError("Could not found Maya's python interpreter: '{}'"
                               .format(p))

    return p

def withSelectionRestored(func):

    def doIt(*args, **kwargs):

        bKeepSel = kwargs.pop("restoreSelection", kwargs.pop("rsl", True))

        if bKeepSel:
            sPrevSelList = mc.ls(sl=True)[:]

        try:
            ret = func(*args, **kwargs)
        finally:
            if bKeepSel:
                sNewSelList = mc.ls(sl=True)[:]
                if sNewSelList:
                    try:mc.select(sNewSelList, deselect=True, noExpand=True)
                    except ValueError:pass

                if sPrevSelList:
                    try:mc.select(sPrevSelList, add=True, noExpand=True)
                    except ValueError:pass
        return ret
    return doIt
