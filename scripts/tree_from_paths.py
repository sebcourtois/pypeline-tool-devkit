
import sys
import os.path as osp
#from collections import OrderedDict

from PySide import QtGui
#from PySide.QtGui import QTreeWidgetItem, QTreeWidgetItemIterator
from PySide.QtCore import Qt

from pytd.util.fsutils import iterPaths
from pytd.util.sysutils import qtGuiApp
from pytd.gui.dialogs import QuickTreeDialog

#srcPaths = ["A/B/C", "A/C/D", "A/C/D/E", "A/C/D/F", "A/B/D/F", "A/A/D/F", "A/C/D/G"]

app = qtGuiApp()
if not app:
    app = QtGui.QApplication(sys.argv)

dlg = QuickTreeDialog()
treeWdg = dlg.treeWidget
treeWdg.setSortingEnabled(True)
dlg.show()

def iterTreeData():

    for p in iterPaths("C:/Users/styx/Google Drive", intermediateDirs=True,
                       relative=False):
        data = {"path":p}

        if osp.isfile(p):
            roleData = {Qt.BackgroundRole:(0, QtGui.QBrush(Qt.green))}
            data["roles"] = roleData

        yield data

treeData = tuple(iterTreeData())
treeWdg.createTree(treeData, rootPath="C:/Users/styx/Google Drive")

sys.exit(app.exec_())


