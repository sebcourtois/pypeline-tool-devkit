
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

    def __init__(self):

        self._writingValues_ = False
        self.__metaProperties = {}

        for sProperty, _ in self.__class__.propertiesDctItems:

            metaprpty = self.__class__.propertyFactoryClass(sProperty, self)
            setattr(self, metaprpty.name, metaprpty.defaultValue)

            self.__metaProperties[sProperty] = metaprpty

        logMsg(self.__class__.__name__, log='all')

    def loadData(self):
        logMsg(self.__class__.__name__, log='all')

        for sProperty, _ in self.__class__.propertiesDctItems:

            metaprpty = self.__metaProperties[sProperty]
            if metaprpty.isReadable():
                setattr(self, metaprpty.name, metaprpty.read())


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

    def setPrpty(self, sProperty, value, write=True):
        logMsg(self.__class__.__name__, log='all')

        metaprpty = self.__metaProperties[sProperty]

        if metaprpty.isValidValue(value):

            if write:
                if metaprpty.isWritable():
                    bStatus = metaprpty.write(value)
                    if not bStatus:
                        return False
                else:
                    logMsg(u"<{}> Writing to non-writable property: {}.{} ."
                           .format(getCaller(fo=0), self, metaprpty.name), warning=True)

            setattr(self, metaprpty.name, value)

            return True

        else:
            logMsg(" {0}.{1} : Invalid value : '{2}'"
                   .format(self, sProperty, value) , warning=True)
            return False

    def iterPropertyNames(self, **params):

        cls = self.__class__
        sPropertyIter = (s for s, _ in cls.propertiesDctItems)

        bFilter = True if params else False
        if not bFilter:
            return sPropertyIter

        return self.filterPropertyNames(sPropertyIter, **params)

    def filterPropertyNames(self, propertyNames, **params):

        sPropertyIter = self.__class__._iterPropertyArg(propertyNames)

        for sPrpty in sPropertyIter:

            ok = True
            for k, value in params.iteritems():
                if self.getPrptyParam(sPrpty, k, "") != value:
                    ok = False
                    break
            if ok:
                yield sPrpty

    def getPrptyParam(self, sProperty, key, default="NoEntry"):

        cls = self.__class__

        assert sProperty in cls.propertiesDct

        if default == "NoEntry":
            return cls.propertiesDct[sProperty][key]
        else:
            return cls.propertiesDct[sProperty].get(key, default)

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

            bWriteOnly = False

            sSetFnc = "set" + upperFirst(sProperty)
            setFnc = getattr(self, sSetFnc, None)

            msg = u"Setting {0}.{1} to {2}( {3} ) using {4}".format(
                    self, sProperty, type(value).__name__, toStr(value), setFnc if setFnc else "setPrpty")
            logMsg(msg, log="debug")

            bSuccess = False
            if setFnc:
                try:
                    bSuccess = setFnc(value, writingAttrs=True)
                except TypeError:
                    try:
                        bSuccess = setFnc(value)
                    except Exception, msg:
                        logMsg(msg , warning=True)
                        bWriteOnly = True
            else:
                bWriteOnly = True

            if bWriteOnly:
                metaprpty = self.__metaProperties[sProperty]
                if metaprpty.isWritable():
                    bSuccess = metaprpty.write(value)
                else:
                    logMsg(u"<{}> Writing to non-writable property: {}.{} ."
                           .format(getCaller(fo=0), self, metaprpty.name), warning=True)
                    bSuccess = True

            if not bSuccess:
                logMsg("Failed " + lowerFirst(msg), warning=True)

    def getAllValues(self, propertyNames=None):

        sPropertyIter = self.__class__._iterPropertyArg(propertyNames)
        return dict((p, self.getPrpty(p)) for p in sPropertyIter)

    def copyValuesFrom(self, srcobj):

        sPropertyList = []

        for sProperty, _ in self.__class__.propertiesDctItems:

            srcprpty = srcobj.metaProperty(sProperty)
            if not srcprpty:
                continue

            if srcprpty.isCopyable():
                value = srcprpty.getattr_()
                # deferred write of all values
                self.setPrpty(sProperty, value, write=False)
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

            if metaprpty.defaultValue == "undefined" and not bIgnoreMissing:

                try:
                    value = kwargs.pop(metaprpty.name)
                except KeyError:
                    msg = u'{0} needs "{1}" kwarg at least'.format(cls.__name__, metaprpty.name)
                    raise TypeError(msg)

                else:
                    setattr(self, metaprpty.name, value)

            else:
                value = kwargs.pop(metaprpty.name, metaprpty.defaultValue)
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

    @classmethod
    def _iterPropertyArg(cls, propertyNames):

        if propertyNames is None:
            return (n for n, _ in cls.propertiesDctItems)
        elif isinstance(propertyNames, set):
            return (n for n, _ in cls.propertiesDctItems if n in propertyNames)
        else:
            return propertyNames


    def __repr__(self):

        cls = self.__class__

        try:
            sClsName = upperFirst(cls.classLabel) if hasattr(cls, "classLabel") else cls.__name__
            sRepr = ("{0}('{1}')".format(sClsName, toStr(getattr(self, cls.classReprAttr))))
        except AttributeError:
            sRepr = cls.__name__

        return sRepr
