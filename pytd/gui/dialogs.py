

from PySide import QtGui
from PySide.QtCore import Signal, Qt

from pytd.util.sysutils import toUnicode, toStr, inDevMode, qtGuiApp
from pytd.util.logutils import confirmMessage

from .ui.ui_logindialog import Ui_LoginDialog
from .ui.ui_simpletreedialog import Ui_SimpleTreeDialog

class ConfirmDialog(QtGui.QMessageBox):

    buttonChoice = Signal(str)

    iconDct = {
            "question": QtGui.QMessageBox.Question,
            "information":QtGui.QMessageBox.Information,
            "warning" :QtGui.QMessageBox.Warning,
            "critical":QtGui.QMessageBox.Critical
            }

    def __init__(self, **kwargs):

        parent = None

        self._parent = kwargs.pop("parent", kwargs.pop("p", parent))
        self._title = kwargs.pop("title", kwargs.pop("t", 'Confirm Dialog box'))
        self._icon = kwargs.pop("icon", kwargs.pop("icn", "information"))

        self._buttons = kwargs.pop("button", kwargs.pop("b", ['Confirm']))
        self._cancelBtn = kwargs.pop("cancelButton", kwargs.pop("cb", None))
        self._defaultBtn = kwargs.pop("defaultButton", kwargs.pop("db", None))
        self._dismissString = kwargs.pop("dismissString", kwargs.pop("ds", "dismiss"))

        self._message = kwargs.get("message", kwargs.get("m", "Are you sure ?"))

        super(ConfirmDialog, self).__init__(self._parent)

        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setObjectName("confirmDialog")

        self.setUI()

    def setUI(self):

        self.setWindowTitle(self._title)

        self.setText(self._message)

        self.setIcon(self.iconDct.get(self._icon, QtGui.QMessageBox.NoIcon))

        for sButton in self._buttons:
            self.__dict__[sButton + "PushButton"] = self.addButton(sButton, QtGui.QMessageBox.ActionRole)
            self.__dict__[sButton + "PushButton"].setObjectName(sButton + "_PushButton")
            self.__dict__[sButton + "PushButton"].clicked.connect(self.clicked)

        if not self._cancelBtn:
            if len(self._buttons) == 1:
                self._cancelBtn = self._buttons[0]

        if self._cancelBtn in self._buttons:
            self.setEscapeButton(self.__dict__[self._cancelBtn + "PushButton"])

        if not self._defaultBtn:
            self.defaultBtn = self._buttons[0]

        if self._defaultBtn in self._buttons:
            self.setDefaultButton(self.__dict__[self._defaultBtn + "PushButton"])

    def clicked(self):
        button = self.sender()
        if button is None or not isinstance(button , QtGui.QPushButton):
            return None

        sButton = button.text()
        self.buttonChoice.emit(sButton)
        self.close()

    def dismissString(self):
        return self._dismissString

def confirmDialog(**kwargs):
    """
    This is the similar and replacement implementation of the Maya confirmDialog.
    """
    global result
    result = None

    if qtGuiApp():

        def choice(sButton):
            global result
            result = sButton

        confirmDlg = ConfirmDialog(**kwargs)
        confirmDlg.buttonChoice.connect(choice)
        dismiss = confirmDlg.dismissString()
        confirmDlg.exec_()
        if not result:
            result = dismiss
        return result

    else:
        return confirmMessage(kwargs.get("title", kwargs.get("t", 'PLEASE...')),
                              kwargs.get("message", kwargs.get("m", "Are you sure ?")),
                              kwargs.get("button", kwargs.get("b", ['Confirm'])))

class PromptDialog(QtGui.QDialog):

    buttonChoice = Signal(str)

    def __init__(self, **kwargs):

        oWin = None
