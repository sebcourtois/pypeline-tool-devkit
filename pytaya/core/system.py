
import os.path as osp

import pymel.core as pm
import pymel.util as pmu
import maya.cmds as mc

from pytd.util.logutils import logMsg
from pytd.util.fsutils import pathResolve
from pytd.util.sysutils import listForNone, argToTuple, toStr

def importFile(sFilePath, **kwargs):

    if not isinstance(sFilePath, basestring):
        raise TypeError, 'Wrong type passed to file path argument: {0}'.format(type(sFilePath))

    if ("%" in sFilePath) or ("$" in sFilePath):
        sResolvedPath = pathResolve(sFilePath)
    else:
        sResolvedPath = sFilePath

    if not osp.isfile(sResolvedPath):
        raise ValueError, 'Import failed. No such file found : "{0}"'.format(sResolvedPath)

    kwargs.pop("defaultNamespace", kwargs.pop("dns", None))
    bReference = kwargs.pop("reference", kwargs.pop("r", False))
    bViewFit = kwargs.pop('viewFit', False)
    bOutNewNodes = kwargs.pop('returnNewNodes', kwargs.pop('rnn', True))
    bPreserveRefs = kwargs.pop('preserveReferences', kwargs.pop('pr', True))
    bNewScene = kwargs.pop('newScene', kwargs.pop('nsc', "NoEntry"))

    if bReference:
        bUseNamespaces = True
        bNewScene = False
    else:
        bUseNamespaces = kwargs.pop('useNamespaces', kwargs.pop('uns', False))

#    sNamespace = ""
    if bUseNamespaces:
        sNamespace = kwargs.pop("namespace", kwargs.pop("ns" , ""))
        if not sNamespace:
            sNamespace = osp.basename(sResolvedPath).rsplit(".", 1)[0]

    ##Three states kwarg:
    ##if newScene == True , importing NewScene is forced
    ##if newScene == False, importing in the CurrentScene
    ##if newScene == "NoEntry", so choose between NewScene and CurrentScene

    if bNewScene == "NoEntry":

        sConfirm = pm.confirmDialog(title="Import File"
                                    , message='Import file into ... ?'
                                    , button=["New Scene", "Current Scene", "Cancel"]
                                    , defaultButton="New Scene"
                                    , cancelButton="Cancel"
                                    , dismissString="Cancel"
                                    )

        if sConfirm == "Cancel":
            logMsg("Cancelled !" , warning=True)
            return

        bNewScene = True if sConfirm == "New Scene" else False

    if bNewScene:
        if newScene(**kwargs):
            return

    if bReference:
        oNewNodeList = pm.createReference(sFilePath
                                        , namespace=sNamespace
                                        , returnNewNodes=bOutNewNodes
                                        , **kwargs)
    else:
        if bUseNamespaces:
            kwargs["namespace"] = sNamespace

        oNewNodeList = pm.importFile(sResolvedPath
                                    , returnNewNodes=bOutNewNodes
                                    , preserveReferences=bPreserveRefs
                                    , **kwargs)

    oNewNodeList = listForNone(oNewNodeList)

    if oNewNodeList and bViewFit:
        pm.viewFit(all=True)

    return oNewNodeList

def getMayaSceneTypeFromExtension(sFilePath):

    _, sFileExt = osp.splitext(sFilePath)

    sSceneTypeExtDict = {
                    ".ma": "mayaAscii",
                    ".mb": "mayaBinary"
                    }

    sType = sSceneTypeExtDict.get(sFileExt, None)

    if not sType:
        raise RuntimeError, 'Invalid extension : "{0}"'.format(sFileExt)

    return sType

def chooseMayaScene(**kwargs):

    fileFilters = kwargs.pop("fileFilter", kwargs.pop("ff", "mayaScene"))
    sFileFilters = argToTuple(fileFilters)

    sFilterDct = {
                "mayaScene":"Maya Scenes (*.ma *.mb)",
                "mayaAscii": "Maya ASCII (*.ma)",
                "mayaBinary": "Maya Binary (*.mb)",
                }

    sFileFilters = tuple(sFilterDct.get(ff, ff) for ff in sFileFilters)
    sFileFilter = ";;".join(sFileFilters)

    sSelFilter = kwargs.pop("selectFileFilter", kwargs.pop("sff", sFileFilters[0]))

    kwargs.pop("dialogStyle", kwargs.pop("ds", 2))

    return pm.fileDialog2(fileFilter=sFileFilter,
                          dialogStyle=2,
                          selectFileFilter=sSelFilter,
                          **kwargs)

