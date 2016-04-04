
import os.path as osp
import re
from collections import OrderedDict
import itertools as itr

import pymel.core as pm
import pymel.util as pmu
import maya.cmds as mc

from pytd.util.logutils import logMsg
from pytd.util.fsutils import pathResolve
from pytd.util.sysutils import listForNone, argToTuple, toStr
from pytd.util.strutils import upperFirst
from pytaya.core.general import iterAttrsUsedAsFilename

try:
    pm.mel.source("exportAnimSharedOptions")
except pm.MelError as e:
    pm.displayError(toStr(e))

try:
    pm.mel.source("importAnimSharedOptions")
except pm.MelError as e:
    pm.displayError(toStr(e))

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
    bNewScene = kwargs.pop('newScene', kwargs.pop('nsc', False))

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

def assertCurrentSceneReadWithoutDataLoss(prompt=True):

    if mc.file(q=True, errorStatus=True) > 0:

        sConfirm = 'Abort'
        sMsg = "ERRORS have occurred while reading this scene \n\nthat may result in DATA LOSS !"
        if prompt:
            sConfirm = pm.confirmDialog(title='WARNING !',
                                        message=sMsg,
                                        button=['Continue', 'Abort'],
                                        defaultButton='Abort',
                                        cancelButton='Abort',
                                        dismissString='Abort',
                                        icon="warning")
        if sConfirm == 'Abort':
            raise AssertionError(sMsg.replace('\n', ''))

