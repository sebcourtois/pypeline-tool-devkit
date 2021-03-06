
from pytd.util.logutils import logMsg
from pytd.util.sysutils import argToTuple, getCaller
from pytd.util.sysutils import toStr
# from pytd.util.sysutils import getCaller
from pytd.util.strutils import upperFirst, lowerFirst

from .metaproperty import BasePropertyFactory

class MetaObject(object):

    classReprAttr = "name"

    propertiesDctItems = ()
    propertiesDct = {}

    presetByPropertyDct = {}

    propertyFactoryClass = BasePropertyFactory
    propertyPerAccessorDct = None

    def __init__(self):

        cls = self.__class__

        self._writingValues_ = False
        self.__metaProperties = {}

        for sProperty, _ in cls.propertiesDctItems:

            metaprpty = cls.propertyFactoryClass(sProperty, self)
            setattr(self, metaprpty.name, metaprpty.defaultValue())

            self.__metaProperties[sProperty] = metaprpty

        logMsg(cls.__name__, log='all')

    def loadData(self, propertyNames=None):
        logMsg(self.__class__.__name__, log='all')

        sPropertyIter = self.__class__._iterPropertyArg(propertyNames)

        for sProperty in sPropertyIter:

            metaprpty = self.__metaProperties[sProperty]
            if metaprpty.isReadable():
                #logMsg("read", self, sProperty, metaprpty.read(), log="debug")
                setattr(self, metaprpty.name, metaprpty.read())
            elif metaprpty.isLazy():
                #logMsg("defaultValue", self, sProperty, metaprpty.defaultValue(), log="debug")
                setattr(self, metaprpty.name, metaprpty.defaultValue())

    def primeProperty(self):
        sProperty = self.__class__.primaryProperty
        return self.__metaProperties.get(sProperty)

    def metaProperty(self, sProperty):
        return self.__metaProperties.get(sProperty)

    def iterMetaPrpties(self, propertyNames=None, nones=True):

        sPropertyIter = self.__class__._iterPropertyArg(propertyNames)

        for sProperty in sPropertyIter:
            metaprpty = self.metaProperty(sProperty)

            if (not metaprpty) and (not nones):
                continue

            yield metaprpty

    def hasPrpty(self, sProperty):
        return sProperty in self.__metaProperties

    def getPrpty(self, sProperty, default="NoEntry"):
        logMsg(self.__class__.__name__, log='all')

        if default == "NoEntry":
            return getattr(self, sProperty)
        else:
            return getattr(self, sProperty, default)


    def setPrpty(self, sProperty, value, write=True, **kwargs):

        bUseSetter = kwargs.pop("useSetter", True)
        bWarn = kwargs.get("warn", True)
        sMsg = ""

        setter = None
        if bUseSetter:
            sSetter = self.metaProperty(sProperty).getParam("setter", "")
            setter = getattr(self, sSetter) if sSetter else None

            sMsg = "Setting {0}.{1} to {2}( {3} ) using {4}".format(
                    self, sProperty, type(value).__name__, toStr(value),
                    setter if setter else "_setPrpty")
            logMsg(sMsg, log="debug")

        bSuccess = False

        if setter:
            if bWarn:
                logMsg("{}.{}() can be used to set '{}' property !"
                       .format(self, sSetter, sProperty), warning=True)

            bSuccess = setter(value, write=write, **kwargs)
        else:
            bSuccess = self._setPrpty(sProperty, value, write=write)

        if (not bSuccess) and sMsg:
            logMsg("Failed " + lowerFirst(sMsg), warning=True)

        return bSuccess

    def _setPrpty(self, sProperty, value, write=True):
        logMsg(self.__class__.__name__, log='all')

        metaprpty = self.__metaProperties[sProperty]

        if not metaprpty.isValidValue(value):
            logMsg(u"{}.{} : Invalid value : '{}'"
                   .format(self, sProperty, value) , warning=True)
            return False

        if write:
            if metaprpty.isWritable():
                bSuccess = metaprpty.write(value)
                if not bSuccess:
                    return False
            else:
                logMsg(u"<{}> Writing to non-writable property: {}.{} ."
                       .format(getCaller(fo=0), self, metaprpty.name), warning=True)

        setattr(self, metaprpty.name, value)

        return True

    def createPrptyEditor(self, sProperty, parentWidget):

        assert sProperty in self.__metaProperties
        metaprpty = self.__metaProperties[sProperty]

        return metaprpty.createEditorWidget(parentWidget)

    def getPrptyValueFromWidget(self, sProperty, wdg):

        assert sProperty in self.__metaProperties
        metaprpty = self.__metaProperties[sProperty]

        return metaprpty.getValueFromWidget(wdg)

    def castValueForPrpty(self, sProperty, value):

        assert sProperty in self.__metaProperties
        metaprpty = self.__metaProperties[sProperty]

        if isinstance(value, (tuple, list)):
            return list(metaprpty.castValue(v) for v in value)
        else:
            return metaprpty.castValue(value)

    def writeAllValues(self, propertyNames=None):

        self._writingValues_ = True
        try:
            res = self._writeAllValues(propertyNames)
        finally:
            self._writingValues_ = False

        return res

    def _writeAllValues(self, propertyNames=None):
        logMsg(self.__class__.__name__, log='all')

        sPropertyIter = self.__class__._iterPropertyArg(propertyNames)

        for sProperty in sPropertyIter:

            value = getattr(self, sProperty)

            try:
                self.setPrpty(sProperty, value, write=True, useSetter=False)
            except Exception, msg:
                logMsg(toStr(msg), warning=True)

    def getAllValues(self, propertyNames=None):
        return dict(self.iterDataItems(propertyNames))

    def iterDataItems(self, propertyNames=None):

        sPropertyIter = self.__class__._iterPropertyArg(propertyNames)
        return ((p, self.getPrpty(p)) for p in sPropertyIter)

    def dataToStore(self, propertyNames=None):

        sPropertyIter = self.__class__._iterPropertyArg(propertyNames)

        data = {}

        for sProperty in sPropertyIter:
            metaprpty = self.__metaProperties[sProperty]

            if not metaprpty.isStored():
                continue

            sName = metaprpty.storageName
            if not sName:
                raise RuntimeError("No storage name defined for {}.{}".format(self, metaprpty.name))

            data[sName] = metaprpty.castToWrite(self.getPrpty(sProperty))

        return data

    def copyValuesFrom(self, srcobj):

        sPropertyList = []

        for sProperty, _ in self.__class__.propertiesDctItems:

            srcprpty = srcobj.metaProperty(sProperty)
            if not srcprpty:
                continue

            if srcprpty.isCopyable():
                value = srcprpty.getattr_()
                # deferred write of all values
                self._setPrpty(sProperty, value, write=False)
                sPropertyList.append(sProperty)

        return self.writeAllValues(sPropertyList)

    def initPropertiesFromKwargs(self, **kwargs):
        logMsg(self.__class__.__name__, log='all')

        logMsg("Entered kwargs:", kwargs, log="debug")

        bIgnoreMissing = kwargs.pop("ignoreMissingKwarg", False)

        cls = self.__class__

        # get all keyword arguments
        for sProperty, _ in cls.propertiesDctItems:
            metaprpty = self.__metaProperties[sProperty]

            defaultValue = metaprpty.defaultValue()
            if defaultValue == "undefined" and (not bIgnoreMissing):

                try:
                    value = kwargs.pop(metaprpty.name)
                except KeyError:
                    msg = u'{0} needs "{1}" kwarg at least'.format(cls.__name__, metaprpty.name)
                    raise TypeError(msg)

                else:
                    setattr(self, metaprpty.name, value)

            else:
                value = kwargs.pop(metaprpty.name, defaultValue)
                setattr(self, metaprpty.name, value)

        logMsg("Remaining kwargs:", kwargs, log="debug")

        return kwargs

    def createInputDataUI(self, parentWidget, **kwargs):
        cls = self.__class__
        logMsg(cls.__name__, log='all')

        sIgnorePrpty = kwargs.pop("ignoreInputData", [])
        sIgnorePrptyList = argToTuple(sIgnorePrpty)

        inputWdgItems = []

        for sProperty, _ in cls.propertiesDctItems:
            if sProperty in sIgnorePrptyList:
                continue

            metaprpty = self.__metaProperties[sProperty]
            if metaprpty.isInput():

                inputWdg = metaprpty.createEditorWidget(parentWidget)
                inputWdgItems.append((metaprpty.name , { "widget" : inputWdg }))

        return inputWdgItems

    def getPrptyPreset(self, sProperty):

        """ Do nothing by default. Should be reimplemented in sub-classes"""

        assert sProperty in self.__class__.propertiesDct

        return None, True

    def displayModelRow(self):
        return True

    @classmethod
    def _propertyNamesPerAccessor(cls, propertyNames=None):

        sPropertyIter = cls._iterPropertyArg(propertyNames)

        resDct = {}

        for sPrpty in sPropertyIter:
            sAccessor = cls.getPrptyParam(sPrpty, "accessor", "")
            resDct.setdefault(sAccessor, []).append(sPrpty)

        return resDct

    @classmethod
    def iterPropertyNames(cls, **params):

        sPropertyIter = (s for s, _ in cls.propertiesDctItems)

        bFilter = True if params else False
        if not bFilter:
            return sPropertyIter

        return cls.filterPropertyNames(sPropertyIter, **params)

    @classmethod
    def filterPropertyNames(cls, propertyNames, **params):

        sPropertyIter = cls._iterPropertyArg(propertyNames)

        for sPrpty in sPropertyIter:

            ok = True
            for k, value in params.iteritems():
                if cls.getPrptyParam(sPrpty, k, "") != value:
                    ok = False
                    break
            if ok:
                yield sPrpty

    @classmethod
    def getPrptyParam(cls, sProperty, key, default="NoEntry"):

        assert sProperty in cls.propertiesDct

        if default == "NoEntry":
            return cls.propertiesDct[sProperty][key]
        else:
            return cls.propertiesDct[sProperty].get(key, default)

    @classmethod
    def _iterPropertyArg(cls, propertyNames):

        if propertyNames is None:
            return (n for n, _ in cls.propertiesDctItems)
        elif isinstance(propertyNames, set):
            return (n for n, _ in cls.propertiesDctItems if n in propertyNames)
        else:
            return propertyNames

    def logData(self, *propertieNames):
        print self.dataRepr(*propertieNames)

    def dataRepr(self, *propertyNames):

        if not propertyNames:
            propertyNames = None

        s = u'{'
        for k, v in self.iterDataItems(propertyNames):
            sValType = type(v).__name__
            try:
                s += u"\n<{}> {}: {}".format(sValType, k, v)
            except:
                print sValType, k, v
                raise
        return (s + u'\n}')

    def __repr__(self):

        cls = self.__class__

        try:
            sClsName = upperFirst(cls.classLabel) if hasattr(cls, "classLabel") else cls.__name__
            sRepr = ("{0}('{1}')".format(sClsName, toStr(getattr(self, cls.classReprAttr))))
        except AttributeError:
            sRepr = cls.__name__

        return sRepr
