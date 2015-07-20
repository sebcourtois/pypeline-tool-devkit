
import inspect as insp

from pytd.util.sysutils import deepCopyOf, copyOf
from pytd.util.sysutils import listClassesFromModule
from pytd.util.fsutils import pathJoin

class PyConfParser(object):

    def __init__(self, pyobj, predefVarParams=None):

        bLoadSection = False
        if insp.ismodule(pyobj):
            bLoadSection = True
        elif insp.isclass(pyobj):
            pass
        else:
            raise TypeError(
                    "argument 'pyobj' must be of type <module> or <class>. Got {0}"
                    .format(type(pyobj)))

        self._pyobj = pyobj

        self._errosOnInit = []
        self.__sections = {}

        self.declareVarsFromTree()
        self.checkPredefVars(predefVarParams)

        if bLoadSection:
            self.loadSections()

        if self._errosOnInit:
            raise ImportError(self.formatedErrors(self._errosOnInit))

    def _checkVar(self, sConfVar, expectedType, out_sErrorMsgList, **kwargs):

        bDeepCopy = kwargs.pop("deepCopy", False)
        defaultValue = kwargs.pop("default", "NoEntry")

        bSetVar = False
        pyobj = self._pyobj

        try:
            value = getattr(pyobj, sConfVar)
        except AttributeError:
            if defaultValue == "NoEntry":
                out_sErrorMsgList.append('"{0}" : Missing'.format(sConfVar))
                return
            else:
                value = defaultValue
                bSetVar = True

        if not isinstance(value, expectedType):
            msg = u'"{0}": Expected {1}, got {2}'.format(sConfVar, expectedType, type(value))
            out_sErrorMsgList.append(msg)
            return

        if bDeepCopy:
            copiedValue = deepCopyOf(value)
        else:
            copiedValue = copyOf(value)

        if bSetVar:
            setattr(pyobj, sConfVar, copiedValue)

        return copiedValue

    def checkPredefVars(self, predefVarParams):

        if not predefVarParams:
            return

        for sConfVar, varParams in predefVarParams:
            self._checkVar(sConfVar,
                           varParams["type"],
                           self._errosOnInit,
                           default=varParams.get("default", "NoEntry"))

    def recurseTreeVars(self, treeDct, sStartPath, parentConf=None):

        pyobj = parentConf._pyobj if parentConf else self._pyobj

        for sDirVar, childDct in treeDct.iteritems():

            if "->" in sDirVar:
                sDirName, sConfVar = sDirVar.split("->", 1)
            else:
                sDirName = sDirVar
                sConfVar = ""

            sPath = pathJoin(sStartPath, sDirName.strip())

            if sConfVar:
                sConfVar = sConfVar.strip()

                sDefinedPath = getattr(pyobj, sConfVar, None)
                if sDefinedPath is None:
                    setattr(pyobj, sConfVar, sPath)
                else:
                    msg = u'"{0}" :  Already defined to "{1}"'.format(sConfVar, sDefinedPath)
                    self._errosOnInit.append(msg)
                    continue

            if childDct:
                self.recurseTreeVars(childDct, sPath, parentConf)

    def declareVarsFromTree(self):

        for sTreeVar in dir(self._pyobj):
            if sTreeVar.endswith("_tree"):
                self.recurseTreeVars(getattr(self._pyobj, sTreeVar), "")

    def _getSectionVar(self, sVarName, default="NoEntry", **kwargs):

        bAsDict = kwargs.get("asDict", False)

        pyobj = self._pyobj

        if default == "NoEntry":
            value = getattr(pyobj, sVarName)
        else:
            value = getattr(pyobj, sVarName, default)

        if bAsDict and not isinstance(value, dict):
            try:
                value = dict(value)
            except ValueError:
                raise ValueError('Could not cast configuration variable to a dictionary: "{0}".'
                                 .format(sVarName))

        return copyOf(value)

    def getVar(self, sSection, sVarName, default="NoEntry", **kwargs):
        return self.getSection(sSection)._getSectionVar(sVarName, default, **kwargs)

    def loadSections(self):

        for sSection, sectionCls in listClassesFromModule(self._pyobj.__name__):
            self.__sections[sSection] = PyConfParser(sectionCls)

    def getSection(self, sSectionName):

        sections = self.__sections
        try:
            return sections[sSectionName]
        except KeyError:
            msg = u"<{}> No such section: '{}'. \n\n\tExpected values: {}".format(self, sSectionName, sections.keys())
            raise KeyError(msg)

    def formatedErrors(self, sErrorList):
        return 'Failed initializing {0}: \n\t{1}'.format(self, "\n\t".join(sErrorList))

    def __repr__(self):

        try:
            sRepr = ("{0}({1})".format(self.__class__.__name__, self._pyobj.__name__))
        except:
            sRepr = object.__repr__(self)

        return sRepr
