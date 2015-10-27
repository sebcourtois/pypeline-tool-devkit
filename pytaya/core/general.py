
import pymel.core
from pytd.util.sysutils import argToTuple
pm = pymel.core

import maya.cmds
mc = maya.cmds


def lsNodes(*args, **kwargs):

    bAsNodeName = kwargs.pop('nodeNames', False)

    bPrune = False
    pruneKwargs = {}
    for k in kwargs.keys():

        if k.startswith("not_"):
            v = kwargs.pop(k)
            pruneKwargs[k.split("not_", 1)[1]] = v

            if (not bPrune) and v:
                bPrune = True

    _lsCmd = pm.ls
    if (bPrune or bAsNodeName):
        _lsCmd = mc.ls
        args = tuple(pynodeToStr(arg) for arg in args)

    nodeList = listForNone(_lsCmd(*args, **kwargs))
    if not nodeList:
        return nodeList

    if bPrune:
        nodeList = pruneNodeList(nodeList, **pruneKwargs)
        if not bAsNodeName:
            return list(pm.PyNode(n) for n in nodeList)

    return nodeList

def pruneNodeList(in_nodeList, **kwargs):

    if not in_nodeList:
        return in_nodeList

    seqType = type(in_nodeList)

    nodeList = argToTuple(in_nodeList)

    _mod = mc if isinstance(nodeList[0], basestring) else pm

    for kwarg, value in kwargs.iteritems():

        if not value:
            continue

        junkNodes = set(_mod.ls(nodeList, **{kwarg:value}))
        if junkNodes:
            nodeList = tuple(n for n in nodeList if n not in junkNodes)

    return seqType(nodeList)

def listForNone(arg):
    return [] if arg is None else arg

def argToStr(arg, bNodeName=True):

    if isinstance(arg, str):
        return arg
    elif arg is None:
        return ""
    elif isinstance(arg, pm.PyNode):
        return arg.nodeName() if bNodeName else arg.name()
    elif isinstance(arg, pm.Attribute):
        return arg.name()
    else:
        return str(arg)

def pynodeToStr(arg):

    if isinstance(arg, (tuple, list, set)):
        return tuple(argToStr(a, False) for a in arg)
    else:
        return argToStr(arg)
