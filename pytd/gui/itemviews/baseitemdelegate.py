
from PySide import QtGui
#from PySide import QtCore
#from PySide.QtCore import QSize
#
#from pytd.util.qtutils import clampPixmapSize


class BaseItemDelegate(QtGui.QStyledItemDelegate):

    def __init__(self, parent=None):
        super(BaseItemDelegate, self).__init__(parent)

        self.decorationMargin = 10

    def sizeHint(self, option, index):

        qSize = QtGui.QStyledItemDelegate.sizeHint(self, option, index)

        iDecorHeight = option.decorationSize.height()
        if iDecorHeight > qSize.height():
            qSize.setHeight(iDecorHeight)

        return qSize

#    def initStyleOption(self, option, index):
#
#        rowHeight = option.decorationSize.height()
#        print option.decorationSize
#
#        QtGui.QStyledItemDelegate.initStyleOption(self, option, index)
#        option = QtGui.QStyleOptionViewItemV4(option)
#
#        if not option.icon.isNull():
##            pixmap = option.icon.pixmap(option.decorationSize)
##            option.icon = QtGui.QIcon(clampPixmapSize(pixmap, rowHeight - self.decorationMargin))
#            option.decorationSize = QSize(rowHeight, rowHeight)

    def __repr__(self):

        try:
            sRepr = ('{0}( "{1}" )'.format(self.__class__.__name__, self.objectName()))
        except:
            sRepr = self.__class__.__module__ + "." + self.__class__.__name__

        return sRepr
