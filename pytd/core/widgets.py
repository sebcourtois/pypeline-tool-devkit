
from PySide import QtGui

from pytd.util.sysutils import toUnicode

class ImageButton(QtGui.QPushButton):

    def __init__(self, parent):
        super(ImageButton, self).__init__(parent)

    def getValue(self):
        return toUnicode(self.text())

    def clear(self):
        icon = QtGui.QIcon()
        self.setIcon(icon)


class TabBar(QtGui.QTabBar):

    def __init__(self, parent):
        super(TabBar, self).__init__(parent)
        self.__tabDataCache = {}
        self.__clearingUp = False

        self.setExpanding(False)

    def setTabData(self, idx, value):

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