#        if cmnCfg.INSIDE_MAYA:
#            oWin = getWidget("MayaWindow")

        self._parent = kwargs.pop("parent", kwargs.pop("p", oWin))
        self._title = kwargs.pop("title", kwargs.pop("t", 'Confirm Dialog box'))

        self._buttons = kwargs.pop("button", kwargs.pop("b", ['Confirm']))
        self._cancelBtn = kwargs.pop("cancelButton", kwargs.pop("cb", None))
        self._defaultBtn = kwargs.pop("defaultButton", kwargs.pop("db", None))
        self._dismissString = kwargs.pop("dismissString", kwargs.pop("ds", "dismiss"))

        self._style = kwargs.pop("style", kwargs.pop("st", 'text'))
        self._inputValue = kwargs.pop("text", kwargs.pop("t", ""))
        self._minValue = kwargs.pop("minimum", kwargs.pop("min", 1))
        self._maxValue = kwargs.pop("maximum", kwargs.pop("max", 99))

        sStyleList = ("integer", "text", "float")
        if self._style not in sStyleList:
            raise TypeError('Wrong type passed to style argument: "{0}", should be one of the list: {1}.'
                            .format(self._style, sStyleList))

        if not self._style == "text":
            oFloatClsList = (float, int)

            if not isinstance(self._minValue, oFloatClsList):
                raise TypeError('Wrong type passed to "min" argument: "{0}", should be one of the list: {1}.'
                                .format(self._minValue, oFloatClsList))

            if not isinstance(self._maxValue, oFloatClsList):
                raise TypeError('Wrong type passed to "max" argument: "{0}", should be one of the list: {1}.'
                                 .format(self._maxValue, oFloatClsList))

            if self._inputValue:
                if not isinstance(self._inputValue, oFloatClsList):
                    raise TypeError('Wrong type passed to "text" argument: "{0}", should be one of the list: {1}.'
                                     .format(self._inputValue, oFloatClsList))
            else:
                self._inputValue = self._minValue

        self._range = (self._minValue, self._maxValue)

        self._message = kwargs.pop("message", kwargs.pop("m", "Are you sure ?"))

        super(PromptDialog, self).__init__(self._parent)

        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setObjectName("promptDialog")

        self.setUI()

    def setUI(self):

        self.setWindowTitle(self._title)

        self.gridLayout = QtGui.QGridLayout(self)
        self.gridLayout.setObjectName("gridLayout")
        self.setLayout(self.gridLayout)

        self.label = QtGui.QLabel(self)
        self.label.setText(self._message)
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        if  self._style == "text":

            self.prompt = QtGui.QLineEdit(self)
            self.prompt.setText(self._inputValue)

        else:

            if self._style == "integer":
                self.prompt = QtGui.QSpinBox(self)

            elif self._style == "float":
                self.prompt = QtGui.QDoubleSpinBox(self)

            self.prompt.setAccelerated(True)
            self.prompt.setRange(*self._range)
            self.prompt.setValue(self._inputValue)

        self.gridLayout.addWidget(self.prompt, 1, 0, 1, 1)

        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setCenterButtons(True)

        self.gridLayout.addWidget(self.buttonBox, 2, 0, 1, 1)

        if not self._cancelBtn:
            if len(self._buttons) == 1:
                self._cancelBtn = self._buttons[0]

        if self._cancelBtn in self._buttons:
            self._buttons.remove(self._cancelBtn)

            self.__dict__[self._cancelBtn + "PushButton"] = self.buttonBox.addButton(self._cancelBtn, QtGui.QDialogButtonBox.RejectRole)
            self.__dict__[self._cancelBtn + "PushButton"].setObjectName(self._cancelBtn + "_PushButton")
            self.__dict__[self._cancelBtn + "PushButton"].clicked.connect(self.clicked)

        for sButton in self._buttons:
            self.__dict__[sButton + "PushButton"] = self.buttonBox.addButton(sButton, QtGui.QDialogButtonBox.ActionRole)
            self.__dict__[sButton + "PushButton"].setObjectName(sButton + "_PushButton")
            self.__dict__[sButton + "PushButton"].clicked.connect(self.clicked)

        if not self._defaultBtn:
            self.defaultBtn = self._buttons[0]

        if self._defaultBtn in self._buttons:
            self.__dict__[self._defaultBtn + "PushButton"].setDefault(True)

    def clicked(self):
        button = self.sender()
        if button is None or not isinstance(button , QtGui.QPushButton):
            return None

        sButton = button.text()
        self.buttonChoice.emit(sButton)

        global PROMPT_TEXT
        PROMPT_TEXT = self.getValue()

        self.close()

    def getValue(self):

        style = self._style
        if style == "text":
            oValue = toUnicode(self.prompt.text())

        elif style in ("integer", "float"):
            oValue = self.prompt.value()

        return oValue

    def dismissString(self):
        return self._dismissString

def promptDialog(**kwargs):
    """
    This is the similar and replacement implementation of the Maya promptDialog.
    """
    global result
    result = None

    global PROMPT_TEXT

    def choice(sButton):
        global result
        result = str(sButton)

    query = kwargs.pop("query", kwargs.pop("q", False))
    if query == True:
        return PROMPT_TEXT

    else:
        PROMPT_TEXT = ""
        promptDlg = PromptDialog(**kwargs)
        promptDlg.buttonChoice.connect(choice)
        dismiss = promptDlg.dismissString()
        promptDlg.exec_()
        if not result:
            result = dismiss
        return result


class LoginDialog(QtGui.QDialog, Ui_LoginDialog):

    loginSubmitted = Signal(unicode, unicode)

    __resultData = None

    def __init__(self, submitSlot=None, parent=None):
        super(LoginDialog , self).__init__(parent)

        self.setupUi(self)

        self.password_lineEdit.setEchoMode(QtGui.QLineEdit.Password)
        self.connexion_btn.clicked.connect(self.submitLogin)
        self.submitSlot = submitSlot

    def getUsername(self):
        return self.username_lineEdit.text()

    def getPassword(self):
        return self.password_lineEdit.text()

    def submitLogin(self):

        sUser, sPwd = (self.getUsername(), self.getPassword())

        res = None
        if self.submitSlot:

            try:
                res = self.submitSlot(sUser, sPwd)
            except Exception, err:
                confirmDialog(title='SORRY !'
                            , message=toStr(err)
                            , button=["OK"]
                            , defaultButton="OK"
                            , cancelButton="OK"
                            , dismissString="OK"
                            , icon="critical")

                if inDevMode():
                    raise

                return

        elif sUser and sPwd:
            res = (sUser, sPwd)

        if res:
            self.__class__.__resultData = res
            self.accept()

    @classmethod
    def resultData(cls):
        data = cls.__resultData
        cls.__resultData = None
        return data

def loginDialog(loginFunc=None):

    loginDlg = LoginDialog(submitSlot=loginFunc)
    loginDlg.exec_()

    return LoginDialog.resultData()


class SimpleTreeDialog(QtGui.QDialog, Ui_SimpleTreeDialog):

    def __init__(self, *args, **kwargs):
        super(SimpleTreeDialog, self).__init__(*args, **kwargs)

        self.setupUi(self)

        self.treeWidget.itemExpanded.connect(self.resizeAllColumns)

    def resizeAllColumns(self, item):
        treeWdg = self.treeWidget
        for c in xrange(treeWdg.columnCount()):
            treeWdg.resizeColumnToContents(c)
