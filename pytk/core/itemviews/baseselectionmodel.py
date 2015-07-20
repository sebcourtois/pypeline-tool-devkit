
from PySide import QtGui

#from pytk.util.logutils import logMsg
from pytk.util.sysutils import getCaller

class BaseSelectionModel(QtGui.QItemSelectionModel):

    def __init__(self, model, parent=None):
        super(BaseSelectionModel, self).__init__(model, parent)

#        self.selectedItems = []
        self.itemPressed = False

        self.selectionChanged.connect(self.onSelectionChanged)

    def onSelectionChanged(self, selected, deselected):

        caller = getCaller()

        #print "onSelectionChanged", caller

        if (caller is None) or (caller == "mousePressEvent"):
            self.itemPressed = True

#        self.updateSelection(selected, deselected)


#    def clearSelection(self):
#        logMsg(log='all')
#
#        QtGui.QItemSelectionModel.clearSelection(self)
#        self.selectedItems = []

#    def clear(self, *args, **kwargs):
#
#        QtGui.QItemSelectionModel.clear(self)
#        self.selectedItems = []

#    def updateSelection(self, selected, deselected):
#        logMsg(log='all')
#
#        curntModel = self.model()
#
#        selectedItems = []
#        deselectedItems = []
#
#        for index in deselected.indexes():
#
#            if index.column() > 0:
#                continue
#
#            item = curntModel.itemFromIndex(index)
#
#            print type(self.selectedItems)
#            try:
#                self.selectedItems.remove(item)
#            except ValueError, msg:
#                logMsg("{0} : {1} not in selectedItems".format(msg, item) , warning=True)
#            else:
#                deselectedItems.append(item)
#
#        for index in selected.indexes():
#
#            if index.column() > 0:
#                continue
#
#            item = curntModel.itemFromIndex(index)
#
#            self.selectedItems.append(item)
#            selectedItems.append(item)
#
#        return selectedItems, deselectedItems



    def __repr__(self):

        try:
            sRepr = ('{0}( "{1}" )'.format(self.__class__.__name__, self.objectName()))
        except:
            sRepr = self.__class__.__module__ + "." + self.__class__.__name__

        return sRepr