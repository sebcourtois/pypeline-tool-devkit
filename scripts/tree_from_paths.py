
import os.path as osp
from collections import OrderedDict

from pytd.util.fsutils import iterPaths, pathSplitDirs, pathJoin

srcPaths = tuple(iterPaths(r"C:\Users\sebcourtois\Documents"))
#srcPaths = ["A/B/C", "A/C/D", "A/C/D/E", "A/C/D/F", "A/B/D/F", "A/A/D/F", "A/C/D/G"]

def recurseTree(tree, path, paths):

    for child, children in tree.iteritems():

        print child

        p = pathJoin(path, child)

        if children:
            recurseTree(children, p, paths)
        else:
            paths.append(p)

tree = OrderedDict()
for p in srcPaths:

    dirs = pathSplitDirs(p)

    children = tree
    for i, d in enumerate(dirs):

        if d not in children:
            nxtChilds = OrderedDict()
            children[d] = nxtChilds
        else:
            nxtChilds = children[d]

        children = nxtChilds

outPaths = []
recurseTree(tree, "", outPaths)

#for srcPath, outPath in zip(srcPaths, outPaths):
#
#    print "\n", srcPath, "\n", outPath
#    print osp.normcase(srcPath) == osp.normcase(outPath)
