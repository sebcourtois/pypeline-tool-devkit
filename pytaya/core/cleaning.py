
import maya.cmds
mc = maya.cmds

import pymel.core
pm = pymel.core

from pytd.util.logutils import logMsg

def isJunkShape(shape, **kwargs):

    bCheckAttr = kwargs.get("checkIntermediateAttr", kwargs.get("cia", True))

    if isinstance(shape, pm.PyNode):
        sShapePath = shape.name()
    else:
        sShapePath = shape

    if not mc.objectType(sShapePath, isAType="shape"):
        raise TypeError, 'Object is not a shape: "{0}"'.format(sShapePath)

    if bCheckAttr and (not mc.getAttr(sShapePath + ".intermediateObject")):
        return False

    sFutureList = mc.ls(mc.listHistory(sShapePath, future=True, allFuture=True),
                        type="shape", ni=True)

    return False if sFutureList else True

def _yieldChildJunkShapes(obj):

    _mod = mc if isinstance(obj, basestring) else pm

    for shape in _mod.listRelatives(obj, type="shape", path=True):
        if isJunkShape(shape):
            yield shape

def deleteChildJunkShapes(*objList):

    for obj in objList:

        junkShapeList = tuple(_yieldChildJunkShapes(obj))

        if junkShapeList:
            logMsg('Removing junk shapes under "{0}": \n\t{1}'.format(obj, "\n\t".join(junkShapeList)))
            pm.delete(junkShapeList)
