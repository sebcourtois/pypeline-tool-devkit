

from PySide.QtCore import Qt, QFileInfo
from PySide import QtGui

try:
    import shiboken
except ImportError:
    from PySide import shiboken

_qTransformModeDct = {
"fast":Qt.FastTransformation,
"smooth":Qt.SmoothTransformation
}

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

        qApp = QtGui.QApplication.instance()
        if qApp and (qApp.type() != QtGui.QApplication.Tty):
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
