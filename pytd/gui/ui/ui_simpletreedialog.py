# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Users\sebcourtois\DEVSPACE\git\z2k-pipeline-toolkit\python\pypeline-tool-devkit\resources\ui\simpletreedialog.ui'
#
# Created: Wed Oct 21 12:47:09 2015
#      by: pyside-uic 0.2.14 running on PySide 1.2.0
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui
from pytd.gui.widgets import SimpleTree

class Ui_SimpleTreeDialog(object):
    def setupUi(self, SimpleTreeDialog):
        SimpleTreeDialog.setObjectName("SimpleTreeDialog")
        SimpleTreeDialog.resize(800, 600)
        self.verticalLayout = QtGui.QVBoxLayout(SimpleTreeDialog)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(3, 3, 3, 3)
        self.verticalLayout.setObjectName("verticalLayout")
        self.treeWidget = SimpleTree(SimpleTreeDialog)
        self.treeWidget.setObjectName("treeWidget")
        self.treeWidget.headerItem().setText(0, "1")
        self.verticalLayout.addWidget(self.treeWidget)
        self.buttonBox = QtGui.QDialogButtonBox(SimpleTreeDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(SimpleTreeDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), SimpleTreeDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), SimpleTreeDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(SimpleTreeDialog)

    def retranslateUi(self, SimpleTreeDialog):
        SimpleTreeDialog.setWindowTitle(QtGui.QApplication.translate("SimpleTreeDialog", "Dialog", None, QtGui.QApplication.UnicodeUTF8))

