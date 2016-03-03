

import maya.api.OpenMaya as om

import pymel.core as pm

def toMObject(*sNameList):

    mSelList = om.MSelectionList()
    mObjList = []

    for i, sName in enumerate(sNameList):

        try:
            mSelList.add(sName)
        except Exception, e:
            pm.warning('{0} : "{1}"'.format(e, sName))
        else:
            node = mSelList.getDependNode(i)
            mObjList.append(node)

    return mObjList

def toMDagPath(*sNameList):

    mSelList = om.MSelectionList()
    dagPathList = []

    for i, sName in enumerate(sNameList):

        try:
            mSelList.add(sName)
        except Exception, e:
            pm.warning('{0} : "{1}"'.format(e, sName))
        else:
            try:
                dagPath = mSelList.getDagPath(i)
            except RuntimeError:
                pm.warning('Object is not a DAG node : "{0}"'.format(sName))
                continue

            dagPathList.append(dagPath)

    return dagPathList

def getObject(sName):
    mObjList = toMObject(sName)
    return mObjList[0] if mObjList else None

def getDagPath(sName):
    dagPathList = toMDagPath(sName)
    return dagPathList[0] if dagPathList else None

def selected():

    mObjList = []

    mSelList = om.MGlobal.getActiveSelectionList()

    for i in range(mSelList.length()):

        node = mSelList.getDependNode(i)

        if node.hasFn(om.MFn.kDagNode):

            cmpnt = mSelList.getComponent(i)
            dagPath = mSelList.getDagPath(i)

            if not cmpnt.isNull():
                mObjList.append((dagPath, cmpnt))
            else:
                mObjList.append(node)

        else:
            mObjList.append(node)

    return mObjList

def listPlugs(mObject, sAttrName, **kwargs):

    bInputs = kwargs.get("inputs", kwargs.get("inp", False))
    bOutputs = kwargs.get("outputs", kwargs.get("out", True))

    dpNode = om.MFnDependencyNode(mObject)
    if not dpNode.hasAttribute(sAttrName):
        raise pm.MayaAttributeError, "{0}.{1}".format(dpNode.name(), sAttrName)

    mPlug = dpNode.findPlug(sAttrName)

    out_plugArray = om.MPlugArray()
    mPlug.connectedTo(out_plugArray, bInputs, bOutputs)

    return out_plugArray

def listOutputs(mObject, sAttrName, **kwargs):
    return listPlugs(mObject, sAttrName, inputs=False, outputs=True)

def listInputs(mObject, sAttrName, **kwargs):

    return listPlugs(mObject, sAttrName, inputs=True, outputs=False)
