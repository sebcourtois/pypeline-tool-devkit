

from PySide.QtCore import Qt, QFileInfo
from PySide import QtGui

from pytd.util.sysutils import qtGuiApp

try:
    import shiboken
except ImportError:
    try:
        from PySide import shiboken
    except ImportError:
        print "shiboken not found."

_qTransformModeDct = {
"fast":Qt.FastTransformation,
"smooth":Qt.SmoothTransformation
}

def getWidget(sWidgetName="", **kwargs):

    bWithFocus = kwargs.pop("withFocus", kwargs.pop("wf", False))

    if bWithFocus:

        return QtGui.qApp.focusWidget()

    else:

        if not sWidgetName:
            raise ValueError, 'Invalid input widget name to get: "{0}"'.format(sWidgetName)

        bTopLevel = kwargs.pop("topLevelWidgets", kwargs.pop("top", True))

        widgetList = QtGui.qApp.topLevelWidgets() if bTopLevel else QtGui.qApp.allWidgets()

        foundWidgets = []
        for widget in widgetList:
            if widget.objectName() == sWidgetName:
                foundWidgets.append(widget)

        if foundWidgets:
            return foundWidgets if len(foundWidgets) > 1 else foundWidgets[0]

def clampPixmapSize(pixmap, iLimitSize, mode="fast"):

    qMode = _qTransformModeDct[mode]

    if pixmap.height() > iLimitSize:
        pixmap = pixmap.scaledToHeight(iLimitSize, qMode)
    if pixmap.width() > iLimitSize:
        pixmap = pixmap.scaledToWidth(iLimitSize, qMode)

    return pixmap

def toQPixmap(sFilePath, **kwargs):

    iLimitSize = kwargs.pop("limitSize", None)

    pixmap = QtGui.QPixmap(sFilePath)

    if iLimitSize:
        pixmap = clampPixmapSize(pixmap, iLimitSize, **kwargs)

    return pixmap

def toQColor(*args, **kwargs):

    sFormat = kwargs.pop("format", "rgbF")

    fromFormat = getattr(QtGui.QColor, "from" + sFormat[0].upper() + sFormat[1:])

    return fromFormat(*args)

def toColorSheet(qColor, default=None):
    """converts a QColor to string for stylesheet"""

    qSpec = qColor.spec()

    if qSpec == QtGui.QColor.Invalid:
        if default:
            return default
        values = ("rgba", 0, 0, 0, 255)
    if qSpec == QtGui.QColor.Rgb:
        values = ("rgba", qColor.red(), qColor.green(), qColor.blue(), qColor.alpha())
    elif qSpec == QtGui.QColor.Hsv:
        values = ("hsva", qColor.hue(), qColor.saturation(), qColor.value(), qColor.alpha())
    else:
        raise NotImplementedError, "Not yet supported QColor.Spec: {0}".format(qSpec)

    return "{0}({1},{2},{3},{4})".format(*values)

def toQFileInfo(p):

    if (not p) or isinstance(p, QFileInfo):
        fileInfo = p
    else:
        fileInfo = QFileInfo(p)

    if fileInfo and fileInfo.isRelative():
        raise ValueError("Given path is relative: '{}'".format(fileInfo.filePath()))

    return fileInfo

def setWaitCursor(func):

    def doIt(*args, **kwargs):

        bOverride = False

        qApp = qtGuiApp()
        if qApp:
            cursor = qApp.overrideCursor()
            if (not cursor) or (cursor.shape() != Qt.WaitCursor):
                bOverride = True

        if bOverride:
            qApp.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))

        try:
            ret = func(*args, **kwargs)
        finally:
            if bOverride:
                qApp.restoreOverrideCursor()

        return ret
    return doIt

def isValidQObj(qobj):
    return shiboken.isValid(qobj)
