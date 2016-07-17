
#from PySide import QtGui
from PySide.QtGui import QIcon
from PySide.QtGui import QApplication, QStyle, QStyledItemDelegate
from PySide.QtGui import QStyleOptionViewItemV4
from PySide.QtCore import Qt, QSize
from pytd.gui.itemviews.utils import ItemUserRole
#
#from pytd.util.qtutils import clampPixmapSize


class BaseItemDelegate(QStyledItemDelegate):

    def __init__(self, parent=None):
        super(BaseItemDelegate, self).__init__(parent)

        self.decorationMargin = 10

    def paint(self, painter, option, index):

        icon = index.data(ItemUserRole.IconRole)
        if (not icon) or icon.isNull():
            return QStyledItemDelegate.paint(self, painter, option, index)

        opt = QStyleOptionViewItemV4(option)
        self.initStyleOption(opt, index)

        widget = opt.widget
        style = widget.style() if widget else QApplication.style()
        style.drawControl(QStyle.CE_ItemViewItem, opt, painter, widget)

        optState = opt.state
        mode = QIcon.Normal
        if (not (optState & QStyle.State_Enabled)):
            mode = QIcon.Disabled
        elif (optState & QStyle.State_Selected):
            mode = QIcon.Selected;
        state = QIcon.On if (optState & QStyle.State_Open) else QIcon.Off

        decorSize = opt.decorationSize
        iconSize = icon.actualSize(decorSize, mode, state)
        iconHeight = iconSize.height()
        iconWidth = iconSize.width()

        iconRect = style.subElementRect(QStyle.SE_ItemViewItemDecoration, opt, widget)

        decorHeight = decorSize.height()
        decorWidth = decorSize.width()
        wadj = hadj = 0

        if iconHeight < decorHeight:
            hadj = (decorHeight - iconHeight) * .5

        if iconWidth < decorWidth:
            wadj = (decorWidth - iconWidth) * .5

        if wadj or hadj:
            iconRect.adjust(wadj, hadj, -wadj, -hadj)

        icon.paint(painter, iconRect, opt.decorationAlignment, mode, state)

    def sizeHint(self, option, index):

        qSize = QStyledItemDelegate.sizeHint(self, option, index)

        iDecorHeight = option.decorationSize.height()
        if iDecorHeight > qSize.height():
            qSize.setHeight(iDecorHeight)

        return qSize + QSize(0, 2)

    def __repr__(self):

        try:
            sRepr = ('{0}( "{1}" )'.format(self.__class__.__name__, self.objectName()))
        except:
            sRepr = self.__class__.__module__ + "." + self.__class__.__name__

        return sRepr
