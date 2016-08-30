
import sys
#import os

from PySide import QtGui
#from PySide import QtCore
from PySide.QtCore import QDir


if __name__ == "__main__":

    app = QtGui.QApplication(sys.argv)

    model = QtGui.QFileSystemModel()
    sRootPath = u"C:/users/sebcourtois"
    model.setRootPath(sRootPath)


    model.setFilter(QDir.Filters(QDir.NoDotAndDotDot | QDir.Dirs | QDir.Files))
    model.setNameFilters(["*_pkg"])

    tree = QtGui.QTreeView()
    tree.setModel(model)
    tree.setRootIndex(model.index(sRootPath))
    tree.setSortingEnabled(True)

    tree.show()

    sys.exit(app.exec_())
