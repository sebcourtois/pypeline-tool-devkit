
from PySide import QtGui
from PySide.QtCore import Qt

from .utils import ItemUserRole
GroupSortRole = ItemUserRole.GroupSortRole

class BaseProxyModel(QtGui.QSortFilterProxyModel):

    def __init__(self, parent=None):
        super(BaseProxyModel, self).__init__(parent)

        self.setDynamicSortFilter(True)
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.setSortCaseSensitivity(Qt.CaseInsensitive)
        #self.setSortRole(Qt.UserRole)

    def itemFromIndex(self, prxIndex):
        return self.sourceModel().itemFromIndex(self.mapToSource(prxIndex))

    def indexFromItem(self, srcItem):
        return self.mapFromSource(self.sourceModel().indexFromItem(srcItem))

    def invisibleRootItem(self):
        return self.sourceModel().invisibleRootItem()

    def getPrptiesFromUiCategory(self, categoryKey):
        return self.sourceModel().getPrptiesFromUiCategory(categoryKey)

    def lessThan(self, leftIndex, rightIndex):

        l = leftIndex.data(GroupSortRole)
        r = rightIndex.data(GroupSortRole)

        if l != r:
            sortedOrder = self.sortOrder()
            if sortedOrder == Qt.AscendingOrder:
                return l < r
            else:
                return l > r

        return QtGui.QSortFilterProxyModel.lessThan(self, leftIndex, rightIndex)

    def setSourceModel(self, srcModel):
        srcModel._proxyModels.append(self)
        return QtGui.QSortFilterProxyModel.setSourceModel(self, srcModel)

