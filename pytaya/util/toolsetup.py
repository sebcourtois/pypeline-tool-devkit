
import sys
import os.path as osp
import traceback
from functools import partial
import logging


from maya.api import OpenMaya as om
import pymel.core; pm = pymel.core

from pytd.util import logutils
from pytd.util import sysutils
from pytd.util.sysutils import hostApp, reloadModule, toStr
from pytd.util.logutils import logMsg


def safely(func, returns=None):
    def doIt(*args, **kwargs):
        try:
            ret = func(*args, **kwargs)
        except Exception as e:
            pm.displayError(toStr(e))
            traceback.print_exc()
            return returns
        return ret
    return doIt


def reloadUI(sUiModuleName, bRelaunchUI, **kwargs):

    sReloadCmd = "import {0}; reload({0}); "

    reloadModule(sUiModuleName)

    if bRelaunchUI:
        strKwargs = ", ".join(str(k) + "='" + str(v) + "'" for k, v in kwargs.items())
        if strKwargs:
            pm.evalDeferred((sReloadCmd + '{0}.launch({1})').format(sUiModuleName, strKwargs))
        else:
            pm.evalDeferred((sReloadCmd + '{0}.launch()').format(sUiModuleName))

def setUrllib3LoggingEnabled(bEnabled):

    logger = logging.getLogger("requests.packages.urllib3.connectionpool")
    if logger:
        logger.disabled = not bEnabled

