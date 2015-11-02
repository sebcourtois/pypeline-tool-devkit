
import re
from functools import partial
from copy import copy

from pytd.util.logutils import logMsg
from pytd.util.sysutils import argToList

class EditState:
    Disabled = 0
    Enabled = 1
    Multi = 2


def setattr_(*args):

    try:
        setattr(*args)
    except AttributeError:
        return False

    return True

_STR_TO_LIST_RGX = re.compile(r'[\w\-.]+', re.L)

class MetaProperty(object):

    parameterDefaults = (
        ("isMulti", False),
        ("default", "undefined"),
        ("copyable", False),
        ("lazy", False),
        ("accessor", ""),
        ("reader", ""),
        ("writer", ""),
    )

    def __init__(self , sProperty, metaobj):

        propertyDct = metaobj.__class__.propertiesDct[sProperty]

        for sParam, value in self.__class__.parameterDefaults:
            if sParam not in propertyDct:
                propertyDct[sParam] = value

        self.type = propertyDct["type"]
        self.__isMulti = propertyDct["isMulti"]

        self.__copyable = propertyDct["copyable"]
        self.__lazy = propertyDct["lazy"]

        sAccessor = propertyDct["accessor"]
        self.accessorName = sAccessor
        self._accessor = None
        self.__readFunc = None
        self.__writeFunc = None

        sReader = propertyDct["reader"]
        self.__readable = True if sReader else False
        if '(' in sReader:
            sFunc, sAttr = sReader.split('(', 1)
            self._readAttr = sAttr.strip(')')
            self.readerName = sFunc
        else:
            self._readAttr = sReader
            self.readerName = ""

        propertyDct["readable"] = self.__readable

        sWriter = propertyDct["writer"]
        bWritable = True if sWriter else False
        if '(' in sWriter:
            sFunc, sAttr = sWriter.split('(', 1)
            self.storageName = sAttr.strip(')')
            self.writerName = sFunc
        else:
            self.storageName = sWriter
            self.writerName = ""

        propertyDct["writable"] = bWritable

        if "stored" in propertyDct:
            bStored = propertyDct["stored"]
        else:
            bStored = True if (bWritable and self.storageName) else False
            propertyDct["stored"] = bStored
        self.__stored = bStored

        self.__writable = bWritable

        self._metaobj = metaobj

        self.name = sProperty
        self.propertyDct = propertyDct

    def initAccessor(self, create=False):

        bLazy = self.__lazy
        curAccessor = self._accessor

        if (not bLazy) and curAccessor:
            return True

        sAccessor = self.accessorName
        if not sAccessor:
            logMsg("No accessor defined: '{}'".format(sAccessor), log='debug')
            return False

        newAccessor = getattr(self._metaobj, sAccessor)
        if newAccessor:
            if id(newAccessor) != id(curAccessor):
                self.__readFunc = None
                self.__writeFunc = None
        elif bLazy:
            self.__readFunc = None
            self.__writeFunc = None
            if create:
                newAccessor = self.createAccessor()
                if newAccessor:
                    setattr(self._metaobj, sAccessor, newAccessor)
                else:
                    raise RuntimeError("Could not create accessor for {}".format(self))
            else:
                return False

        self._accessor = newAccessor

        return True if newAccessor else False

    def createAccessor(self):
        raise NotImplementedError("must be implemented in subclass")

    def getParam(self, sParam, default="NoEntry"):

        if default == "NoEntry":
            value = self.propertyDct[sParam]
        else:
            value = self.propertyDct.get(sParam, default)

        return copy(value)

    def defaultValue(self):

        value = copy(self.propertyDct.get("default", "undefined"))
        return argToList(value) if self.__isMulti else value

    def isMulti(self):
        return self.__isMulti

    def isInput(self):
        return self.propertyDct.get("inputData", False)

    def isCopyable(self):
        return self.__copyable

    def isLazy(self):
        return self.__lazy

    def isStored(self):
        return self.__stored

    def isValidValue(self, value):
        return True

    def isReadable(self):

        bReadable = self.__readable and self.initAccessor()

        if bReadable and (self.__readFunc is None):
            sFunc = self.readerName
            if sFunc:
                self.__readFunc = getattr(self._accessor, sFunc)
            else:
                self.__readFunc = partial(getattr, self._accessor)

        return bReadable

    def read(self):

        sAttr = self._readAttr
        if sAttr:
            value = self.__readFunc(sAttr)
        else:
            value = self.__readFunc()

        return value

    def isWritable(self):

        bWritable = self.__writable and self.initAccessor(create=True)

        if bWritable and (self.__writeFunc is None):
            sFunc = self.writerName
            if sFunc:
                self.__writeFunc = getattr(self._accessor, sFunc)
            else:
                self.__writeFunc = partial(setattr_, self._accessor)

        return bWritable

    def write(self, in_value):

        value = self.castToWrite(in_value)

        sAttr = self.storageName
        if sAttr:
            bStatus = self.__writeFunc(sAttr, value)
        else:
            bStatus = self.__writeFunc(value)

        if not isinstance(bStatus, bool):
            sFunc = self.writerName
            raise ValueError("Writer function must return a boolean: {}.{}"
                             .format(self._accessor, sFunc))

        return bStatus

    def castToWrite(self, in_value):

        if in_value == "undefined":
            raise ValueError(u"Bad value for {}.{}: '{}'."
                   .format(self._metaobj, self.name, in_value))

        return in_value

    def castFromUi(self, value):

        if self.isMulti():
            if value and isinstance(value, basestring):
                values = _STR_TO_LIST_RGX.findall(value)
            else:
                values = argToList(value)

            _castFromUi = self._castFromUi
            return list(_castFromUi(v) for v in values)

        return value

    def _castFromUi(self, value):
        return value

    def getattr_(self, *args):
        return getattr(self._metaobj, self.name, *args)

    def getPresetValues(self):
        return None, True

    def __repr__(self):

        cls = self.__class__

        try:
            sRepr = ("{0}('{1}')".format(cls.__name__, self.name))
        except AttributeError:
            sRepr = cls.__name__

        return sRepr


class BasePropertyFactory(object):

    propertyTypeDct = {}

    def __new__(cls, sProperty, metaobj):

        sPropertyType = metaobj.__class__.propertiesDct[sProperty]["type"]
        PropertyClass = cls.propertyTypeDct[sPropertyType]
        return PropertyClass(sProperty, metaobj)
