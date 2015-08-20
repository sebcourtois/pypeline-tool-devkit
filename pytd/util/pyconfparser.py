
import re
import inspect as insp

from pytd.util.sysutils import deepCopyOf, copyOf
from pytd.util.sysutils import listClassesFromModule
from pytd.util.fsutils import pathJoin

_SECTION_RGX = re.compile(r"{([\w]+)\.")

class PyConfParser(object):

    def __init__(self, pyobj, predefVarParams=None):

        bLoadSections = False
        if insp.ismodule(pyobj):
            bLoadSections = True
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

        if bLoadSections:
            self.loadSections()
#            for k, v in self.__sections.iteritems():
#                print k, v

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

                sDefinedPath = pyobj.__dict__.get(sConfVar, None)#getattr(pyobj, sConfVar, None)
                if sDefinedPath is None:
                    setattr(pyobj, sConfVar, sPath)
                    sPathVars = getattr(pyobj, "all_tree_vars", [])
                    sPathVars.append(sConfVar)
                    setattr(pyobj, "all_tree_vars", sPathVars)
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

    def hasVar(self, sSection, sVarName):
        return self.getSection(sSection)._sectionHasVar(sVarName)

    def getVar(self, sSection, sVarName, default="NoEntry", **kwargs):
        value = self.getSection(sSection)._getSectionVar(sVarName, default, **kwargs)

        if isinstance(value, basestring):

            sSectionSet = set(_SECTION_RGX.findall(value))
            if sSectionSet:
                sections = dict((s, getattr(self._pyobj, s)) for s in sSectionSet)
                return value.format(**sections)

        return value

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

    def _sectionHasVar(self, sVarName):
        return hasattr(self._pyobj, sVarName)

    def loadSections(self):

        sections = self.__sections

        for sSection, sectionCls in self.listSections():

            parser = PyConfParser(sectionCls)
            sections[sSection] = parser

            sAliasList = getattr(sectionCls, "aliases", ())
            for sAlias in sAliasList:

                if sAlias in sections:
                    raise RuntimeError("Section alias already used: '{}'".format(sAlias))

                sections[sAlias] = parser

    def listSections(self):
        return listClassesFromModule(self._pyobj.__name__)

    def getSection(self, sSectionName):

        sections = self.__sections
        try:
            return sections[sSectionName]
        except KeyError:
            msg = (u"<{}> No such section: '{}'.\n\nTry: {}"
                   .format(self, sSectionName, sorted(sections.iterkeys())))
            raise EnvironmentError(msg)

    def formatedErrors(self, sErrorList):
        return 'Failed initializing {0}: \n\t{1}'.format(self, "\n\t".join(sErrorList))

    def __repr__(self):

        try:
            sRepr = ("{0}({1})".format(self.__class__.__name__, self._pyobj.__name__))
        except:
            sRepr = object.__repr__(self)

        return sRepr
