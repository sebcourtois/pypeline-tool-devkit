
from cgkit.mayaascii import MAReader
from pytd.util.fsutils import jsonWrite, jsonRead

class RefParser(MAReader):

    def __init__(self):
        MAReader.__init__(self)

    def init(self):

        self.topRefs = []
        self.deferredRefs = []
        self.loadedRefs = []

    def read(self, f):

        self.init()
        MAReader.read(self, f)

    def onCommand(self, cmd, args):

        if cmd == "createNode":
            self.abort()

        return MAReader.onCommand(self, cmd, args)

    def onFile(self, sFilePath, opts):

        sFilePath = sFilePath.replace("//", "/").strip('"')

        if "reference" in opts:
            self.topRefs.append(sFilePath)

        elif "deferReference" in opts:
            self.deferredRefs.append(sFilePath)

    def end(self):
        #print "aborted at line {0}".format( self.linenr )
        self.loadedRefs = list(set(f for f in self.topRefs if f not in self.deferredRefs))

    def save(self, sFilePath):

        exportDct = dict((k, v) for (k, v) in vars(self).iteritems() if k in ("topRefs", "deferredRefs", "loadedRefs"))
        jsonWrite(sFilePath, exportDct)

    def load(self, sFilePath):

        loadedVars = jsonRead(sFilePath)
        for sName in loadedVars.iterkeys():
            getattr(self, sName)

        self.__dict__.update(loadedVars)
