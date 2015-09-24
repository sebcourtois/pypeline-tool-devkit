
from functools import partial

import pymel.util
pmu = pymel.util

import pymel.core
pm = pymel.core

import maya.cmds
mc = maya.cmds

from pytd.util.logutils import logMsg
from pytd.util import logutils
from pytd.util import sysutils

#-------------------------------------------------------------------------------
#    Decorators
#-------------------------------------------------------------------------------

def catchJobException(func):

    def doIt(*args, **kwargs):

        try:
            ret = func(*args, **kwargs)
        except Exception, e:
            pm.displayError('< {0}.{1} > {2}.'.format(func.__module__, func.__name__, str(e)))
            return

        return ret

    return doIt

''
#-------------------------------------------------------------------------------
#    Core
#-------------------------------------------------------------------------------

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

    def setLogLevel(self, *args):

        logutils.logSeverity = args[0]
        pm.optionVar["TD_logLevel"] = args[0]

    def getLogLevel(self):
        return pm.optionVar.get("TD_logLevel", 0)

    def beforeReloading(self, *args):
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

    def onPostSceneRead(self, *args):
        logMsg("Post Scene Read", log="debug")

    def onNewSceneOpened(self, *args):
        logMsg("New Scene Opened", log="debug")

    def onSceneOpened(self, *args):
        logMsg("Scene Opened", log="debug")

    def onPreFileNewOrOpened(self, *args):
        logMsg("Pre File New Or Opened", log="debug")

    def onQuitApplication(self):
        logMsg("Quit Application", log="debug")

    def onSceneSaved(self):
        logMsg("Scene Saved", log="debug")

    def startScriptJobs(self):
        logMsg("Launch Start ScriptJobs", log="debug")

        self.postSceneReadJobId = pm.scriptJob(event=("PostSceneRead",
                                                      catchJobException(self.onPostSceneRead)),
                                                      cu=True, kws=False)
        logMsg("PostSceneRead Job Started.")

        self.newSceneOpenedJobId = pm.scriptJob(event=("NewSceneOpened",
                                                       catchJobException(self.onNewSceneOpened)),
                                                       cu=True, kws=False)
        logMsg("NewSceneOpened Job Started.")

        self.sceneOpenedJobId = pm.scriptJob(event=("SceneOpened",
                                                    catchJobException(self.onSceneOpened)),
                                                    cu=True, kws=False)
        logMsg("SceneOpened Job Started.")

        self.preNewOrOpenedJobId = pm.scriptJob(event=("PreFileNewOrOpened",
                                                       catchJobException(self.onPreFileNewOrOpened)),
                                                       cu=True, kws=False)
        logMsg("PreNewFileOrOpened Job Started.")

        self.quitMayaJobId = pm.scriptJob(event=("quitApplication",
                                                 catchJobException(self.onQuitApplication)),
                                                 cu=True, kws=False)
        logMsg("QuitApplication Job Started.")

        self.sceneSavedJobId = pm.scriptJob(event=("SceneSaved",
                                                   catchJobException(self.onSceneSaved)),
                                                   cu=True, kws=False)
        logMsg("SceneSaved Job Started.")

        #pm.scriptJob( event = ( "DagObjectCreated", fncUtil.fillTypeLists ), runOnce = True )

    def killScriptJobs(self):

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

        logutils.logSeverity = self.getLogLevel()
        return True

    def afterBuildingMenu(self):

        pmu.putEnv("TD_FILE_CHECK", "1")
        self.startScriptJobs()

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

            #if isGitDisabled():
                pm.menuItem(divider=True)
                pm.menuItem(label="Reload Tools", c=self.reload)

    def buildMenu(self):

#        if sysutils.MAYAPY_STANDALONE:
#            return

        if not self.beforeBuildingMenu():
            return

        self.beginMenu()
        self.populateMenu()
        self.endMenu()

        self.afterBuildingMenu()

    def install(self):

        self.buildMenu()