def saveScene(**kwargs):

    sCurScnPath = mc.file(q=True, sceneName=True)
    if not sCurScnPath:
        sCurScnPath = "untitled"
        sSceneName = "untitled scene"
        sSceneTypeList = ['mayaAscii', 'mayaBinary']
    else:
        sSceneName = sCurScnPath
        sExt = osp.splitext(sCurScnPath)[1].lower()

        sSceneTypeList = []
        if sExt:
            if sExt == ".ma":
                sSceneTypeList = ['mayaAscii']
            elif sExt == ".mb":
                sSceneTypeList = ['mayaBinary']

        if not sSceneTypeList:
            raise ValueError("Invalid maya scene extension: '{}'".format(sExt))
            #sSceneTypeList = mc.file(q=True, type=True)

        if len(sSceneTypeList) > 1:
            raise RuntimeError, 'Saving "{0}" : More than one type matches this file : {1}'\
                                .format(sCurScnPath, sSceneTypeList)
        else:
            sSceneType = sSceneTypeList[0]

    sWantedSceneType = kwargs.get('fileType', kwargs.get('ft', ''))

    bForce = True
    if sWantedSceneType and (sWantedSceneType != sSceneType):

        if sWantedSceneType not in ('mayaAscii', 'mayaBinary'):
            raise ValueError('Invalid file type : "{0}"'.format(sWantedSceneType))

        sSceneType = sWantedSceneType
        bForce = False

    else:
        if not mc.file(q=True, modified=True):
            logMsg('Saving "{0}" : No changes to save.'.format(sSceneName) , warning=True)
            return sCurScnPath

    bConfirm = kwargs.get("confirm", True)

    if bConfirm:

        if kwargs.get("discard", True):
            buttonList = ("Save", "Don't Save", "Cancel")
            sDismiss = "Don't Save"
            sConfirmEnd = "?"
        else:
            buttonList = ("Save", "Cancel")
            sDismiss = "Cancel"
            sConfirmEnd = "!"

        sConfirm = pm.confirmDialog(title="Warning : Save Your Current Scene"
                                    , message='Save changes to :\n\n{0} {1}'.format(sSceneName, sConfirmEnd)
                                    , button=buttonList
                                    , defaultButton="Cancel"
                                    , cancelButton="Cancel"
                                    , dismissString=sDismiss
                                    )
    else:
        sConfirm = "Save"

    if sConfirm == "Cancel":
        logMsg("Cancelled !" , warning=True)
        return ""

    elif sConfirm == "Don't Save":
        return sCurScnPath

    elif sConfirm == "Save":

        bNoFileCheck = kwargs.pop("noFileCheck", True)

        if sCurScnPath == "untitled":

            sFileList = chooseMayaScene(ff=sSceneTypeList)
            if not sFileList:
                return ""

            if bNoFileCheck:
                pmu.putEnv("DAVOS_FILE_CHECK", "")

            return pm.saveAs(sFileList[0], force=True)

        else:
            if bNoFileCheck:
                pmu.putEnv("DAVOS_FILE_CHECK", "")

            return pm.saveFile(force=bForce, type=sSceneType)

def newScene(**kwargs):

    bForce = kwargs.get("force", kwargs.get("f", False))

    if not bForce:
        sScenePath = saveScene()
    else:
        sScenePath = "newSceneForced"

    if sScenePath:
        pm.newFile(force=True)

    return sScenePath

def openScene(*args, **kwargs):

    if kwargs.pop("noFileCheck", True):
        pmu.putEnv("DAVOS_FILE_CHECK", "")

    bFail = kwargs.pop("fail", True)

    try:
        return pm.openFile(*args, **kwargs)
    except RuntimeError, e:
        if bFail:
            raise
        else:
            pm.displayError(toStr(e.message))

    return None
