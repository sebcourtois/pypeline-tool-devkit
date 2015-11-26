
import os
import sys

import maya.cmds as mc

from pytd.util.fsutils import pathJoin

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
