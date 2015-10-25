
from PySide import QtGui

from pytd.util.sysutils import toUnicode
from pytd.util.fsutils import orderedTreeFromPaths, pathJoin, pathNorm
from pytd.util.fsutils import pathRelativeTo

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


class QuickTree(QtGui.QTreeWidget):

    itemClass = QtGui.QTreeWidgetItem

    def __init__(self, parent):
        super(QuickTree, self).__init__(parent)

        self.loadedItems = {}

    def createTree(self, pathData, rootPath=""):

        pathItems = tuple(((pathNorm(d["path"]), d) for d in pathData))
        tree = orderedTreeFromPaths(t[0] for t in pathItems)

        self.createItems(self, tree, dict(pathItems), rootPath=rootPath)

    def createItems(self, parent, tree, data, parentPath="", rootPath=""):

        loadedItems = self.loadedItems
        itemCls = self.__class__.itemClass

        for child, children in tree.iteritems():

            p = pathJoin(parentPath, child)

            bNoItem = False
            if rootPath:
                rp = pathRelativeTo(p, rootPath)
                if (rp == ".") or (".." in rp):
                    bNoItem = True

            if bNoItem:
                item = parent
            elif p in loadedItems:
                item = loadedItems[p]
            else:
                itemData = data.get(p, {})
                texts = itemData.get("texts", [child])

                item = itemCls(parent, texts)

                flags = itemData.get("flags")
                if flags is not None:
                    item.setFlags(flags)

                roles = itemData.get("roles")
                if roles:
                    for role, args in roles.iteritems():
                        column, value = args
                        item.setData(column, role, value)

                loadedItems[p] = item

            if children:
                self.createItems(item, children, data, p, rootPath=rootPath)

