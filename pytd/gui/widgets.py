
from PySide import QtGui, QtCore
from PySide.QtCore import Qt, QSize

from pytd.util.sysutils import toUnicode, isIterable
from pytd.util.fsutils import pathJoin, pathNorm
from pytd.util.fsutils import pathRelativeTo
from pytd.util.utiltypes import OrderedTree

_PATH_BAR_SS = """
QToolBar{
    spacing:0px;
}

QToolButton{
    padding-right:  -1px;
    padding-left:   -1px;
    padding-top:     1px;
    padding-bottom:  1px;
}
"""

class ImageButton(QtGui.QPushButton):

    def __init__(self, parent):
        super(ImageButton, self).__init__(parent)

    def getValue(self):
        return toUnicode(self.text())

    def clear(self):
        icon = QtGui.QIcon()
        self.setIcon(icon)


class ToolBar(QtGui.QToolBar):

    def __init__(self, parent):
        super(ToolBar, self).__init__(parent)
        self.__actDataCache = {}
        self.__clearingUp = False

    def setActionData(self, action, value):

        pyId = id(value)
        self.__actDataCache[pyId] = value

        action.setData(pyId)

    def actionData(self, action):
        pyId = action.data()
        return self.__actDataCache.get(pyId)

    def clear(self):

        self.__clearingUp = True
        try:
            QtGui.QToolBar.clear(self)
            self.__actDataCache.clear()
        finally:
            self.__clearingUp = False

class TabBar(QtGui.QTabBar):

    def __init__(self, parent):
        super(TabBar, self).__init__(parent)
        self.__tabDataCache = {}
        self.__clearingUp = False

        self.setExpanding(False)

    def sestTabData(self, idx, value):

        pyId = id(value)
        self.__tabDataCache[pyId] = value

        return QtGui.QTabBar.setTabData(self, idx, pyId)

    def tabData(self, idx):
        pyId = QtGui.QTabBar.tabData(self, idx)
        return self.__tabDataCache.get(pyId)

    def tabRemoved(self, idx):

        if not self.__clearingUp:
            pyId = QtGui.QTabBar.tabData(self, idx)
            if pyId is not None:
                self.__tabDataCache.pop(pyId)

        return QtGui.QTabBar.tabRemoved(self, idx)

    def clear(self):

        self.__clearingUp = True

        try:
            c = self.count()
            while c :
                self.removeTab(0)
                c = self.count()

            self.__tabDataCache.clear()
        finally:
            self.__clearingUp = False


class PathSwitchBox(QtGui.QComboBox):

    pathChanged = QtCore.Signal(str, bool)

    def __init__(self, *args, **kwargs):
        super(PathSwitchBox, self).__init__(*args, **kwargs)

        self.setEditable(True)
        self.setIconSize(QSize(16, 16))

        delegate = QuickTreeItemDelegate(self.view())
        delegate.setItemMarginSize(0, 4)
        self.view().setItemDelegate(delegate)

        toolBar = ToolBar(self)
        self.toolBar = toolBar

        toolBar.setFocusProxy(self)
        toolBar.setStyleSheet(_PATH_BAR_SS)
        toolBar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        toolBar.setIconSize(QSize(16, 16))
        toolBar.setLayoutDirection(Qt.RightToLeft)

        lineEdit = self.lineEdit()
        lineEdit.setVisible(False)

        lineEdit.returnPressed.connect(self.onPathEdited)
        self.activated[str].connect(self.onPathSelected)

    def setLineEditVisible(self, bShow):
        self.lineEdit().setVisible(bShow)
        self.toolBar.setVisible(not bShow)

    def onPathSelected(self, sCurText):
        if self.toolBar.isVisible():
            self.pathChanged.emit(sCurText, False)
        self.setCurrentIndex(-1)
        self.setEditText(sCurText)

    def onPathEdited(self):
        self.pathChanged.emit(self.currentText(), True)

    def resizeEvent(self, *args, **kwargs):
        res = QtGui.QComboBox.resizeEvent(self, *args, **kwargs)
        self.updateToolBarGeometry()
        return res

