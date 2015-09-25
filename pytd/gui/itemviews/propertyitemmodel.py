
from PySide import QtGui
from PySide.QtCore import Qt

from pytd.util.logutils import logMsg
from pytd.util.sysutils import toUnicode, toStr
from pytd.util.strutils import labelify
from pytd.util.qtutils import setWaitCursor

from pytd.core.metaproperty import EditState as Eds

from .utils import ItemUserFlag
from .utils import ItemUserRole
from .utils import toDisplayText
from pytd.gui.dialogs import confirmDialog

class PropertyIconProvider(object):

    def __init__(self):
        pass

    def icon(self, value):
        return QtGui.QIcon(value)

    def image(self, value):
        img = QtGui.QPixmap(value)
        return img

class PropertyItem(QtGui.QStandardItem):

    def __init__(self, metaprpty=None):
        super(PropertyItem, self).__init__()

        self.childrenLoaded = False
        self._metaobj = None

        self._metaprpty = metaprpty

        if metaprpty:
            self._metaobj = metaprpty._metaobj
            self.propertyName = metaprpty.name

    def type(self):
        return QtGui.QStandardItem.UserType + 1

    def updateRow(self):
        logMsg(log='all')

        for siblItem in self.iterSiblingRow(self.row()):
            if siblItem.isValid():
                siblItem.updateData()

    def updateData(self):
        logMsg(log='all')

        metaprpty = self._metaprpty
        self.loadFlags(metaprpty)
        self.loadData(metaprpty)

    def setupData(self, metaprpty):

        msg = u"{} has not been added to a model yet !".format(self)
        assert (self.model() is not None), msg

        self._metaobj = metaprpty._metaobj

        self.loadFlags(metaprpty)
        self.loadData(metaprpty)

        if self.column() == 0:
            metaprpty.viewItems.append(self)

    def loadData(self, metaprpty):

        self.setData(toDisplayText(metaprpty.getattr_()), Qt.DisplayRole)
        self.setData(getattr(self._metaobj.__class__, "classUiPriority", 0),
                     ItemUserRole.GroupSortRole)

        if metaprpty.getParam("uiDecorated", False):
            provider = self.model().iconProvider()
            if provider:
                iconSrc = metaprpty.iconSource()
                icon = provider.icon(iconSrc)
                self.setData(icon, Qt.DecorationRole)

    def loadImage(self):

        metaprpty = self._metaprpty
        if metaprpty.getParam("uiDecorated", False):
            provider = self.model().iconProvider()
            if provider:
                image = provider.image(metaprpty.imageSource())
                if image.isNull():
                    image = self.icon()

                self.setData(image, ItemUserRole.ImageRole)

    def setData(self, value, role=Qt.EditRole):

        if role == Qt.EditRole:

            metaobj = self._metaobj
            if not metaobj:
                return

            bSuccess = False
            try:
                value = self._metaprpty.castFromUi(value)
                bSuccess = metaobj.setPrpty(self.propertyName, value, warn=False)
            except Exception, err:
                sMsg = u"Could not set {}.{}:\n\n".format(metaobj, self.propertyName)
                confirmDialog(title='SORRY !'
                            , message=sMsg + toStr(err)
                            , button=["OK"]
                            , defaultButton="OK"
                            , cancelButton="OK"
                            , dismissString="OK"
                            , icon="critical")
                raise

            if bSuccess:
                metaobj.refresh()
                self.emitDataChanged()

        else:
            return QtGui.QStandardItem.setData(self, value, role)

    def loadFlags(self, metaprpty):

        itemFlags = Qt.ItemFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

        editableState = metaprpty.getParam("uiEditable", Eds.Disabled)
        if editableState:
            # #Allow edition of the column
            itemFlags = Qt.ItemFlags(Qt.ItemIsEditable | itemFlags)

            if editableState == Eds.Multi:
                itemFlags = Qt.ItemFlags(ItemUserFlag.MultiEditable | itemFlags)

        self.setFlags(itemFlags)

    def isValid(self):
        return (self._metaprpty is not None)

    def hasChildren(self):

        if self.column() > 0:
            return False

        if self._metaobj:# and (not self.childrenLoaded):
            return self._metaobj.hasChildren()

        return QtGui.QStandardItem.hasChildren(self)

    @setWaitCursor
    def loadChildren(self):
        self._metaobj.loadChildren()

    def iterChildItems(self):

        column = self.column()

        for row in xrange(self.rowCount()):
            yield self.child(row, column)

    def iterChildRow(self, row):

        for column in xrange(self.model().columnCount()):
            yield self.child(row, column)

    def iterSiblingRow(self, row):

        parent = self.parent()
        if not parent:
            parent = self.model()

        return parent.iterChildRow(row)

    def __repr__(self):
        sClsName = self.__class__.__name__
        sRepr = ("{}('{}')".format(sClsName, toStr(self.text())))
        return sRepr

