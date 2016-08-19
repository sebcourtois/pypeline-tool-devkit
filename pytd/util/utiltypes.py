

from collections import OrderedDict
from pytd.util.fsutils import pathSplitDirs, pathJoin, pathRelativeTo

class OrderedTree(OrderedDict):

    def __init__(self, *args, **kwargs):
        super(OrderedTree, self).__init__(*args, **kwargs)

    def iterPaths(self, parentPath="", rootPath=""):

        for sChild, children in self.iteritems():

            p = pathJoin(parentPath, sChild)

            bYield = True
            if rootPath:
                rp = pathRelativeTo(p, rootPath)
                if (rp == ".") or (".." in rp):
                    bYield = False

            if bYield:
                yield p

            for cp in children.iterPaths(p, rootPath):
                yield cp

    @classmethod
    def fromPaths(cls, paths):

        tree = cls()
        for p in paths:

            dirs = pathSplitDirs(p)

            children = tree
            for d in dirs:
                if d not in children:
                    nxtChilds = cls()
                    children[d] = nxtChilds
                else:
                    nxtChilds = children[d]

                children = nxtChilds

        return tree
