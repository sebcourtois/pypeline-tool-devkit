
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
    ("accessor", ""),
    ("reader", ""),
    ("writer", ""),
    ("copyable", False),
    ("lazy", False),
    ("stored", True),
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

        sAccessor = propertyDct["accessor"]
        self._accessor = sAccessor

        sReader = propertyDct["reader"]
        self.__readable = True if sReader else False
        self._reader = sReader
        self.__read = None

        sWriter = propertyDct["writer"]
        self.__writable = True if sWriter else False
        self._writer = sWriter
        self.__write = None

        self.__copyable = propertyDct["copyable"]
        self.__lazy = propertyDct["lazy"]
        self.__stored = propertyDct["stored"]

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
        return self.__stored

    def isValidValue(self, value):
        return True

    def isReadable(self):

        bReadable = self.__readable and self.initAccessors()

        if bReadable and (not self.__read):
            sReader = self._reader
            if '(' in sReader:
                sFunc, sAttr = sReader.split('(', 1)
                self._reader = sAttr.strip(')')
                self.__read = getattr(self._accessor, sFunc)
            else:
                self.__read = partial(getattr, self._accessor)

        return bReadable

    def read(self):

        reader = self._reader
        if reader:
            value = self.__read(reader)
        else:
            value = self.__read()

        return value

    def isWritable(self):

        bWritable = self.__writable and self.initAccessors(create=True)

        if bWritable and (not self.__write):
            sWriter = self._writer
            if '(' in sWriter:
                sFunc, sAttr = sWriter.split('(', 1)
                self._writer = sAttr.strip(')')
                self.__write = getattr(self._accessor, sFunc)
            else:
                self.__write = partial(setattr_, self._accessor)

        return bWritable

    def write(self, value):

        writer = self._writer
        if writer:
            bStatus = self.__write(writer, value)
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
