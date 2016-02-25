

import maya.cmds as mc
import pymel.core as pm

from pytd.util.logutils import logMsg
from pytaya.util.sysutils import argsToPyNode

def matchTransform(obj, target, **kwargs):
    logMsg(log='all')

    bPreserveChild = kwargs.pop('preserveChild', kwargs.pop('pc', False))
    sAttr = kwargs.pop('attributeToMatch', kwargs.pop('atm', 'trs'))
    bObjSpace = kwargs.get('objectSpace', kwargs.get('os', False))

    (oObj, oTarget) = argsToPyNode(obj, target)

    oChildren = None
    if bPreserveChild:
        oChildren = oObj.getChildren(typ='transform')
        oParent = oObj.getParent()
        if oChildren:
            if oParent:
                pm.parent(oChildren, oParent)
            else:
                pm.parent(oChildren, world=True)

    sAttrList = list(sAttr)

    if sAttr == "trs":
        matchTRS(oObj, oTarget, **kwargs)
    elif sAttr == "rpvt":
        matchRotatePivot(oObj, oTarget, **kwargs)
    elif sAttr == "spvt":
        matchScalePivot(oObj, oTarget, **kwargs)
    else:
        for sAttr in sAttrList:
            if sAttr == "t":
                matchPos(oObj, oTarget, **kwargs)
            elif sAttr == "r":
                matchRot(oObj, oTarget, **kwargs)
            elif sAttr == "s":
                if bObjSpace == True:
                    matchScl(oObj, oTarget, **kwargs)
                else:
                    logMsg('scale cannot be matched in world space !!', log='all')
            else:
                logMsg("'%s' not a valid attribute to match !!" % sAttr, log='all')

    if oChildren:
        pm.parent(oChildren, oObj)

def matchPos(obj, target, **kwargs):
    logMsg(log='all')

    bPreserveChild = kwargs.get('preserveChild', kwargs.get('pc', False))
    bObjSpace = kwargs.get('objectSpace', kwargs.get('os', False))

    (oObj, oTarget) = argsToPyNode(obj, target)

    sSpace = 'world'
    if bObjSpace == True:
        sSpace = "object"

    fPosVec = mc.xform(oTarget.name(), q=True, ws=not bObjSpace, os=bObjSpace, t=True)

    oChildren = None
    if bPreserveChild:
        oChildren = oObj.getChildren(typ='transform')
        oParent = oObj.getParent()
        if oChildren:
            if oParent:
                pm.parent(oChildren, oParent)
            else:
                pm.parent(oChildren, world=True)

    mc.xform(oObj.name(), ws=not bObjSpace, os=bObjSpace, t=fPosVec)
    logMsg("'%s' translate %s to %s" % (sSpace, oObj, oTarget), log='all')

    if oChildren:
        pm.parent(oChildren, oObj)

def matchRot(obj, target, **kwargs):
    logMsg(log='all')

    bPreserveChild = kwargs.pop('preserveChild', kwargs.pop('pc', False))
    bObjSpace = kwargs.get('objectSpace', kwargs.get('os', False))

    (oObj, oTarget) = argsToPyNode(obj, target)

    sSpace = 'world'
    if bObjSpace == True:
        sSpace = "object"

    objWorldPos = mc.xform(oObj.name(), q=True, ws=True, t=True)
    objScale = mc.xform(oObj.name(), q=True, r=True, s=True)

    oChildren = None
    if bPreserveChild:
        oChildren = oObj.getChildren(typ='transform')
        oParent = oObj.getParent()
        if oChildren:
            if oParent:
                pm.parent(oChildren, oParent)
            else:
                pm.parent(oChildren, world=True)

    matchTRS(oObj, oTarget, logMsg=False, **kwargs)
    logMsg("'%s' rotate %s to %s" % (sSpace, oObj, oTarget), log='all')

    if oChildren:
        pm.parent(oChildren, oObj)

    mc.xform(oObj.name(), ws=True, t=objWorldPos)
    mc.xform(oObj.name(), s=objScale)

def matchScl(obj, target, **kwargs):
    logMsg(log='all')

    bPreserveChild = kwargs.get('preserveChild', kwargs.get('pc', False))

    (oObj, oTarget) = argsToPyNode(obj, target)

    fScaleVec = mc.xform(oTarget.name(), q=True, r=True, s=True)

    oChildren = None
    if bPreserveChild:
        oChildren = oObj.getChildren(typ='transform')
        oParent = oObj.getParent()
        if oChildren:
            if oParent:
                pm.parent(oChildren, oParent)
            else:
                pm.parent(oChildren, world=True)

    mc.xform(oObj.name(), s=fScaleVec)
    logMsg("'object' scale %s to %s" % (oObj, oTarget), log='all')

    if oChildren:
        pm.parent(oChildren, oObj)

def matchTRS(obj, target, **kwargs):
    logMsg(log='all')

    bPreserveChild = kwargs.get('preserveChild', kwargs.get('pc', False))
    bObjSpace = kwargs.get('objectSpace', kwargs.get('os', False))
    bLog = kwargs.get('logMsg', True)

    (oObj, oTarget) = argsToPyNode(obj, target)

    sSpace = 'world'
    if bObjSpace == True:
        sSpace = "object"

    targetMtx = mc.xform(oTarget.name(), q=True, ws=not bObjSpace, os=bObjSpace, m=True)

    oChildren = None
    if bPreserveChild:
        oChildren = oObj.getChildren(typ='transform')
        oParent = oObj.getParent()
        if oChildren:
            if oParent:
                pm.parent(oChildren, oParent)
            else:
                pm.parent(oChildren, world=True)

    mc.xform(oObj.name(), m=targetMtx, ws=not bObjSpace, os=bObjSpace)
    if bLog:
        logMsg("'%s' transform %s to %s" % (sSpace, oObj, oTarget), log='all')

    if oChildren:
        pm.parent(oChildren, oObj)

def matchRotatePivot(obj, target, **kwargs):
    logMsg(log='all')

    bPreserveChild = kwargs.get('preserveChild', kwargs.get('pc', False))

    (oObj, oTarget) = argsToPyNode(obj, target)

    fPosVec = mc.xform(oTarget.name(), q=True, ws=True, rp=True)

    oChildren = None
    if bPreserveChild:
        oChildren = oObj.getChildren(typ='transform')
        oParent = oObj.getParent()
        if oChildren:
            if oParent:
                pm.parent(oChildren, oParent)
            else:
                pm.parent(oChildren, world=True)

    mc.xform(oObj.name(), ws=True, t=fPosVec)
    logMsg("'world' translate %s to %s's rotate pivot" % (oObj, oTarget), log='all')

    if oChildren:
        pm.parent(oChildren, oObj)

def matchScalePivot(obj, target, **kwargs):
    logMsg(log='all')

    bPreserveChild = kwargs.get('preserveChild', kwargs.get('pc', False))

    (oObj, oTarget) = argsToPyNode(obj, target)

    fPosVec = mc.xform(oTarget.name(), q=True, ws=True, sp=True)

    oChildren = None
    if bPreserveChild:
        oChildren = oObj.getChildren(typ='transform')
        oParent = oObj.getParent()
        if oChildren:
            if oParent:
                pm.parent(oChildren, oParent)
            else:
                pm.parent(oChildren, world=True)

    mc.xform(oObj.name(), ws=True, t=fPosVec)
    logMsg("'world' translate %s to %s's scale pivot" % (oObj, oTarget), log='all')

    if oChildren:
        pm.parent(oChildren, oObj)
