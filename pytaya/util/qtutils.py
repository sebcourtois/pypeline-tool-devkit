
from maya import OpenMayaUI as omui

# Import available PySide or PyQt package, as it will work with both
try:
#    from PySide.QtCore import Qt, QPoint, QSize
#    from PySide.QtCore import Signal
    from PySide.QtGui import QMainWindow, QWidget
    from shiboken import wrapInstance
    _qtImported = 'PySide'
except ImportError, e1:
    try:
#        from PyQt4.QtCore import Qt, QPoint, QSize
#        from PyQt4.QtCore import pyqtSignal as Signal
        from PyQt4.QtGui import QMainWindow, QWidget
        from sip import wrapinstance as wrapInstance
        _qtImported = 'PyQt4'
    except ImportError, e2:
        raise ImportError, '%s, %s' % (e1, e2)


def mayaMainWindow():

    mainWinPtr = omui.MQtUtil.mainWindow()
    mainWin = wrapInstance(long(mainWinPtr), QMainWindow)
    return mainWin

def findWindow(sWindowName):

    ptr = omui.MQtUtil.findWindow(sWindowName)
    if not ptr:
        return None

    window = wrapInstance(long(ptr), QWidget)
    return window

