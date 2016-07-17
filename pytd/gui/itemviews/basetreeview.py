
import functools

from PySide import QtGui
from PySide import QtCore
from PySide.QtCore import Qt, QEvent


from .utils import ItemUserFlag
from .baseproxymodel import BaseProxyModel
from .propertyitemmodel import PropertyItemModel
from .baseitemdelegate import BaseItemDelegate
from pytd.util.sysutils import getCaller

class BaseTreeView(QtGui.QTreeView):

    itemDelegateClass = BaseItemDelegate
    proxyModelClass = BaseProxyModel
    itemModelClass = PropertyItemModel

    def __init__(self, parent=None, **kwargs):
        super(BaseTreeView, self).__init__(parent)

        self.mainCtxMenu = None
        self.shiftModifier = False
        self.noScrollTo = False
        self.mousePressEventButtons = kwargs.pop("mousePressButtons", (Qt.LeftButton, Qt.RightButton))

        self.setUniformRowHeights(True)
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)

#        self.header().setStretchLastSection( True )
        self.setAlternatingRowColors(True)
        self.setItemDelegate(self.__class__.itemDelegateClass(self))
        self.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.setTextElideMode(Qt.ElideRight)

        self.setItemHeight(16)

#        self.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
#        self.setDropIndicatorShown(True)

#        self.clicked.connect(self.onItemClicked)
#
#    def onItemClicked(self, index):
#        item = self.model().itemFromIndex(index)
#        print item
#
#        if (index.flags() & Qt.ItemIsEditable):
#            print "item editable"
#        else:
#            print "item not editable"

    def setupModelData(self, metamodel, **kwargs):