#    def mouseDoubleClickEvent(self, event):
#        child = self.childAt(event.pos())
#        if child and child.objectName() == "spacer":
#            self.setLineEditVisible(True)
#        return QtGui.QComboBox.mouseDoubleClickEvent(self, event)

    def updateToolBarGeometry(self):
        self.toolBar.setGeometry(self.lineEdit().geometry())


class QuickTreeItem(QtGui.QTreeWidgetItem):

    def __init__(self, *args, **kwargs):

        flags = kwargs.pop("flags", None)
        roles = kwargs.pop("roles", None)

        super(QuickTreeItem, self).__init__(*args, **kwargs)

        treeWidget = self.treeWidget()
        flags = flags if flags is not None else treeWidget.defaultFlags
        if flags is not None:
            self.setFlags(flags)

        defaultRoles = treeWidget.defaultRoles
        if roles is None:
            roles = defaultRoles.copy()
        elif defaultRoles:
            roles.update((k, v) for k, v in defaultRoles.iteritems() if k not in roles)

        if roles:
            for role, args in roles.iteritems():
                column, value = args
                if isIterable(column):
                    for c in column:
                        self.setData(c, role, value)
                else:
                    self.setData(column, role, value)

class QuickTreeItemDelegate(QtGui.QStyledItemDelegate):

    def __init__(self, parent=None):
        super(QuickTreeItemDelegate, self).__init__(parent)
        self.__itemMarginSize = None

    def setItemMarginSize(self, w, h):
        self.__itemMarginSize = QSize(w, h)

    def sizeHint(self, option, index):
        qSize = QtGui.QStyledItemDelegate.sizeHint(self, option, index)
        itemMarginSize = self.__itemMarginSize
        if itemMarginSize:
            qSize += itemMarginSize
        return qSize

class QuickTree(QtGui.QTreeWidget):

    def __init__(self, parent):
        super(QuickTree, self).__init__(parent)

        self.loadedItems = {}
        self.itemClass = QuickTreeItem
        self.defaultFlags = Qt.ItemFlags(Qt.ItemIsSelectable |
                                         Qt.ItemIsUserCheckable |
                                         Qt.ItemIsEnabled)
        self.defaultRoles = {}

        self.setItemDelegate(QuickTreeItemDelegate(self))
        self._connectSignals()

    def createTree(self, pathData, rootPath=""):

        pathItems = tuple(((pathNorm(d.pop("path")), d) for d in pathData))
        tree = OrderedTree.fromPaths(t[0] for t in pathItems)

        self.createItems(self, tree, dict(pathItems), rootPath=rootPath)
        self.resizeAllColumns()

    def createItems(self, parentItem, tree, data, parentPath="", rootPath=""):

        loadedItems = self.loadedItems
        itemCls = self.itemClass

        for current, children in tree.iteritems():

            p = pathJoin(parentPath, current)

            bBypassItem = False
            if rootPath:
                rp = pathRelativeTo(p, rootPath)
                if (rp == ".") or (".." in rp):
                    bBypassItem = True

            if bBypassItem:
                item = parentItem
            elif p in loadedItems:
                item = loadedItems[p]
            else:
                kwargs = data.get(p, {}).copy()
                texts = parentItem.columnCount() * [""]
                texts[0] = current
                texts = kwargs.pop("texts", texts)

                item = itemCls(parentItem, texts, **kwargs)

                loadedItems[p] = item

            if children:
                self.createItems(item, children, data, p, rootPath=rootPath)

    def itemFromPath(self, p):
        return self.loadedItems.get(p)

    def resizeAllColumns(self, *args):
        for c in xrange(self.columnCount()):
            self.resizeColumnToContents(c)

    def clear(self):
        self.loadedItems.clear()
        return QtGui.QTreeWidget.clear(self)

    def _connectSignals(self):
        self.itemExpanded.connect(self._onItemExpanded)
        self.itemCollapsed.connect(self._onItemCollapsed)
        self.itemClicked.connect(self._onItemClicked)

    def _onItemExpanded(self, item):
        self.resizeAllColumns()

    def _onItemCollapsed(self, item):
        self.resizeAllColumns()

    def _onItemClicked(self, item):
        return
