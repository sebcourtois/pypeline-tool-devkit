

import maya.api.OpenMaya as om

import maya.cmds as mc
import pymel.core as pm

from pytd.util.sysutils import argToTuple
from pytd.util.logutils import logMsg

from pytaya.util.sysutils import listForNone, pynodeToStr, argToStr
from pytaya.util import apiutils as api


def iterAttrsUsedAsFilename(*args, **kwargs):

    kwargs.update(nodeNames=True, ni=True,
                  not_defaultNodes=True,
                  not_references=True,)

    sNodeList = lsNodes(*args, **kwargs)

    for sNode in sNodeList:
        for sAttr in listForNone(mc.listAttr(sNode, usedAsFilename=True)):
            sAttr = sAttr.split(".", 1)[0]
            sNodeAttr = sNode + "." + sAttr
            sType = mc.getAttr(sNodeAttr, type=True)
            if sType == "string":
                yield sNodeAttr

def lsNodes(*args, **kwargs):

    bAsNodeName = kwargs.pop('nodeNames', False)

    bPrune = False
    pruneKwargs = {}
    for k in kwargs.keys():

        if k.startswith("not_"):
            v = kwargs.pop(k)
            pruneKwargs[k.split("not_", 1)[1]] = v

            if (not bPrune) and v:
                bPrune = True

    _lsCmd = pm.ls
    if (bPrune or bAsNodeName):
        _lsCmd = mc.ls
        args = tuple(pynodeToStr(arg) for arg in args)

    nodeList = listForNone(_lsCmd(*args, **kwargs))
    if not nodeList:
        return nodeList

    if bPrune:
        nodeList = pruneNodeList(nodeList, **pruneKwargs)
        if not bAsNodeName:
            return list(pm.PyNode(n) for n in nodeList)

    return nodeList

def pruneNodeList(in_nodeList, **kwargs):

    if not in_nodeList:
        return in_nodeList

    seqType = type(in_nodeList)

    nodeList = argToTuple(in_nodeList)

    _mod = mc if isinstance(nodeList[0], basestring) else pm

    for kwarg, value in kwargs.iteritems():

        if not value:
            continue

        junkNodes = set(_mod.ls(nodeList, **{kwarg:value}))
        if junkNodes:
            nodeList = tuple(n for n in nodeList if n not in junkNodes)

    return seqType(nodeList)

def getAddAttrCmd(sNodeAttr, longName=True):

    sNode, sAttr = sNodeAttr.split(".")

    node = api.getNode(sNode)
    fnNode = om.MFnDependencyNode(node)
    mAttr = om.MFnAttribute(fnNode.attribute(sAttr))
    return mAttr.getAddAttrCmd(longName)

def getObject(sName, fail=False):
    if not mc.objExists(sName):
        if fail:
            raise pm.MayaObjectError(sName)
        return None
    return sName

def copyAttrs(srcNode, destNode, *sAttrList, **kwargs):
    logMsg(log='all')

    if "values" not in kwargs:
        kwargs["values"] = True

    bDelete = kwargs.pop("delete", False)
    bCreate = kwargs.pop("create", False)

    sSrcNode = argToStr(srcNode)
    sDestNode = argToStr(destNode)

    mObj = api.getNode(sSrcNode)
    fnNode = om.MFnDependencyNode(mObj)

    sCopyAttrList = []
    for sAttr in sAttrList:
        if not getObject(sDestNode + "." + sAttr):
            if bCreate:
                mAttr = om.MFnAttribute(fnNode.attribute(sAttr))
                sAddAttrCmd = mAttr.getAddAttrCmd(False).replace(";", " {};".format(sDestNode))

                logMsg("Copy attr. '{}' from '{}' to '{}'."
                       .format(sAttr, sSrcNode, sDestNode), log="info")
                pm.mel.eval(sAddAttrCmd)
            else:
                sAttr = ""
        else:
            if bCreate:
                logMsg("Attr. '{}' already exists on '{}'.".format(sAttr, sDestNode), log="info")

        if sAttr:
            sCopyAttrList.append(sAttr)

    mc.copyAttr(sSrcNode, sDestNode, attribute=sCopyAttrList, **kwargs)
    #copyAttrState(sSrcNode, sDestNode , *sCopyAttrList)

    if bDelete:
        for sAttr in sCopyAttrList:
            mc.deleteAttr(sSrcNode + "." + sAttr)

    return sCopyAttrList

def copyAttrState(srcNode, destNode , *sAttrList):
    logMsg(log='all')

    sSrcNode = argToStr(srcNode)
    sDestNode = argToStr(destNode)

    for sAttr in sAttrList:
        sDestNodeAttr = getObject(sDestNode + "." + sAttr)
        if sDestNodeAttr:
            sSrcNodeAttr = sSrcNode + "." + sAttr
            mc.setAttr(sDestNodeAttr,
                       k=mc.getAttr(sSrcNodeAttr, k=True),
                       l=mc.getAttr(sSrcNodeAttr, l=True),
                       cb=mc.getAttr(sSrcNodeAttr, cb=True))

def iterRenderLayerOverrides(sLayerName):

    for idx in listForNone(mc.getAttr(sLayerName + ".adjustments", multiIndices=True)):

        sLyrAttr = sLayerName + ".adjustments[{}]".format(idx)
        sInAttrList = mc.listConnections(sLyrAttr + ".plug", s=True, d=False, plugs=True)
        if not sInAttrList:
            continue

        sInPlugAttr = sInAttrList[0]

        sInAttrList = mc.listConnections(sLyrAttr + ".value", s=True, d=False, plugs=True)
        if sInAttrList:
            value = sInAttrList[0]
        else:
            value = mc.getAttr(sLyrAttr + ".value")

        yield (sInPlugAttr, value)