class ToolSetup(object):

    classMenuName = "baseToolMenu"
    classMenuLabel = "Base Tools"

    def __init__(self):

        self.canDistribute = False

        self.menu = None

        self.postSceneReadJobId = None
        self.newSceneOpenedJobId = None
        self.quitMayaJobId = None
        self.sceneOpenedJobId = None
        self.preNewOrOpenedJobId = None
        self.sceneSavedJobId = None
        self.preCreateRefCheckCbkId = None
        self.mayaInitializedCbkId = None
        self.beforeNewCheckCbkId = None
        self.beforeOpenCheckCbkId = None

        self.currentSceneName = None

        logutils.logSeverity = self.getLogLevel()

    def setLogLevel(self, *args):
        logutils.logSeverity = args[0]
        pm.optionVar["TD_logLevel"] = args[0]

    def getLogLevel(self):
        return pm.optionVar.get("TD_logLevel", 0)

    def beforeReloading(self, *args):
        self.killCallbacks()
        self.killScriptJobs()

    def afterReloading(self, *args):
        sClsName = self.__class__.__name__
        sModName = self.__class__.__module__

        s = "from {0} import {1}; {1}().install()".format(sModName, sClsName)
        exec(s, {})

    def reload(self, *args):

        self.beforeReloading()

        cls = self.__class__
        sysutils.reloadModule(cls.__module__)

        self.afterReloading()

    def onMayaInitialized(self, clientData=None):
        logMsg("Maya Initialized", log="callback")
        return True

    def onPostSceneRead(self, *args):
        logMsg("Post Scene Read", log="callback")

    def onNewSceneOpened(self, *args):
        logMsg("New Scene Opened", log="callback")

    def onSceneOpened(self, *args):
        logMsg("Scene Opened", log="callback")

    def onPreFileNewOrOpened(self, *args):
        logMsg("Pre File New Or Opened", log="callback")

    def onQuitApplication(self):
        logMsg("Quit Application", log="callback")

    def onSceneSaved(self):
        logMsg("Scene Saved", log="callback")

    def onPreCreateReferenceCheck(self, mFileObj, clientData=None):
        logMsg("Before Create Reference Check", log="callback")
        return True

    def onBeforeNewCheck(self, clientData=None):
        logMsg("Before New Check", log="callback")
        self.currentSceneName = ""
        return True

    def onBeforeOpenCheck(self, mFileObj, clientData=None):
        logMsg("Before Open Check", log="callback")
        self.currentSceneName = osp.normpath(mFileObj.resolvedFullName()).replace("\\", "/")
        return True

    def startCallbacks(self):

        logMsg("Start Callbacks", log="debug")

        args = (om.MSceneMessage.kMayaInitialized, safely(self.onMayaInitialized))
        self.mayaInitializedCbkId = om.MSceneMessage.addCallback(*args)
        logMsg("MayaInitialized Callback Started.")

        args = (om.MSceneMessage.kBeforeCreateReferenceCheck, safely(self.onPreCreateReferenceCheck, returns=True))
        self.preCreateRefCheckCbkId = om.MSceneMessage.addCheckFileCallback(*args)
        logMsg("PreCreateReferenceCheck Callback Started.")

        args = (om.MSceneMessage.kBeforeNewCheck, safely(self.onBeforeNewCheck, returns=True))
        self.beforeNewCheckCbkId = om.MSceneMessage.addCheckCallback(*args)
        logMsg("BeforeNewCheck Callback Started.")

        args = (om.MSceneMessage.kBeforeOpenCheck, safely(self.onBeforeOpenCheck, returns=True))
        self.beforeOpenCheckCbkId = om.MSceneMessage.addCheckFileCallback(*args)
        logMsg("BeforeOpenCheck Callback Started.")

    def killCallbacks(self):

        if self.mayaInitializedCbkId:
            self.mayaInitializedCbkId = om.MSceneMessage.removeCallback(self.mayaInitializedCbkId)
            logMsg("MayaInitialized Callback Killed.")

        if self.preCreateRefCheckCbkId:
            self.preCreateRefCheckCbkId = om.MSceneMessage.removeCallback(self.preCreateRefCheckCbkId)
            logMsg("PreCreateReferenceCheck Callback Killed.")

        if self.beforeNewCheckCbkId:
            self.beforeNewCheckCbkId = om.MSceneMessage.removeCallback(self.beforeNewCheckCbkId)
            logMsg("BeforeNewCheck Callback Killed.")

        if self.beforeOpenCheckCbkId:
            self.beforeOpenCheckCbkId = om.MSceneMessage.removeCallback(self.beforeOpenCheckCbkId)
            logMsg("BeforeOpenCheck Callback Killed.")

    def startScriptJobs(self):

        if pm.about(batch=True):
            return

        logMsg("Start ScriptJobs", log="debug")

        self.postSceneReadJobId = pm.scriptJob(event=("PostSceneRead",
                                                      safely(self.onPostSceneRead)),
                                                      cu=True, kws=False)
        logMsg("PostSceneRead Job Started.")

        self.newSceneOpenedJobId = pm.scriptJob(event=("NewSceneOpened",
                                                       safely(self.onNewSceneOpened)),
                                                       cu=True, kws=False)
        logMsg("NewSceneOpened Job Started.")

        self.sceneOpenedJobId = pm.scriptJob(event=("SceneOpened",
                                                    safely(self.onSceneOpened)),
                                                    cu=True, kws=False)
        logMsg("SceneOpened Job Started.")

        self.preNewOrOpenedJobId = pm.scriptJob(event=("PreFileNewOrOpened",
                                                       safely(self.onPreFileNewOrOpened)),
                                                       cu=True, kws=False)
        logMsg("PreNewFileOrOpened Job Started.")

        self.quitMayaJobId = pm.scriptJob(event=("quitApplication",
                                                 safely(self.onQuitApplication)),
                                                 cu=True, kws=False)
        logMsg("QuitApplication Job Started.")

        self.sceneSavedJobId = pm.scriptJob(event=("SceneSaved",
                                                   safely(self.onSceneSaved)),
                                                   cu=True, kws=False)
        logMsg("SceneSaved Job Started.")

    def killScriptJobs(self):

        if pm.about(batch=True):
            return

        self.postSceneReadJobId = pm.scriptJob(kill=self.postSceneReadJobId, force=True)
        logMsg("PostSceneRead Job Killed.")

        self.newSceneOpenedJobId = pm.scriptJob(kill=self.newSceneOpenedJobId, force=True)
        logMsg("NewSceneOpened Job Killed.")

        self.sceneOpenedJobId = pm.scriptJob(kill=self.sceneOpenedJobId, force=True)
        logMsg("SceneOpened Job Killed.")

        self.preNewOrOpenedJobId = pm.scriptJob(kill=self.preNewOrOpenedJobId, force=True)
        logMsg("PreNewFileOrOpened Job Killed.")

        self.quitMayaJobId = pm.scriptJob(kill=self.quitMayaJobId, force=True)
        logMsg("QuitApplication Job Killed.")

        self.sceneSavedJobId = pm.scriptJob(kill=self.sceneSavedJobId, force=True)
        logMsg("SceneSaved Job Killed.")


    def beforeBuildingMenu(self):
        #logutils.logSeverity = self.getLogLevel()
        return True

    def afterBuildingMenu(self):

        self.startScriptJobs()

        sMuteModList = ["requests.packages.urllib3.connectionpool",
                        "pytd.util.external.parse",
                        "PIL.Image", ]

        for sModule in sMuteModList:

            if not sModule:
                continue

            try:
                logger = logging.getLogger(sModule)
                if logger:
                    logger.disabled = True
            except Exception as e:
                pm.displayWarning(toStr(e))

    def beginMenu(self):

        cls = self.__class__

        sMayaMainWin = pm.mel.eval('$tempMelVar=$gMainWindow')
        sMenuName = cls.classMenuName

        if pm.menu(sMenuName, q=True, exists=True):
            pm.menu (sMenuName, e=True, dai=True)
            self.menu = pm.ui.PyUI("|".join([sMayaMainWin, sMenuName]))
        else:
            self.menu = pm.menu(sMenuName, label=cls.classMenuLabel, p=sMayaMainWin, to=True)

    def populateMenu(self):
        pass

    def endMenu(self):

        with self.menu:

            if sysutils.inDevMode():

                pm.menuItem(divider=True)

                with pm.subMenuItem(label="Log Level", to=True):
                    pm.radioMenuItemCollection()

                    pm.menuItem(label='Callback',
                                radioButton=(logutils.logSeverity == -1),
                                c=partial(self.setLogLevel, -1))
                    pm.menuItem(label='Silent',
                                radioButton=(logutils.logSeverity == 0),
                                c=partial(self.setLogLevel, 0))
                    pm.menuItem(label='Info',
                                radioButton=(logutils.logSeverity == 1),
                                c=partial(self.setLogLevel, 1))
                    pm.menuItem(label='Debug',
                                radioButton=(logutils.logSeverity == 2),
                                c=partial(self.setLogLevel, 2))
                    pm.menuItem(label='All',
                                radioButton=(logutils.logSeverity == 3),
                                c=partial(self.setLogLevel, 3))


                pm.menuItem(label="Urllib3 Logging", c=setUrllib3LoggingEnabled, cb=False)

            pm.menuItem(divider=True)
            pm.menuItem(label="Reload Tools", c=self.reload)

    def buildMenu(self):

        if not self.beforeBuildingMenu():
            return

        if hostApp() == "maya":

            self.beginMenu()
            self.populateMenu()
            self.endMenu()

        self.afterBuildingMenu()

    def install(self):

        self.startCallbacks()

        self.buildMenu()

        m = sys.modules["__main__"]
        m.TOOL_SETUP = self
