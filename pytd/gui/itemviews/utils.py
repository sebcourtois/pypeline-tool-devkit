
import os.path as osp
import datetime
import subprocess

from PySide.QtCore import Qt, SIGNAL
from PySide import QtGui

from pytd.util.sysutils import toUnicode
from pytd.util.systypes import MemSize
from pytd.util.sysutils import isIterable
from pytd.gui.dialogs import confirmDialog

class ItemUserFlag:
    MultiEditable = Qt.ItemFlag(128)

class ItemUserRole:
    ImageRole = Qt.UserRole + 1
    GroupSortRole = Qt.UserRole + 2
    IconRole = Qt.UserRole + 3

def createAction(text, parentWidget, **kwargs):

    slot = kwargs.get("slot", None)
    icon = kwargs.get("icon", None)
    tip = kwargs.get("tip", None)
    checkable = kwargs.get("checkable", None)
    signal = kwargs.get("signal", "triggered(bool)")

    action = QtGui.QAction(text, parentWidget)
    if icon is not None:
        action.setIcon(QtGui.QIcon(":/{0}.png".format(icon)))
    if tip is not None:
        action.setToolTip(tip)
        action.setStatusTip(tip)
    if slot is not None:
        parentWidget.connect(action, SIGNAL(signal), slot)
    if checkable:
        action.setCheckable(True)
    return action

def toDisplayText(value, sep=", "):

    if value in (None, False, "undefined"):
        return ""

    elif value is True:
        return "on"

    elif isinstance(value, datetime.date):
        try:
            return value.strftime("%Y-%m-%d %H:%M")
        except ValueError:
            return ""

    elif isinstance(value, MemSize):
        return "{0:.2cM}".format(value)

    elif isinstance(value, basestring):
        return toUnicode(value)

    elif isIterable(value):
        return sep.join((toDisplayText(v, sep) for v in value))

    else:
        return toUnicode(value)


def toEditText(value, sep=", "):

    if value is None:
        return ""

    elif isinstance(value, basestring):
        return toUnicode(value)

    elif isinstance(value, bool):
        return toUnicode(int(value))

    elif isIterable(value):
        return sep.join((toEditText(v, sep) for v in value))

    else:
        return toUnicode(value)


def showPathInExplorer(sPath, isFile=False, select=False):

    p = osp.normpath(sPath)

    if not osp.exists(p):

        sPathType = "file" if isFile else "directory"

        confirmDialog(title='SORRY !'
                    , message='No such {0} found: \n\n{1}'.format(sPathType, p)
                    , button=['OK']
                    , icon="critical")
        return False

    sCmd = "explorer /select, {0}" if isFile or select else "explorer {0}"
    sCmd = sCmd.format(p)
    subprocess.Popen(sCmd, shell=True)

    return True
