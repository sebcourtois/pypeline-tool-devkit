
from PySide import QtGui
from PySide import QtCore
from PySide.QtCore import Qt

from .propertyitemmodel import PropertyItemModel
from .baseproxymodel import BaseProxyModel
from .basecontextmenu import BaseContextMenu
from .basetreeview import BaseTreeView
from .baseselectionmodel import BaseSelectionModel

class BaseTreeWidget(QtGui.QWidget):

    treeViewClass = BaseTreeView
    itemModelClass = PropertyItemModel
    selectModelClass = BaseSelectionModel
    proxyModelClass = BaseProxyModel
    contextMenuClass = BaseContextMenu

    def __init__(self, parent=None , **kwargs):
        super(BaseTreeWidget, self).__init__(parent)

        self.horizontalLayout = QtGui.QHBoxLayout(self)
        self.horizontalLayout.setSpacing(2)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")

        splitter = QtGui.QSplitter(self)
        splitter.setOrientation(QtCore.Qt.Horizontal)
        splitter.setHandleWidth(3)
        splitter.setObjectName("splitter")
        splitter.setChildrenCollapsible(True)

        treeView = self.__class__.treeViewClass(splitter)
        treeView.setObjectName("treeView")
        treeView.header().setStretchLastSection(True)

        dataView = self.__class__.treeViewClass(splitter)
        dataView.setObjectName("dataView")
        dataView.header().setStretchLastSection(False)
        dataView.noScrollTo = True

        self.horizontalLayout.addWidget(splitter)

        treeView.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        treeView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        dataView.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        dataView.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        dataView.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        treeView.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)

        treeVSB = treeView.verticalScrollBar()
        dataVSB = dataView.verticalScrollBar()

        treeVSB.valueChanged.connect(dataVSB.setValue)
        dataVSB.valueChanged.connect(treeVSB.setValue)

        treeView.collapsed.connect(dataView.collapse)
        treeView.expanded.connect(dataView.expand)

        treeView.collapsed.connect(treeView.recursiveCollapse)
        treeView.expanded.connect(treeView.recursiveExpand)

#        treeView.setStyleSheet(viewStyleSheet + branchStyleSheet + itemStyleSheet)
#        dataView.setStyleSheet(viewStyleSheet + itemStyleSheet)

        self.tableHScrollBar = dataView.horizontalScrollBar()

        #should be done once all widget in splitter was created
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        self.splitter = splitter
        self.treeView = treeView
        self.dataView = dataView

    def setupModelData(self, metamodel, **kwargs):

        bProxyModel = kwargs.pop("useProxyModel", True)

        model = self.__class__.itemModelClass(metamodel, self)

        if bProxyModel:

            proxyModel = self.__class__.proxyModelClass()
            proxyModel.setSourceModel(model)
            self.setModel(proxyModel)

            self.treeView.sortByColumn(0, Qt.AscendingOrder)
            self.treeView.setSortingEnabled(True)

        else:
            self.setModel(model)

        self.dataView.mainCtxMenu = self.__class__.contextMenuClass(self.dataView)
        if self.treeView:
            self.treeView.mainCtxMenu = self.__class__.contextMenuClass(self.treeView)
#            self.connect(self.dataView.model(), SIGNAL("leafAdded(QModelIndex)"), self.treeView.expand)
#        else:
#            self.connect(self.dataView.model(), SIGNAL("leafAdded(QModelIndex)"), self.dataView.expand)

        return

    def setModel(self, model):

        self.dataView.setModel(model)
        self.dataView.setSelectionModel(self.__class__.selectModelClass(model))

        self.dataView.setColumnHidden(0, True)

        if self.treeView:

            self.treeView.setModel(model)
            self.treeView.setSelectionModel(self.dataView.selectionModel())

            for i in range(1, self.dataView.model().columnCount()):
                self.treeView.setColumnHidden(i, True)

            #self.dataView.header().setResizeMode(0, QtGui.QHeaderView.Fixed)
            #self.treeView.header().setResizeMode(0, QtGui.QHeaderView.Fixed)

    def model(self):
        return self.treeView.model()

    def selectionModel(self):
        return self.treeView.selectionModel()

    def getSelectedLeaves(self):
        return self.selectionModel().selectedLeaves

    def refresh(self):
        self.treeView.model().refresh()

    def wasAnItemPressed(self):

        ret = self.treeView.wasAnItemPressed()
#        print self, "wasAnItemPressed", ret
        return ret

    def updateTableHScrollRange(self, iMin , iMax):
        self.tableHScrollBar.setMinimum(self.dataView.columnWidth(0))


    def keyPressEvent(self, keyEvent):
        self.dataView.keyPressEvent(keyEvent)
        if self.treeView:
            self.treeView.keyPressEvent(keyEvent)

    def keyReleaseEvent(self, keyEvent):
        self.dataView.keyReleaseEvent(keyEvent)
        if self.treeView:
            self.treeView.keyReleaseEvent(keyEvent)


    def expandAll(self):
        self.dataView.expandAll()
        if self.treeView:
            self.treeView.expandAll()

    def resizeColumnsToContents(self):
        self.dataView.resizeColumnsToContents()
        if self.treeView:
            self.treeView.resizeColumnsToContents()


    def setUiCategory(self, categoryKey):

        model = self.model()
        if isinstance(model, QtGui.QSortFilterProxyModel):
            model = model.sourceModel()

        sPropertyToDisplayList = model.getPrptiesFromUiCategory(categoryKey)

        dataView = self.dataView
        treeView = self.treeView

        for i, sProperty in enumerate(model.propertyNames):

            dataView.setColumnHidden(i, sProperty not in sPropertyToDisplayList)

            if i == 0 and treeView:
                treeView.resizeColumnToContents(i)
            else:
                dataView.resizeColumnToContents(i)

    def parentSelected(self):

        model = self.dataView.model()

        selectedLeaves = self.dataView.selectionModel().selectedLeaves[:]
        if model and selectedLeaves:
            model.moveLeaves(selectedLeaves[:-1], selectedLeaves[-1])

    def unparentSelected(self):

        model = self.dataView.model()

        selectedLeaves = self.dataView.selectionModel().selectedLeaves[:]
        if model and selectedLeaves:

            for leaf in selectedLeaves:

                parentLeaf = leaf.parent
                if parentLeaf:
                    grdParentLeaf = parentLeaf.parent
                    if grdParentLeaf:
                        model.moveLeaves([leaf], grdParentLeaf)


    def __repr__(self):

        try:
            sRepr = ('{0}( "{1}" )'.format(self.__class__.__name__, self.objectName()))
        except:
            sRepr = self.__class__.__module__ + "." + self.__class__.__name__

        return sRepr
