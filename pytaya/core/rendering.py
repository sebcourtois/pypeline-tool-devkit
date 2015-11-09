

import maya.cmds
from pytaya.core.general import listForNone
from pytd.util.logutils import logMsg
mc = maya.cmds

import pymel.core
pm = pymel.core


def fileNodesFromObjects(oObjList):

    oMatList = shadersFromObjects(oObjList)

    oFileNodeList = set()

    for oMat in oMatList:

        oFileNodeList.update(oMat.listHistory(type="file"))

    return list(oFileNodeList)

def shadersFromObjects(oObjList):

    if not oObjList:
        return []

    oSGMatList = shadingGroupsFromObjects(oObjList)

    oMatList = []
    for oSGMat in oSGMatList:
        oMatList.extend(pm.ls(listForNone(mc.listConnections(oSGMat.name(),
                                                             source=True,
                                                             destination=False)),
                                type=mc.listNodeTypes('shader', ex="texture")))
    return oMatList

def shadingGroupsFromObjects(oObjList):

    oShdGrpList = set()

    for oObj in oObjList:
        oShdGrpList.update(shadingGroupsForObject(oObj))

    return list(oShdGrpList)

def shadingGroupsForObject(oObj, warn=True):

    oShdGrpList = []
    oShape = None
    if isinstance(oObj, pm.general.MeshFace):
        indiceList = oObj.indices()
        for oShdEng in oObj.listHistory(type="shadingEngine"):
            if set(indiceList).intersection(set(oShdEng.members()[0].indices())):
                oShdGrpList.append(oShdEng)

    elif isinstance(oObj, pm.general.NurbsSurfaceFace):
        oShape = oObj.node()

    elif isinstance(oObj, pm.nt.Transform):
        oShape = oObj.getShape()

    elif isinstance(oObj, (pm.nt.Mesh, pm.nt.NurbsSurface)):
        oShape = oObj

    elif warn:
        logMsg("Can't get shading groups from {}".format(repr(oObj)) , warning=True)

    if not oShdGrpList:
        if oShape:
            oShdGrpList = oShape.shadingGroups()
            if not oShdGrpList:
                oShdGrpList = oShape.connections(type="shadingEngine")

    return oShdGrpList
