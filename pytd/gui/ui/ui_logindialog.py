# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Users\sebcourtois\DEVSPACE\git\z2k-pipeline-toolkit\python\pypeline-tool-devkit\resources\ui\logindialog.ui'
#
# Created: Wed Oct 21 12:31:28 2015
#      by: pyside-uic 0.2.14 running on PySide 1.2.0
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_LoginDialog(object):
    def setupUi(self, LoginDialog):
        LoginDialog.setObjectName("LoginDialog")
        LoginDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        LoginDialog.resize(200, 100)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(LoginDialog.sizePolicy().hasHeightForWidth())
        LoginDialog.setSizePolicy(sizePolicy)
        LoginDialog.setMinimumSize(QtCore.QSize(200, 100))
        LoginDialog.setMaximumSize(QtCore.QSize(200, 100))
        self.horizontalLayout = QtGui.QHBoxLayout(LoginDialog)
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setContentsMargins(6, 6, 6, 6)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.vLay = QtGui.QVBoxLayout()
        self.vLay.setSpacing(0)
        self.vLay.setObjectName("vLay")
        self.input_hLay = QtGui.QHBoxLayout()
        self.input_hLay.setSpacing(6)
        self.input_hLay.setContentsMargins(1, -1, 1, -1)
        self.input_hLay.setObjectName("input_hLay")
        self.username_lineEdit = QtGui.QLineEdit(LoginDialog)
        self.username_lineEdit.setObjectName("username_lineEdit")
        self.input_hLay.addWidget(self.username_lineEdit)
        self.password_lineEdit = QtGui.QLineEdit(LoginDialog)
        self.password_lineEdit.setEnabled(True)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.password_lineEdit.sizePolicy().hasHeightForWidth())
        self.password_lineEdit.setSizePolicy(sizePolicy)
        self.password_lineEdit.setObjectName("password_lineEdit")
        self.input_hLay.addWidget(self.password_lineEdit)
        self.vLay.addLayout(self.input_hLay)
        self.valid_hLay = QtGui.QHBoxLayout()
        self.valid_hLay.setObjectName("valid_hLay")
        self.connexion_btn = QtGui.QPushButton(LoginDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.connexion_btn.sizePolicy().hasHeightForWidth())
        self.connexion_btn.setSizePolicy(sizePolicy)
        self.connexion_btn.setObjectName("connexion_btn")
        self.valid_hLay.addWidget(self.connexion_btn)
        self.vLay.addLayout(self.valid_hLay)
        self.horizontalLayout.addLayout(self.vLay)

        self.retranslateUi(LoginDialog)
        QtCore.QObject.connect(self.username_lineEdit, QtCore.SIGNAL("returnPressed()"), self.password_lineEdit.setFocus)
        QtCore.QObject.connect(self.password_lineEdit, QtCore.SIGNAL("returnPressed()"), self.connexion_btn.click)
        QtCore.QMetaObject.connectSlotsByName(LoginDialog)

    def retranslateUi(self, LoginDialog):
        LoginDialog.setWindowTitle(QtGui.QApplication.translate("LoginDialog", "Sign-In", None, QtGui.QApplication.UnicodeUTF8))
        self.connexion_btn.setText(QtGui.QApplication.translate("LoginDialog", "Connexion", None, QtGui.QApplication.UnicodeUTF8))

