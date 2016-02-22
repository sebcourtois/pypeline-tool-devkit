
import functools
import inspect as insp

from PySide import QtGui
SelectionBehavior = QtGui.QAbstractItemView.SelectionBehavior

from pytd.gui.itemviews.utils import createAction
from pytd.gui.dialogs import confirmDialog

from pytd.util.sysutils import toStr, inDevMode, hostApp
from pytd.util.logutils import logMsg

class BaseContextMenu(QtGui.QMenu):

    def __init__(self, parentView):
        super(BaseContextMenu, self).__init__(parentView)

        self.view = parentView
        self.actionTargets = []
        self.actionTargetsLoaded = False

        self.createActions()
        self.buildSubmenus()

        self.installEventFilter(parentView)

    def model(self):

        model = self.view.model()
        if isinstance(model, QtGui.QSortFilterProxyModel):
            return model.sourceModel()

        return model

    def getActionTargets(self):

        view = self.view
        model = view.model()
        selectModel = view.selectionModel()

        selBhv = view.selectionBehavior()
        if selBhv == SelectionBehavior.SelectRows:
            selIndexes = selectModel.selectedRows(0)
        elif selBhv == SelectionBehavior.SelectColumns:
            selIndexes = selectModel.selectedColumns(0)
        else:
            selIndexes = selectModel.selectedIndexes()

        if len(selIndexes) > 1:

            curIndex = selectModel.currentIndex()

            if selBhv == SelectionBehavior.SelectRows:
                curIndex = curIndex.sibling(curIndex.row(), 0)
            elif selBhv == SelectionBehavior.SelectColumns:
                curIndex = curIndex.sibling(0, curIndex.column())

            if curIndex.isValid() and curIndex != selIndexes[-1]:

                try: selIndexes.remove(curIndex)
                except ValueError: pass

                selIndexes.append(curIndex)

        itemFromIndex = model.itemFromIndex
        return [itemFromIndex(idx) for idx in selIndexes]

    def loadActionTargets(self):

        self.actionTargets = self.getActionTargets()
        self.actionTargetsLoaded = True

    def assertActionTargets(self):

        if not self.actionTargetsLoaded:
            raise RuntimeError("Action Selection not loaded.")
        else:
            self.actionTargetsLoaded = False

    def launchAction(self, actionDct, checked):

        bCheckable = actionDct.get("checkable", False)

        if not bCheckable:
            self.assertActionTargets()

        if not bCheckable:
            sActionMsg = u"Action: {} > {}".format(actionDct["menu"], actionDct["label"])
            try:
                logMsg(u'# Action: {} #'.format(sActionMsg))
            except Exception, e:
                logMsg(e, warning=True)

        args = actionDct.get("args", []) + self.actionTargets
        kwargs = actionDct.get("kwargs", {})
        if bCheckable:
            kwargs.update(checked=checked)
        func = actionDct["fnc"]

        try:
            return func(*args, **kwargs)
        except Exception, err:
            sMsg = u"{}\n\n".format(sActionMsg)
            confirmDialog(title='SORRY !'
                        , message=toStr(sMsg) + toStr(err)
                        , button=["OK"]
                        , defaultButton="OK"
                        , cancelButton="OK"
                        , dismissString="OK"
                        , icon="critical")
            raise

    def getActionsConfig(self):
        return []

    def createActions(self):

        self.createdActions = []
        self.createdActionConfigs = []

        for actionDct in self.getActionsConfig():
            sAction = actionDct["label"]
            sMenu = actionDct.get("menu", "Main")

            if actionDct.get("dev", False):
                if not inDevMode():
                    continue

            if sAction == "separator":
                qAction = None
            else:
                bCheckable = actionDct.get("checkable", False)
                actionSlot = functools.partial(self.launchAction, actionDct)
                qAction = createAction(sAction, self, slot=actionSlot,
                                       checkable=bCheckable)

                self.createdActions.append(qAction)

            actionDct["action"] = qAction
            actionDct["menu"] = sMenu

            self.createdActionConfigs.append(actionDct)

    def buildSubmenus(self):

        qMenuDct = { "Main": self }
        for actionDct in self.createdActionConfigs:

            sMenu = actionDct["menu"]
            qAction = actionDct["action"]

            qMenu = qMenuDct.get(sMenu, None)
            if qMenu is None:
                qMenu = self.addMenu(sMenu)
                qMenuDct[sMenu] = qMenu

            if qAction is None:
                qMenu.addSeparator()
            else:
                qMenu.addAction(qAction)

        del qMenuDct["Main"]
        return qMenuDct

    def iterAllowedActions(self, prptyItem):

        cls = prptyItem._metaobj.__class__
        sMroList = tuple(c.__name__ for c in insp.getmro(cls))
        sCurApp = hostApp()

        for actionDct in self.createdActionConfigs:

            qAction = actionDct["action"]
            if qAction is None:
                continue

            sAppList = actionDct.get("apps")
            if sAppList and (sCurApp not in sAppList):
                continue

            fnc = actionDct["fnc"]
            allowedTypes = getattr(fnc, "auth_types", None)
            if not allowedTypes:
                yield qAction
            else:
                for sTypeName in sMroList:
                    if sTypeName in allowedTypes:
                        yield qAction
                        break

    def updateVisibilities(self):

        if not self.actionTargets:
            return

        allowedActions = set(self.createdActions)
        for prptyItem in self.actionTargets:
            allowedActions.intersection_update(self.iterAllowedActions(prptyItem))

        if not allowedActions:
            return

        for qAction in self.createdActions:
            qAction.setVisible((qAction in allowedActions))

        for qMenu in self.findChildren(QtGui.QMenu):
            qMenu.menuAction().setVisible(not qMenu.isEmpty())

    def updateActionsState(self):

        for actionDct in self.createdActionConfigs:

            updFnc = actionDct.get("upd")
            if not updFnc:
                continue

            action = actionDct["action"]
            if not action.isVisible():
                continue

            updFnc(action, *self.actionTargets)

    def launch(self, event):

        self.loadActionTargets()
        self.updateVisibilities()
        self.updateActionsState()
        self.exec_(event.globalPos())

    def refreshItems(self, *itemList, **kwargs):

        sRefreshFunc = "update"
        if self.view.selectionBehavior() == SelectionBehavior.SelectRows:
            sRefreshFunc = "updateRow"

        for item in itemList:
            getattr(item, sRefreshFunc)()

