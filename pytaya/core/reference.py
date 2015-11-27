

import maya.cmds as mc
import pymel.core as pm

from pytd.util.logutils import logMsg

def listReferences(**kwargs):

    bSelected = kwargs.pop("selected", kwargs.pop("sl", False))
    bLocked = kwargs.pop("locked", None)
    bLoaded = kwargs.pop("loaded", True)
    bTopRef = kwargs.pop("topReference", kwargs.pop("top", True))

    if bSelected:
        searchList = mc.ls(sl=True , dag=True, referencedNodes=True)
        sRefNodeList = mc.ls(sl=True, type="reference")
        if sRefNodeList:
            searchList.extend(sRefNodeList)
    else:
        searchList = pm.iterReferences(recursive=not bTopRef)

    sRefNodeList = []
    oFileRefList = []

    for each in searchList:

        if bSelected:
            sRefNode = mc.referenceQuery(each, referenceNode=True, topReference=bTopRef)
        else:
            sRefNode = each.refNode.name()

        if sRefNode in sRefNodeList:
            continue
        else:
            sRefNodeList.append(sRefNode)

        if bLocked is not None:
            if (mc.getAttr(sRefNode + ".locked") != bLocked):
                continue

        if bLoaded is not None:
            if (mc.referenceQuery(sRefNode, isLoaded=True) != bLoaded):
                continue

        oFileRefList.append(pm.FileReference(sRefNode))

    return oFileRefList

def processSelectedReferences(func):

    def doIt(*args, **kwargs):

        bUnload = kwargs.pop("unloadBefore", False)
        bAllIfNoSel = kwargs.pop("allIfNoSelection", False)
        sProcessLabel = kwargs.pop("processLabel", "Process")
        bSelected = kwargs.pop("selected", kwargs.pop("sl", True))
        bConfirm = kwargs.pop("confirm", True)
#        bTestRes = kwargs.pop("testReturn", True)

        if bAllIfNoSel and bSelected:
            if not mc.ls(sl=True):
                bSelected = False

        oRefList = listReferences(sl=bSelected, **kwargs)

        if not oRefList:
            if bSelected:
                logMsg("No referenced objects selected !" , warning=True)
            else:
                logMsg("No referenced objects to {0} !!".format(sProcessLabel.lower()) , warning=True)

            return [], []

        if bSelected:
            sConfirmText = sProcessLabel + " Selected References ?"
            sRefNames = '  '.join(oRef.namespace for oRef in oRefList)
        else:
            sConfirmText = sProcessLabel + " All References ?"
            sRefNames = ""


        if bConfirm:
            sConfirmMsg = (sConfirmText + '\n\n' + sRefNames) if sRefNames else sConfirmText

            sConfirm = pm.confirmDialog(title='WARNING !'
                                        , message=sConfirmMsg
                                        , button=['OK', 'Cancel'])

            if sConfirm == 'Cancel':
                logMsg("Cancelled !" , warning=True)
                return [], []


        if bUnload:
            for oRef in oRefList:
                oRef.unload()

        try:
            resultList = []
            kwargs.update(processResults=resultList)
            for oRef in oRefList:
                func(oRef, *args, **kwargs)
        finally:
            if bUnload:
                for oRef in oRefList:
                    try:
                        oRef.load()
                    except Exception, e:
                        pm.displayError(e)

        return oRefList, resultList
    return doIt
