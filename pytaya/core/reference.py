
import maya.cmds as mc
import pymel.core as pm

from pytd.util.logutils import logMsg

def listReferences(**kwargs):

    bSelected = kwargs.pop("selected", kwargs.pop("sl", False))
    bLocked = kwargs.pop("locked", None)
    bLoaded = kwargs.pop("loaded", None)
    bTopRef = kwargs.pop("topReference", kwargs.pop("top", True))
    excludeFunc = kwargs.pop("exclude", None)

    if bSelected:
        searchList = mc.ls(sl=True , dag=True, referencedNodes=True)
        sRefNodeList = mc.ls(sl=True, type="reference")
        if sRefNodeList:
            searchList.extend(sRefNodeList)
    else:
        searchList = pm.iterReferences(recursive=(not bTopRef))

    sRefNodeList = []
    oFileRefList = []

    for each in searchList:

        oFileRef = None
        if bSelected:
            sRefNode = mc.referenceQuery(each, referenceNode=True, topReference=bTopRef)
        else:
            sRefNode = each.refNode.name()
            oFileRef = each

        if sRefNode in sRefNodeList:
            continue

        sRefNodeList.append(sRefNode)

        if bLocked is not None:
            if (mc.getAttr(sRefNode + ".locked") != bLocked):
                continue

        if bLoaded is not None:
            if (mc.referenceQuery(sRefNode, isLoaded=True) != bLoaded):
                continue

        if not oFileRef:
            oFileRef = pm.FileReference(sRefNode)

        if excludeFunc and excludeFunc(oFileRef):
            continue

        oFileRefList.append(oFileRef)

    return oFileRefList

def processSceneReferences(func):

    def doIt(*args, **kwargs):

        bUnload = kwargs.pop("unloadBefore", False)
        bAllIfNoSel = kwargs.pop("allIfNoSelection", False)
        sProcessLabel = kwargs.pop("processLabel", "Process")
        bSelMode = kwargs.pop("selected", kwargs.pop("sl", True))
        bConfirm = kwargs.pop("confirm", True)

        bSelected = bSelMode
        if bSelMode and bAllIfNoSel:
            if not mc.ls(sl=True):
                bSelected = False

        oFileRefList = listReferences(sl=bSelected, **kwargs)

        if not oFileRefList:
            if bSelected:
                pm.displayError("No referenced objects selected !")
            else:
                pm.displayError("No referenced objects to {} !".format(sProcessLabel.lower()))
            return [], []

        if bSelMode:
            if bSelected:
                sConfirmText = sProcessLabel + " {} Selected References ?".format(len(oFileRefList))
                sRefNames = '  '.join(oFileRef.namespace for oFileRef in oFileRefList)
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
            for oFileRef in oFileRefList:
                oFileRef.unload()

        try:
            resultList = []
            kwargs.update(processResults=resultList)
            for oFileRef in oFileRefList:
                func(oFileRef, *args, **kwargs)
        finally:
            if bUnload:
                for oFileRef in oFileRefList:
                    try:
                        oFileRef.load()
                    except Exception, e:
                        pm.displayError(e)

        return oFileRefList, resultList
    return doIt
