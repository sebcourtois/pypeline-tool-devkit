
import os.path as osp

import pymel.core as pm
import pymel.util as pmu
import maya.cmds as mc

from pytd.util.logutils import logMsg
from pytd.util.fsutils import pathResolve
from pytd.util.sysutils import listForNone

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
    bReference = kwargs.pop("reference", kwargs.pop("r", None))
    bViewFit = kwargs.pop('viewFit', False)
    bOutNewNodes = kwargs.pop('returnNewNodes', kwargs.pop('rnn', True))
    bPreserveRefs = kwargs.pop('preserveReferences', kwargs.pop('pr', True))

    if bReference:
        bUseNamespaces = True
    else:
        bUseNamespaces = kwargs.pop('useNamespaces', kwargs.pop('uns', False))

#    sNamespace = ""
    if bUseNamespaces:
        sNamespace = kwargs.pop("namespace", kwargs.pop("ns" , ""))
        if not sNamespace:
            sNamespace = osp.basename(sResolvedPath).rsplit(".", 1)[0]

    ##Three states kwarg:
    ##if newFile == True , importing NewScene is forced
    ##if newFile == False, importing in the CurrentScene
    ##if newFile == "NoEntry", so choose between NewScene and CurrentScene

    bNewFile = kwargs.pop('newFile', kwargs.pop('nf', "NoEntry"))

    if bNewFile == "NoEntry":

        sConfirm = pm.confirmDialog(title="Import File"
                                    , message='Import file into ... ?'
                                    , button=["New Scene", "Current Scene", "Cancel"]
                                    , defaultButton="New Scene"
                                    , cancelButton="Cancel"
                                    , dismissString="Cancel"
                                    )

        if sConfirm == "Cancel":
            logMsg("Cancelled !" , warning=True)
            return '_cancelled_'

        bNewFile = True if sConfirm == "New Scene" else False

    if bNewFile:
        if newFile(**kwargs) == '_cancelled_':
            return '_cancelled_'

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

def getMayaFileTypeFromExtension(sFilePath):

    _, sFileExt = osp.splitext(sFilePath)

    sFileTypeExtDict = {
                    ".ma": "mayaAscii",
                    ".mb": "mayaBinary"
                    }

    sType = sFileTypeExtDict.get(sFileExt, None)

    if not sType:
        raise RuntimeError, 'Invalid extension : "{0}"'.format(sFileExt)

    return sType

def chooseMayaFile(**kwargs):

    sInputType = kwargs.pop("type", kwargs.pop("typ", ""))

    sInputTypeDct = {
                    "mayaAscii": "Maya ASCII (*.ma)",
                    "mayaBinary": "Maya Binary (*.mb)"
                    }

    sFileFilter = sInputTypeDct.get(sInputType, "Maya Binary (*.mb);;Maya ASCII (*.ma)")

    kwargs.pop("fileFilter", None)
    kwargs.pop("dialogStyle", None)

    bSelFilter = kwargs.get("selectFileFilter", "Maya ASCII (*.ma)") if not sInputType else None

    return pm.fileDialog2(fileFilter=sFileFilter, dialogStyle=2, selectFileFilter=bSelFilter, **kwargs)

def saveFile(**kwargs):

    sFileType = mc.file(q=True, type=True)

    sCurntScenePath = mc.file(q=True, sceneName=True)
    if not sCurntScenePath:
        sCurntScenePath = "untitled scene"

    if len(sFileType) > 1:
        raise RuntimeError, 'Saving "{0}" : More than one type matches this file : {1}'\
                            .format(sCurntScenePath, sFileType)
    else:
        sFileType = sFileType[0]

    sWantedFileType = kwargs.get('type', kwargs.get('typ', ''))

    bForce = True

    if sWantedFileType and (sWantedFileType != sFileType):

        if sWantedFileType not in ('mayaAscii', 'mayaBinary'):
            raise ValueError, 'Invalid file type : "{0}"'.format(sWantedFileType)

        sFileType = sWantedFileType
        bForce = False

    else:
        if not mc.file(q=True, modified=True):
            logMsg('Saving "{0}" : No changes to save.'.format(sCurntScenePath) , warning=True)
            return sCurntScenePath

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
                                    , message='Save changes to :\n\n{0} {1}'.format(sCurntScenePath, sConfirmEnd)
                                    , button=buttonList
                                    , defaultButton="OK"
                                    , cancelButton="Cancel"
                                    , dismissString=sDismiss
                                    )
    else:
        sConfirm = "Save"

    if sConfirm == "Cancel":
        logMsg("Cancelled !" , warning=True)
        return "_cancelled_"

    elif sConfirm == "Don't Save":
        return sCurntScenePath

    elif sConfirm == "Save":

        bNoFileCheck = kwargs.pop("noFileCheck", True)

        if sCurntScenePath == "untitled scene":

            sFileList = chooseMayaFile(type=sWantedFileType)
            if not sFileList:
                return "_cancelled_"

            if bNoFileCheck:
                pmu.putEnv("DAM_FILE_CHECK", "")

            return pm.saveAs(sFileList[0], force=True)

        else:

            if bNoFileCheck:
                pmu.putEnv("DAM_FILE_CHECK", "")

            return pm.saveFile(force=bForce, type=sFileType)

def newFile(**kwargs):

    bForce = kwargs.get("force", kwargs.get("f", False))

    if not bForce:
        sSavedFile = saveFile()
    else:
        sSavedFile = "newFileForced"

    if sSavedFile != '_cancelled_':
        pm.newFile(force=True)

    return sSavedFile

def openFile(*args, **kwargs):

    if kwargs.pop("noFileCheck", True):
        pmu.putEnv("DAM_FILE_CHECK", "")

    return pm.openFile(*args, **kwargs)