def saveScene(**kwargs):

    sSceneType = ""

    sCurScnPath = pm.sceneName()
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

    if sWantedSceneType and (sWantedSceneType != sSceneType):

        if sWantedSceneType not in ('mayaAscii', 'mayaBinary'):
            raise ValueError('Invalid file type: "{0}"'.format(sWantedSceneType))

        sSceneType = sWantedSceneType
    else:
        if not mc.file(q=True, modified=True):
            pm.displayWarning("Current scene has NO changes to save: '{}'.".format(sSceneName))
            return sCurScnPath

    bPrompt = kwargs.get("prompt", True)
    if bPrompt:
        if kwargs.get("discard", True):
            buttonList = ("Save", "Don't Save", "Cancel")
            sDismiss = "Don't Save"
            sConfirmEnd = "?"
        else:
            buttonList = ("Save", "Cancel")
            sDismiss = "Cancel"
            sConfirmEnd = "!"

        sMsg = 'Save changes to :\n\n{0} {1}'.format(sSceneName, sConfirmEnd)
        sConfirm = pm.confirmDialog(title="DO YOU WANT TO...",
                                    message=sMsg,
                                    button=buttonList,
                                    defaultButton="Cancel",
                                    cancelButton="Cancel",
                                    dismissString=sDismiss,
                                    icon="question",
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

        if (not sCurScnPath) or sCurScnPath == "untitled":

            sFileList = chooseMayaScene(ff=sSceneTypeList)
            if not sFileList:
                return ""

            if bNoFileCheck:
                pmu.putEnv("DAVOS_FILE_CHECK", "")

            return pm.saveAs(sFileList[0], force=True)

        else:
            if bNoFileCheck:
                pmu.putEnv("DAVOS_FILE_CHECK", "")

            if kwargs.get("checkError", True):
                try:
                    assertCurrentSceneReadWithoutDataLoss()
                except AssertionError:
                    return ""

            if sSceneType:
                return pm.saveFile(force=True, type=sSceneType)
            else:
                return pm.saveFile(force=True)

def newScene(**kwargs):

    bForce = kwargs.get("force", kwargs.get("f", False))

    if not bForce:
        sScenePath = saveScene()
    else:
        sScenePath = "newSceneForced"

    if sScenePath:
        pm.newFile(force=True)

    return sScenePath

def openScene(sScenePath, **kwargs):

    if kwargs.pop("noFileCheck", True):
        pmu.putEnv("DAVOS_FILE_CHECK", "")

    bFail = kwargs.pop("fail", True)

    try:
        return pm.openFile(sScenePath, **kwargs)
    except RuntimeError, e:
        if bFail:
            raise
        else:
            pm.displayError(toStr(e.message))

    return sScenePath

_toBool = lambda x: int(bool(int(x)))

ATOM_EXPORT_OPTS = OrderedDict((
("animExportSDK", _toBool),
("animExportConstraints", _toBool),
("animExportAnimLayers", _toBool),
("animExportStatics", _toBool),
("animExportBaked", _toBool),
("animExportPoints", _toBool),
("animExportHierarchy", {"selected":1, "below":2}),
("animExportChannels", {"all_keyable":1, "from_channel_box":2}),
("animExportTimeRange", {"all":1, "time_slider":2, "single_frame":3, "start_end":4}),
("animExportStartTime", float),
("animExportEndTime", float),
)
)

def getAtomExportOptions():

    pm.mel.setExportAnimSharedOptionVars(0)
    pm.mel.exportAnimSharedOptionsCallback()

    return OrderedDict((k, pm.optionVar[k])  for k in ATOM_EXPORT_OPTS.iterkeys())

def exportAtomFile(sFilePath, **kwargs):

#    print " before ".center(100, "-")
#    for k, v in getAtomExportOptions().iteritems():
#        print k, v

    savedOpts = getAtomExportOptions()
    try:

        pm.mel.setExportAnimSharedOptionVars(1)# reset to default options

        lowerFirst = lambda s: s[0].lower() + s[1:] if s != "SDK" else s
        sValidKwargs = tuple(lowerFirst(o.replace("animExport", ""))
                             for o in ATOM_EXPORT_OPTS.keys())

        for k, v in kwargs.iteritems():

            if k not in sValidKwargs:
                raise TypeError("Unexpected keyword argument: '{}'. \n    Are valid: {}"
                                .format(k, ", ".join(sValidKwargs)))

            sOpt = "animExport" + upperFirst(k)
            valueCast = ATOM_EXPORT_OPTS[sOpt]
            if isinstance(valueCast, dict):
                try:
                    value = valueCast[v]
                except KeyError:
                    raise ValueError("Invalid '{}' value. Got '{}', expected {}."
                                     .format(k, v, valueCast.keys()))
            else:
                value = valueCast(v)

            pm.optionVar[sOpt] = value

        sHeader = " Atom Export ".center(100, "-")
        print sHeader
        for k, v in getAtomExportOptions().iteritems():
            print k, v

        pm.mel.doExportAtom(1, [sFilePath])

        print sHeader

    finally:
        for k, v in savedOpts.iteritems():
            pm.optionVar[k] = v

#        print " after ".center(100, "-")
#        for k, v in getAtomExportOptions().iteritems():
#            print k, v

    return

_toTimeRange = lambda ts: ":".join((re.sub("0+$", "", "{:.4f}".format(t)).rstrip(".") for t in ts))

ATOM_IMPORT_KWARGS = OrderedDict((
("targetTime", {"start_end":1, "time_slider":2, "from_file":3}),
("srcTime", _toTimeRange),
("dstTime", _toTimeRange),
("option", ["insert", "scaleInsert", "replace", "scaleReplace"]),
("match", ["hierarchy", "string"]),
("selected", ["selectedOnly", "childrenToo"]),
("search", toStr),
("replace", toStr),
("prefix", toStr),
("suffix", toStr),
("mapFile", toStr),
)
)

def importAtomFile(sFilePath, **kwargs):

    if not osp.isfile(sFilePath):
        raise EnvironmentError("No such file: '{}'".format(sFilePath))

    sBaseName = osp.basename(osp.splitext(sFilePath)[0])
    sNamespace = kwargs.pop("namespace", kwargs.pop("ns", sBaseName))

    sValidKwargs = ATOM_IMPORT_KWARGS.keys()

    sOptList = []
    for k, v in kwargs.iteritems():

        if k not in sValidKwargs:
            raise TypeError("Unexpected keyword argument: '{}'. \n    Are valid: {}"
                            .format(k, ", ".join(sValidKwargs)))

        valueCast = ATOM_IMPORT_KWARGS[k]
        if isinstance(valueCast, dict):
            try:
                value = valueCast[v]
            except KeyError:
                raise ValueError("Invalid '{}' value: '{}'. Are valid: {}."
                                 .format(k, v, valueCast.keys()))
        elif isinstance(valueCast, list):
            if v in valueCast:
                value = v
            else:
                raise ValueError("Invalid '{}' value: '{}'. Are valid: {}."
                                 .format(k, v, valueCast))
        else:
            try:
                value = valueCast(v)
            except Exception as e:
                raise ValueError("Invalid '{}' value: {}. {}."
                                 .format(k, v, toStr(e)))

        sOpt = "{}={}".format(k, value)
        sOptList.append(sOpt)

    print ";".join(sOptList)

    sSelected = kwargs.get("selected", "selectedOnly")
    if sSelected == "selectedOnly":
        sXfmList = mc.ls(sl=True, tr=True)
    elif sSelected == "childrenToo":
        sXfmList = mc.ls(sl=True, dag=True, tr=True)

    def listAttr_(sNode):
        return listForNone(mc.listAttr(sNode, k=True, ud=True))

    sPreAttrSet = set()
    for sXfm in sXfmList:
        sPreAttrSet.update(sXfm + "." + attr for attr in listAttr_(sXfm))

    res = pm.importFile(sFilePath, type="atomImport",
                         renameAll=True,
                         namespace=sNamespace,
                         options=";".join(sOptList))

    sPostAttrSet = set()
    for sXfm in sXfmList:
        sPostAttrSet.update(sXfm + "." + attr for attr in listAttr_(sXfm))

    keyFunc = lambda s: s.split(".", 1)[0]
    sNewAttrList = sorted((sPostAttrSet - sPreAttrSet), key=keyFunc)
    if sNewAttrList:
        for sXfm, attrs in itr.groupby(sNewAttrList, keyFunc):

            oXfm = pm.PyNode(sXfm)
            oShape = oXfm.getShape()
            if not oShape:
                continue

            sAttrSet = set(a.split(".", 1)[1] for a in attrs)
            sAttrList = list(sAttrSet & set(pm.listAttr(oShape, k=True)))
            if not sAttrList:
                continue

            sSep = "\n    -"
            print (("transfering imported attrs from '{}' to '{}':" + sSep + "{}")
                   .format(oXfm, oShape, sSep.join(sAttrList)))
            pm.copyAttr(oXfm, oShape, attribute=sAttrList,
                        inConnections=True, keepSourceConnections=True)

            for sAttr in sAttrList:
                #print "deleting imported attr:", oXfm.name() + "." + sAttr
                oXfm.deleteAttr(sAttr)

    return res

def iterNodeAttrFiles(**kwargs):

    bResolved = kwargs.pop("resolved", True)

    for sNodeAttr in iterAttrsUsedAsFilename(**kwargs):

        try:
            p = mc.getAttr(sNodeAttr)
        except Exception as e:
            sErr = unicode(e)
            print ("{}: {}".format(sNodeAttr, sErr) if sNodeAttr not in sErr else sErr).strip()
            continue

        if p:
            yield pathResolve(p) if bResolved else p, sNodeAttr
