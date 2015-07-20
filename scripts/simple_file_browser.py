
import sys
#import os

from PySide import QtGui
from PySide import QtCore


if __name__ == "__main__":

    app = QtGui.QApplication(sys.argv)

    model = QtGui.QFileSystemModel()
    model.setRootPath("Z:/")

    model.setFilter(QtCore.QDir.Filters(model.filter() | QtCore.QDir.Hidden))

    tree = QtGui.QTreeView()
    tree.setModel(model)

    tree.show()

    sys.exit(app.exec_())
