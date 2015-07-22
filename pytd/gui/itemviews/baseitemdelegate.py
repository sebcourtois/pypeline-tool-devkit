
from PySide import QtGui

#from PySide import QtCore
#from PySide.QtCore import Qt
#from pytd.util.qtutils import clampPixmapSize

class BaseItemDelegate(QtGui.QStyledItemDelegate):

    def __init__(self, parent=None):
        super(BaseItemDelegate, self).__init__(parent)

    def __repr__(self):

        try:
            sRepr = ('{0}( "{1}" )'.format(self.__class__.__name__, self.objectName()))
        except:
            sRepr = self.__class__.__module__ + "." + self.__class__.__name__

        return sRepr
