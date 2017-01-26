
import re
import inspect as insp
from copy import copy, deepcopy

from pytd.util.sysutils import listClassesFromModule
from pytd.util.fsutils import pathJoin, addEndSlash
from pytd.util.strutils import findFmtFields
from pytd.util.logutils import logMsg

_SECTION_REXP = re.compile(r"{([\w]+)\.")

def getattr_(pyobj, sAttr, *default):

    if default:
        return pyobj.__dict__.get(sAttr, default[0])
    else:
        return pyobj.__dict__[sAttr]

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
        self.name = pyobj.__name__

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

    def _checkVar(self, sVarName, expectedType, out_sErrorMsgList, **kwargs):

        bDeepCopy = kwargs.pop("deepCopy", False)
        defaultValue = kwargs.pop("default", "NoEntry")

        bSetVar = False
        pyobj = self._pyobj

        try:
            value = getattr(pyobj, sVarName)
        except AttributeError:
            if defaultValue == "NoEntry":
                out_sErrorMsgList.append('"{0}" : Missing'.format(sVarName))
                return
            else:
                value = defaultValue
                bSetVar = True

        if not isinstance(value, expectedType):
            msg = u'"{0}": Expected {1}, got {2}'.format(sVarName, expectedType, type(value))
            out_sErrorMsgList.append(msg)
            return

        if bDeepCopy:
            copiedValue = deepcopy(value)
        else:
            copiedValue = copy(value)

        if bSetVar:
            setattr(pyobj, sVarName, copiedValue)

        return copiedValue

    def checkPredefVars(self, predefVarParams):

        if not predefVarParams:
            return

        for sVarName, varParams in predefVarParams:
            self._checkVar(sVarName, varParams["type"], self._errosOnInit,
                           default=varParams.get("default", "NoEntry"))

    def recurseTreeVars(self, treeDct, sStartPath, parentConf=None):

        pyobj = parentConf._pyobj if parentConf else self._pyobj

        for sDirVar, childDct in treeDct.iteritems():

            if "->" in sDirVar:
                sDirName, sVarName = sDirVar.split("->", 1)
            else:
                sDirName = sDirVar
                sVarName = ""

            sCurPath = pathJoin(sStartPath, sDirName.strip())

            if sVarName:
                sVarName = sVarName.strip()

                sPath = pyobj.__dict__.get(sVarName, None)
                if sPath is None:

                    sPath = sCurPath

#                    if '@' in sPath:
#                        tokens = {}
#                        for f in set(findFmtFields(sPath)):
#                            if '@' not in f:
#                                continue
#                            v, k = f.split('@')
#                            tokens[k.strip()] = v.strip()
#
#                            sPath = sPath.replace(f, k)
#
#                        setattr(pyobj, sVarName + "_tokens", tokens)

                    if isinstance(childDct, dict):
                        sPath = addEndSlash(sPath)
                    
                    setattr(pyobj, sVarName, sPath)

                    sPathVarList = pyobj.__dict__.get("all_tree_vars", [])
                    sPathVarList.append(sVarName)
                    setattr(pyobj, "all_tree_vars", sPathVarList)

                else:
                    msg = u'"{0}" :  Already defined to "{1}"'.format(sVarName, sPath)
                    self._errosOnInit.append(msg)
                    continue

            if childDct:
                self.recurseTreeVars(childDct, sCurPath, parentConf)

    def declareVarsFromTree(self):

        for sTreeVar in dir(self._pyobj):
            if sTreeVar.endswith("_tree"):
                self.recurseTreeVars(getattr(self._pyobj, sTreeVar), "")

    def hasVar(self, sSection, sVarName):
        return self.getSection(sSection)._sectionHasVar(sVarName)

    def getVar(self, sSection, sVarName, default="NoEntry", **kwargs):

        bResVars = kwargs.pop("resVars", True)
        inTokens = kwargs.pop("tokens", {})

        currConfobj = self.getSection(sSection)
        value = currConfobj._getSectionVar(sVarName, default, **kwargs)

        if not isinstance(value, basestring):
            return value

        sFieldSet = set(findFmtFields(value))
        if not sFieldSet:
            return value

        #print "\n", "raw value:", value, sFieldSet

        fields = copy(getattr(currConfobj._pyobj, sVarName + "_tokens", None))
        if not fields:
            fields = {}

            for sField in sFieldSet:
                sToken = ""
                sValue = sField
                if '@' in sField:
                    sValue, sToken = sField.split('@', 1)
                    sToken = sToken.strip()
                    sValue = sValue.strip()

                if '.' in sValue:

                    sFieldSection, sFieldAttr = sValue.split(".", 1)
                    if not sFieldSection:
                        sFieldSection = sSection

                    confobj = self.getSection(sFieldSection)
                    pyobj = confobj._pyobj

                    if sToken:
                        sValue = getattr(pyobj, sFieldAttr)
                    else:
                        fields[sFieldSection] = pyobj

                elif not sToken:
                    fields[sValue] = "{" + sValue + "}"

                if sToken:
                    value = value.replace(sField, sToken)
                    if bResVars:
                        fields[sToken] = sValue
                    else:
                        fields[sToken] = "{" + sToken + "}"

                #print sField, sValue, sToken
            if bResVars and fields:
                #print sVarName + "_tokens", fields
                setattr(currConfobj._pyobj, sVarName + "_tokens", copy(fields))
                setattr(currConfobj._pyobj, sVarName, value)

        elif not bResVars:
            return value

        if fields:
            if inTokens:
                fields = fields.copy()
                fields.update(inTokens)
            return value.format(**fields)

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

        return deepcopy(value)

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

    def hasSection(self, sSection):
        return sSection in self.__sections

    def formatedErrors(self, sErrorList):
        return 'Failed initializing {0}: \n\t{1}'.format(self, "\n\t".join(sErrorList))

    def __repr__(self):

        try:
            sRepr = ("{0}({1})".format(self.__class__.__name__, self.name))
        except:
            sRepr = object.__repr__(self)

        return sRepr
