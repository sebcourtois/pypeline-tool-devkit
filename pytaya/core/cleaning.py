
import maya.cmds
mc = maya.cmds

import pymel.core
pm = pymel.core

def _yieldChildJunkShapes(obj):

    _mod = mc if isinstance(obj, basestring) else pm

    for shape in _mod.listRelatives(obj, type="shape", path=True):
        if fncUtil.isJunkShape(shape):
            yield shape

def deleteChildJunkShapes(*objList):

    for obj in objList:

        junkShapeList = tuple(_yieldChildJunkShapes(obj))

        if junkShapeList:
            logMsg('Removing junk shapes under "{0}": \n\t{1}'.format(obj, joinName(*junkShapeList, sep="\n\t", alias=False)))
            pm.delete(junkShapeList)