#        bModelTest = kwargs.pop("testModel", False)
        bProxyModel = kwargs.pop("useProxyModel", True)

        model = self.__class__.itemModelClass(metamodel, self)

        if bProxyModel:

            proxyModel = self.__class__.proxyModelClass()
            proxyModel.setSourceModel(model)
            self.setModel(proxyModel)

            self.sortByColumn(0, Qt.AscendingOrder)
            self.setSortingEnabled(True)

        else:
            self.setModel(model)

    def edit(self, index, *args):

        if args:
            result = QtGui.QTreeView.edit(self, index, *args)
            return result

        #print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", getCaller(fo=0), self, "edit()", index
        editor = self.indexWidget(index)
        if editor:

            column = index.column()
            editorMinWidth = editor.minimumSizeHint().width()

            colWidth = self.columnWidth(column)

            if column == 0:
                rectWidth = self.visualRect(index).width()
                iWidth = colWidth - rectWidth + editorMinWidth
            else:
                iWidth = editorMinWidth

            if iWidth > colWidth:
                self.setColumnWidth(index.column(), iWidth)

            self.updateEditorGeometries()

            if isinstance(editor, QtGui.QComboBox):
                pressEvent = QtGui.QMouseEvent(QtCore.QEvent.MouseButtonPress,
                                                QtCore.QPoint(0, 0),
                                                Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
                releaseEvent = QtGui.QMouseEvent(QtCore.QEvent.MouseButtonRelease,
                                                QtCore.QPoint(0, 0),
                                                Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)

                QtGui.QApplication.sendEvent(editor, pressEvent)
                QtGui.QApplication.sendEvent(editor, releaseEvent)

    def commitData(self, editor):
        QtGui.QTreeView.commitData(self, editor)

        curntIndex = self.currentIndex()
        iCurntColumn = curntIndex.column()
        self.resizeColumnToContents(iCurntColumn)

        #apply data of current edited index across selected indexes of the same column
        model = self.model()
        variant = model.data(curntIndex, Qt.UserRole)

        selectedIdxs = self.selectionModel().selectedIndexes()
        if selectedIdxs:
            selectedIdxs.remove(curntIndex)

            for index in selectedIdxs:

                if index.column() != iCurntColumn:
                    continue

                if index.flags() & ItemUserFlag.MultiEditable:
                    model.setData(index, variant)

    def eventFilter(self, obj, event):

        if isinstance(obj, QtGui.QMenu):
            eventType = event.type()
            if eventType in (QEvent.MouseButtonPress, QEvent.MouseButtonDblClick):
                action = obj.activeAction()
                if action and action.isCheckable():
                    action.trigger()
                    return True

        return super(BaseTreeView, self).eventFilter(obj, event)

    def mousePressEvent(self, mouseEvent):

        if mouseEvent.button() not in self.mousePressEventButtons:
            mouseEvent.ignore()
            return

        QtGui.QTreeView.mousePressEvent(self, mouseEvent)

    def mouseMoveEvent(self, mouseEvent):

        if mouseEvent.buttons() == Qt.MidButton:
            return QtGui.QTreeView.mouseMoveEvent(self, mouseEvent)

    def keyPressEvent(self, keyEvent):

        if keyEvent.key() in (Qt.Key_Left, Qt.Key_Right):
            keyEvent.ignore()
            return

        QtGui.QTreeView.keyPressEvent(self, keyEvent)

        if keyEvent.modifiers() & Qt.ShiftModifier:
            self.shiftModifier = True

    def keyReleaseEvent(self, keyEvent):
        QtGui.QTreeView.keyReleaseEvent(self, keyEvent)
        self.shiftModifier = False

    def focusInEvent(self, event):
        #print "focusInEvent", self

        selModel = self.selectionModel()
        if selModel:
            selModel.itemPressed = True

        return QtGui.QTreeView.focusInEvent(self, event)

    def contextMenuEvent(self, event):

        curIndex = self.currentIndex()
        iColumn = curIndex.column() if curIndex.isValid() else 0

        if iColumn == 0:
            if self.mainCtxMenu:
                self.mainCtxMenu.launch(event)
        else:
            model = self.model()

            qMenu = QtGui.QMenu(self)

            curItem = model.itemFromIndex(curIndex)

            if not curItem:
                return

            presetList, _ = curItem._metaprpty.getPresetValues()
            if presetList:
                presetList.sort()

                for preset in presetList:

                    if isinstance(preset, (tuple, list)):
                        text, userdata = preset
                    else:
                        text = userdata = preset

                    qAction = qMenu.addAction(text)
                    slot = functools.partial(self.applyDataToSelection, userdata)
                    qAction.triggered.connect(slot)

            qMenu.exec_(event.globalPos())

    def applyDataToSelection(self, variant):

        model = self.model()
        curntIndex = self.currentIndex()
        iCurntColumn = curntIndex.column()

        model.setData(curntIndex, variant)

        for index in self.selectionModel().selectedIndexes():

            if index.column() != iCurntColumn:
                continue

            if index.flags() & ItemUserFlag.MultiEditable:
                model.setData(index, variant)

        self.resizeColumnToContents(iCurntColumn)


    def selectIndex(self, *indexes, **kwargs):

        bReplace = kwargs.get("replace", kwargs.get("r", True))

        count = len(indexes)
        if count > 1:

            selection = QtGui.QItemSelection()

            for index in indexes:
                selIndex = self.mappedIdx(index)

                if not selIndex.isValid():
                    continue

                selection.select(selIndex, selIndex)

        elif count == 1:

            selIndex = self.mappedIdx(indexes[0])

            if not selIndex.isValid():
                return

            selection = selIndex

        else:
            selection = None

        curntSelModel = self.selectionModel()
        if not curntSelModel:
            return

        if bReplace:
            curntSelModel.clearSelection()

        if selection:

            currentIndex = self.mappedIdx(indexes[-1])

            curntSelModel.select(selection, QtGui.QItemSelectionModel.Select | QtGui.QItemSelectionModel.Rows)
            curntSelModel.setCurrentIndex(currentIndex, QtGui.QItemSelectionModel.Current)

    def selectLeaf(self, *leafList , **kwargs):

        model = self.model()

        indexes = tuple(model.indexForLeaf(leaf) for leaf in leafList if (leaf.isInTree() and (leaf != model.root)))

        self.selectIndex(*indexes, **kwargs)


    def recursiveExpand(self, index):

        model = self.model()
        item = model.itemFromIndex(index)
        self.resizeColumnToContents(0)

        if self.shiftModifier:
            for row in xrange(item.rowCount()):
                child = item.child(row, 0)
                if child.rowCount() > 0:
                    childIdx = model.indexFromItem(child)
                    self.setExpanded(childIdx, True)

    def recursiveCollapse(self, index):

        model = self.model()
        item = model.itemFromIndex(index)
        self.resizeColumnToContents(0)

        if self.shiftModifier:
            for row in xrange(item.rowCount()):
                child = item.child(row, 0)
                if child.rowCount() > 0:
                    childIdx = model.indexFromItem(child)
                    self.setExpanded(childIdx, False)

    def sizeHintForColumn(self, column):
        iSizeHint = QtGui.QTreeView.sizeHintForColumn(self, column)
        iNewSizeHint = iSizeHint + 8
        return iNewSizeHint if iNewSizeHint >= self.header().sectionSizeHint(column) else iSizeHint

    def resizeColumnsToContents(self):
        for column in range(self.model().columnCount()):
            self.resizeColumnToContents(column)

#    def selectionChanged( self, selected, deselected ):
#        self.resizeColumnToContents( 0 )
#        QtGui.QTreeView.selectionChanged( self, selected, deselected )

    def scrollTo(self, index, *args):

        if self.noScrollTo:
            return

        QtGui.QTreeView.scrollTo(self, self.mappedIdx(index) , *args)

    def mappedIdx(self, index):

        if not index.isValid():
            return index

        viewModel = self.model()

        if isinstance(viewModel, QtGui.QSortFilterProxyModel):

            indexModel = index.model()

            if indexModel == viewModel.sourceModel():
                return viewModel.mapFromSource(index)

            elif isinstance(indexModel, QtGui.QSortFilterProxyModel):

                if indexModel != viewModel:
                    srcIndex = indexModel.mapToSource(index)
                    return viewModel.mapFromSource(srcIndex)

        return index


    def isExpanded(self, index):
        return QtGui.QTreeView.isExpanded(self, self.mappedIdx(index))

    def setExpanded(self, index, bExpand):
        return QtGui.QTreeView.setExpanded(self, self.mappedIdx(index), bExpand)

    def setItemHeight(self, height):
        if height >= 16:
            self.setIconSize(QtCore.QSize(height, height))
        self.itemHeight = height

    def wasAnItemPressed(self):

        selModel = self.selectionModel()
        if selModel:
            ret = selModel.itemPressed
            selModel.itemPressed = False

            return ret

        return False

    def sourceModel(self):
        viewModel = self.model()
        if isinstance(viewModel, QtGui.QSortFilterProxyModel):
            return viewModel.sourceModel()
        else:
            return viewModel


    def __repr__(self):

        try:
            sRepr = ('{0}( "{1}" )'.format(self.__class__.__name__, self.objectName()))
        except:
            sRepr = self.__class__.__module__ + "." + self.__class__.__name__

        return sRepr
