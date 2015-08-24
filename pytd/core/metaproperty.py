
from functools import partial

from pytd.util.logutils import logMsg
from pytd.util.sysutils import copyOf, argToList

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

        value = copyOf(propertyDct.get("default", "undefined"))
        self.defaultValue = argToList(value) if self.__isMulti else value

        self.__copyable = propertyDct["copyable"]
        self.__lazy = propertyDct["lazy"]

        sAccessor = propertyDct["accessor"]
        self._accessor = sAccessor

        sReader = propertyDct["reader"]
        self.__readable = True if sReader else False
        if '(' in sReader:
            sFunc, sAttr = sReader.split('(', 1)
            self._readAttr = sAttr.strip(')')
            self.__read = sFunc
        else:
            self._readAttr = sReader
            self.__read = ""

        propertyDct["readable"] = self.__readable

        sWriter = propertyDct["writer"]
        bWritable = True if sWriter else False
        if '(' in sWriter:
            sFunc, sAttr = sWriter.split('(', 1)
            self.storageName = sAttr.strip(')')
            self.__write = sFunc
        else:
            self.storageName = sWriter
            self.__write = ""

        propertyDct["writable"] = bWritable
        propertyDct["stored"] = True if bWritable and self.storageName else False

        self.__writable = bWritable

        self._metaobj = metaobj

        self.__accessorOk = False

        self.name = sProperty
        self.propertyDct = propertyDct

    def initAccessors(self, create=False):

        if self.__accessorOk:
            return True

        sAccessor = self._accessor
        if not sAccessor:
            logMsg("No accessor defined: '{}'".format(sAccessor), log='debug')
            return False

        accessor = getattr(self._metaobj, sAccessor)
        if (not accessor) and self.__lazy:
            if create:
                accessor = self.createAccessor()
                if accessor:
                    setattr(self._metaobj, sAccessor, accessor)
                else:
                    raise RuntimeError("Could not create accessor for {}".format(self))
            else:
                return False

        if accessor:
            self._accessor = accessor

        self.__accessorOk = True

        return True

    def createAccessor(self):
        raise NotImplementedError("must be implemented in subclass")

    def getParam(self, sParam, default="NoEntry"):

        if default == "NoEntry":
            value = self.propertyDct[sParam]
        else:
            value = self.propertyDct.get(sParam, default)

        return copyOf(value)

    def isMulti(self):
        return self.__isMulti

    def isInput(self):
        return self.propertyDct.get("inputData", False)

    def isCopyable(self):
        return self.__copyable

    def isLazy(self):
        return self.__lazy

    def isStored(self):
        return self.__writable and self.storageName

    def isValidValue(self, value):
        return True

    def isReadable(self):

        bReadable = self.__readable and self.initAccessors()

        if bReadable and isinstance(self.__read, basestring):
            sFunc = self.__read
            if sFunc:
                self.__read = getattr(self._accessor, sFunc)
            else:
                self.__read = partial(getattr, self._accessor)

        return bReadable

    def read(self):

        sAttr = self._readAttr
        if sAttr:
            value = self.__read(sAttr)
        else:
            value = self.__read()

        return value

    def isWritable(self):

        bWritable = self.__writable and self.initAccessors(create=True)

        if bWritable and isinstance(self.__write, basestring):
            sFunc = self.__write
            if sFunc:
                self.__write = getattr(self._accessor, sFunc)
            else:
                self.__write = partial(setattr_, self._accessor)

        return bWritable

    def write(self, value):

        sAttr = self.storageName
        if sAttr:
            bStatus = self.__write(sAttr, value)
        else:
            bStatus = self.__write(value)

        if not isinstance(bStatus, bool):
            sWriter = self.propertyDct["writer"]
            raise ValueError("Writer function must return a boolean: {}.{}"
                             .format(self._accessor, sWriter))

        return bStatus

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