class PropertyItemModel(QtGui.QStandardItemModel):

    standardItemClass = PropertyItem
    iconProviderClass = PropertyIconProvider

    def __init__(self, metamodel, parent=None):
        super(PropertyItemModel, self).__init__(parent)

        self._metamodel = metamodel
        metamodel.setItemModel(self)

        self.__iconProvider = None

        self.loadProperties(metamodel)
        self.setupHeaderData(metamodel)
        self.populateModel(metamodel)

        # self.rowsInserted.connect(self.onRowsInserted)
        # self.rowsMoved.connect(self.onRowsMoved)
        # self.columnsInserted.connect(self.onRowsInserted)

    def onRowsInserted(self, parentIndex, start, end):

        parentItem = self.itemFromIndex(parentIndex)
        if not parentItem:
            parentItem = self.invisibleRootItem()

        print parentItem, start, end

    def onRowsMoved(self, *args):
        print args

    def loadProperties(self, metamodel):

        sPropertyList = []
        propertiesDct = {}
        uiCategoryDct = {}

        sPrimePrptyList = []

        uiClassList = metamodel.listUiClasses()

        for uiClass in uiClassList:

            if not hasattr(uiClass, "primaryProperty"):
                sClsPrimePrpty = uiClass.propertiesDctItems[0][0]
                uiClass.primaryProperty = sClsPrimePrpty
            else:
                sClsPrimePrpty = uiClass.primaryProperty

            sPrimePrptyList.append(sClsPrimePrpty)

            for sProperty, propertyDct in uiClass.propertiesDctItems:

                if sProperty in sPropertyList:
                    continue

                if not propertyDct.get("uiVisible", False):
                    continue

                sPropertyList.append(sProperty)
                propertiesDct[sProperty] = propertyDct

                sCat = propertyDct.get("uiCategory", None)
                if not sCat:
                    sCat = "ZZ_Dev"
                    propertyDct["uiCategory"] = sCat

                if sCat != "ZZ_Dev":
                    uiCategoryDct.setdefault("XX_All", []).append(sProperty)

                uiCategoryDct.setdefault(sCat, []).append(sProperty)

        assert len(set(sPrimePrptyList)) == 1, "Multiple properties defined as primary: \n\t{0}".format("\n\t".join(sPrimePrptyList))
        sPrimePrpty = sPrimePrptyList[0]

        self.uiCategoryList = sorted(uiCategoryDct.iterkeys())

        self.propertyNames = []
        for sCat in self.uiCategoryList:
            if sCat != "XX_All":
                self.propertyNames.extend(uiCategoryDct[sCat])

        if self.propertyNames.index(sPrimePrpty) != 0:
            self.propertyNames.remove(sPrimePrpty)
            self.propertyNames.insert(0, sPrimePrpty)

        uiCategoryDct["YY_AllnDev"] = uiCategoryDct["XX_All"] + uiCategoryDct["ZZ_Dev"]

        self.propertiesDct = propertiesDct
        self.uiCategoryDct = uiCategoryDct
        self.primaryProperty = sPrimePrpty

#        for k, v in uiCategoryDct.iteritems():
#            print k, v

    def getPrptiesFromUiCategory(self, categoryKey):

        if isinstance(categoryKey, basestring):
            sCategoryKey = categoryKey
        elif isinstance(categoryKey, int):
            sCategoryKey = toUnicode(self.uiCategoryList[categoryKey])

        return self.uiCategoryDct.get(sCategoryKey, ())

    def setupHeaderData(self, metamodel):

        self.setColumnCount(len(self.propertyNames))

        for c, sProperty in enumerate(self.propertyNames):

            propertyDct = self.propertiesDct[sProperty]

            sValue = propertyDct.get("uiDisplay")
            if not sValue:
                sValue = labelify(sProperty)

            self.setHeaderData(c, Qt.Horizontal, sValue, Qt.DisplayRole)

            sValue = propertyDct.get("uiToolTip", labelify(sProperty))
            self.setHeaderData(c, Qt.Horizontal, sValue, Qt.ToolTipRole)

    def populateModel(self, metamodel):

        parentItem = self.invisibleRootItem()

        for metaobj in metamodel.iterChildren():
            self.loadRowItems(metaobj, parentItem)

    def loadRowItems(self, metaobj, parentItem):

        itemCls = self.__class__.standardItemClass

        metaprpties = metaobj.iterMetaPrpties(self.propertyNames)
        rowItems = tuple(itemCls(metaprpty) for metaprpty in metaprpties)
        parentItem.appendRow(rowItems)

        for item in rowItems:
            if item.isValid():
                item.setupData(item._metaprpty)

        return rowItems

    def iterChildRow(self, row):
        for column in xrange(self.columnCount()):
            yield self.item(row, column)

    def hasChildren(self, parentIndex):

        if not parentIndex.isValid():
            return True

        if parentIndex.column() > 0:
            return False

        return self.itemFromIndex(parentIndex).hasChildren()

    def canFetchMore(self, parentIndex):

        if not parentIndex.isValid():
            return False

        if parentIndex.column() > 0:
            return False

        parentItem = self.itemFromIndex(parentIndex)
        return parentItem.hasChildren() and not parentItem.childrenLoaded

    def fetchMore(self, parentIndex):

        if not parentIndex.isValid():
            return

        parentItem = self.itemFromIndex(parentIndex)

        if parentItem.childrenLoaded:
            return

        parentItem.childrenLoaded = True
        parentItem.loadChildren()

    def setIconProvider(self, provider):
        self.__iconProvider = provider

    def iconProvider(self, *args):

        if not self.__iconProvider:
            self.__iconProvider = self.__class__.iconProviderClass(*args)

        return self.__iconProvider

    def __repr__(self):

        try:
            sRepr = ('{0}( "{1}" )'.format(self.__class__.__name__, self.objectName()))
        except:
            sRepr = self.__class__.__module__ + "." + self.__class__.__name__

        return sRepr
