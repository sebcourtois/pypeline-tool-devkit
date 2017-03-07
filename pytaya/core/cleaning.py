
import maya.cmds
mc = maya.cmds

import pymel.core
pm = pymel.core

from pytd.util.logutils import logMsg

from pytaya.core.general import lsNodes


def isJunkShape(shape, **kwargs):

    bCheckAttr = kwargs.get("checkIntermediateAttr", kwargs.get("cia", True))

    if isinstance(shape, pm.PyNode):
        sShapePath = shape.name()
    else:
        sShapePath = shape

    if not mc.objectType(sShapePath, isAType="shape"):
        raise TypeError, 'Object is not a shape: "{0}"'.format(sShapePath)

    if mc.referenceQuery(sShapePath, isNodeReferenced=True):
        return False

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

def iterJunkIntermedShapes(*args, **kwargs):

    bAsPyNode = not kwargs.pop("nodeNames", True)

    for sShape in lsNodes(*args, o=True, type="shape", intermediateObjects=True, nodeNames=True, **kwargs):
        if isJunkShape(sShape, checkIntermediateAttr=False):
            yield asPyNode(sShape, bAsPyNode)

def listJunkIntermedShapes(*args, **kwargs):
    return list(iterJunkIntermedShapes(*args, **kwargs))

def iterUsedIntermedShapes(*args, **kwargs):
    bAsPyNode = not kwargs.pop("nodeNames", True)

    for sShape in lsNodes(*args, o=True, type="shape", intermediateObjects=True, nodeNames=True, **kwargs):
        print sShape
        if not isJunkShape(sShape, checkIntermediateAttr=False):
            yield asPyNode(sShape, bAsPyNode)

def listUsedIntermedShapes(*args, **kwargs):
    return list(iterUsedIntermedShapes(*args, **kwargs))

def deleteAllJunkShapes(dryRun=False):

    sJunkShapeList = listJunkIntermedShapes(nodeNames=True, not_rn=True)

    if not sJunkShapeList:
        logMsg("\nNo junk shapes found.")
        return

    sSep = "\n    delete junk shape: "
    logMsg("\nRemoving junk shapes...{}{}".format(sSep, sSep.join(sJunkShapeList)))

    if not dryRun:
        mc.delete(sJunkShapeList)

    logMsg("Removed {0} junk shapes.".format(len(sJunkShapeList)))

def unsmoothAllMeshes():

    sMeshList = lsNodes(r=True, type="mesh", not_rn=True, nodeNames=True)
    if sMeshList:
        mc.displaySmoothness(sMeshList, polygonObject=1)

def cleanLambert1():

    oLambert1 = pm.PyNode("lambert1")
    for oInputAttr in oLambert1.inputs(p=True):
        oInputAttr.disconnect()

def asPyNode(obj, bCast):
    if bCast:
        return pm.PyNode(obj) if not isinstance(obj, pm.PyNode) else obj
    else:
        return obj

