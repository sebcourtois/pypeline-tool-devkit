# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Users\styx\DEVSPACE\git\z2k-pipeline-toolkit\python\pypeline-tool-devkit\resources\ui\simpletreedialog.ui'
#
# Created: Sun Oct 25 18:42:34 2015
#      by: pyside-uic 0.2.14 running on PySide 1.2.0
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_QuickTreeDialog(object):
    def setupUi(self, QuickTreeDialog):
        QuickTreeDialog.setObjectName("QuickTreeDialog")
        QuickTreeDialog.resize(800, 600)
        self.verticalLayout = QtGui.QVBoxLayout(QuickTreeDialog)
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setContentsMargins(3, 3, 3, 3)
        self.verticalLayout.setObjectName("verticalLayout")
        self.treeWidget = QuickTree(QuickTreeDialog)
        self.treeWidget.setObjectName("treeWidget")
        self.treeWidget.headerItem().setText(0, "1")
        self.verticalLayout.addWidget(self.treeWidget)
        self.buttonBox = QtGui.QDialogButtonBox(QuickTreeDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(QuickTreeDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), QuickTreeDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), QuickTreeDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(QuickTreeDialog)

    def retranslateUi(self, QuickTreeDialog):
        QuickTreeDialog.setWindowTitle(QtGui.QApplication.translate("QuickTreeDialog", "Dialog", None, QtGui.QApplication.UnicodeUTF8))

from pytd.gui.widgets import QuickTree
