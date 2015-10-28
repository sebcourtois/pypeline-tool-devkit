
from PySide import QtGui
from PySide.QtCore import Qt

from pytd.util.sysutils import toUnicode, isIterable
from pytd.util.fsutils import pathJoin, pathNorm
from pytd.util.fsutils import pathRelativeTo
from pytd.util.utiltypes import OrderedTree

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


class QuickTreeItem(QtGui.QTreeWidgetItem):

    def __init__(self, *args, **kwargs):

        flags = kwargs.pop("flags", None)
        roles = kwargs.pop("roles", None)

        super(QuickTreeItem, self).__init__(*args, **kwargs)

        treeWidget = self.treeWidget()
        flags = flags if flags is not None else treeWidget.defaultFlags
        if flags is not None:
            self.setFlags(flags)

        roles = roles if roles else treeWidget.defaultRoles
        if roles:
            for role, args in roles.iteritems():
                column, value = args
                if isIterable(column):
                    for c in column:
                        self.setData(c, role, value)
                else:
                    self.setData(column, role, value)

class QuickTree(QtGui.QTreeWidget):

    def __init__(self, parent):
        super(QuickTree, self).__init__(parent)

        self.loadedItems = {}
        self.itemClass = QuickTreeItem
        self.defaultFlags = Qt.ItemFlags(Qt.ItemIsSelectable |
                                         Qt.ItemIsUserCheckable |
                                         Qt.ItemIsEnabled)
        self.defaultRoles = None

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