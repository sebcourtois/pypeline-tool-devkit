
import maya.cmds;mc = maya.cmds
import pymel.core;pm = pymel.core

from pytaya.core.general import listForNone
from pytd.util.logutils import logMsg
from pytd.util.sysutils import grouper


def fileNodesFromObjects(oObjList):
    return fileNodesFromShaders(shadersFromObjects(oObjList))

def fileNodesFromShaders(oMatList):

    oFileNodeList = set()
    for oMat in oMatList:
        oFileNodeList.update(oMat.listHistory(type="file"))

    return list(oFileNodeList)

def shadersFromObjects(objList, connectedTo=""):

    sAttrName = connectedTo

    if not objList:
        return []

    oMatSgList = shadingGroupsFromObjects(objList)

    oMatList = []
    for oMatSg in oMatSgList:
        sName = oMatSg.attr(sAttrName).name() if connectedTo else oMatSg.name()
        oMatList.extend(pm.ls(listForNone(mc.listConnections(sName, source=True,
                                                             destination=False)),
                              type=mc.listNodeTypes('shader', ex="texture")))
    return oMatList

def shadingGroupsFromObjects(objList):

    oShdGrpList = set()

    for obj in objList:

        oObj = obj if isinstance(obj, pm.PyNode) else pm.PyNode(obj)

        oShdGrpList.update(shadingGroupsForObject(oObj))

    return list(oShdGrpList)

def shadingGroupsForObject(oObj, warn=True):

    oShdGrpList = []
    oShape = None
    if isinstance(oObj, pm.general.MeshFace):
        indiceList = oObj.indices()
        for oShdEng in oObj.listHistory(type="shadingEngine"):
            if set(indiceList).intersection(set(oShdEng.members()[0].indices())):
                oShdGrpList.append(oShdEng)

    elif isinstance(oObj, pm.general.NurbsSurfaceFace):
        oShape = oObj.node()

    elif isinstance(oObj, pm.nt.Transform):
        oShape = oObj.getShape()

    elif isinstance(oObj, (pm.nt.Mesh, pm.nt.NurbsSurface)):
        oShape = oObj

    elif warn:
        logMsg("Can't get shading groups from {}".format(repr(oObj)) , warning=True)

    if not oShdGrpList:
        if oShape:
            oShdGrpList = oShape.shadingGroups()
            if not oShdGrpList:
                oShdGrpList = oShape.connections(type="shadingEngine")

    return oShdGrpList

def conformShadingNetworkToNamespace(oMeshList, sNamespaceToMatch , **kwargs):

    bForce = kwargs.get("force", False)

    oShadingGroupMembersDct = {}
    oMatNotConformList = []

    for oShape in oMeshList:
#        print "\nfor shape: ", oShape
        oMatSGList = shadingGroupsForObject(oShape)
        for oMatSG in oMatSGList:
#            print "for shadingGroup: ", oMatSG

            oMatList = pm.ls(oMatSG.inputs(), type=mc.listNodeTypes('shader', ex="texture"))
            oMat = oMatList[0]

            ##ignore shadingGroups where materials are defaultNode
            if oMat.isDefaultNode():
                continue

            ##ignore shadingGroups where materials are already in namespace to match
            sMatNamespace = oMat.namespace()
#            print "sMatNamespace", sMatNamespace
#            print "sNamespaceToMatch", sNamespaceToMatch
            if sMatNamespace == sNamespaceToMatch:
                continue
            else:
                oMatNotConformList.append(oMat)

            oMembers = oMatSG.members()
            for oMember in oMembers:
#                print "member :", oMember

                if oMember.node() == oShape:
                    oShadingGroupMembersDct.setdefault(oMatSG, []).append(oMember)

#    for k, v in oShadingGroupMembersDct.iteritems():
#        print "for shadingGroup: ", k, ", specific members are: ", v

    if oMatNotConformList:
        if bForce:
            pass
        else:
            result = pm.confirmDialog(title='Materials not conform to Namespace...'
                                    , message="Found materials not conform to Namespace,\nCopy Shading Network, Conform to Namespace & Assign ?"
                                    , button=["OK", 'Cancel']
                                    , defaultButton='Cancel'
                                    , cancelButton='Cancel'
                                    , dismissString='Cancel')

            if result == "Cancel":
                pm.warning("Materials Namespace conformation cancelled.")
                return bForce
            else:
                bForce = True

    else:
        if sNamespaceToMatch:
            logMsg('Materials already conformed to Namespace: "{0}"'.format(sNamespaceToMatch) , warning=True)
        return bForce


    ##Force current namespace to the one to match to duplicate in this namespace
    mc.namespace(set=":")
    mc.namespace(set=sNamespaceToMatch if sNamespaceToMatch else ":")

    oMatNotConformList = []

    oShapeAssignedList = []
    for oMatSG, oMembers in oShadingGroupMembersDct.iteritems():

        oNewMatSGs = pm.duplicate(oMatSG, rr=True, un=True)
        oNewMatSG = oNewMatSGs[0]
#        print "old shadingGroup: ", oMatSG
#        print "new shadingGroup: ", oNewMatSGs[0]
#        print "oMembers", oMembers
#        print oMembers[0]
        for oMember in oMembers:
            oShape = oMember.node()
            if oShape not in oShapeAssignedList:
                oShapeAssignedList.append(oShape)
                try:
                    pm.sets(oNewMatSG, e=True, forceElement=oShape)
                    logMsg('Material "{0}" assigned first to: "{1}"'.format(oNewMatSG, oShape) , warning=True)
                except:
                    logMsg('Could not assign material "{0}" first to: "{1}"'.format(oNewMatSG, oShape) , warning=True)

        try:
            pm.sets(oNewMatSG, e=True, forceElement=oMembers)
            logMsg('Material "{0}" assigned to: "{1}"'.format(oNewMatSG, oMembers) , warning=True)
        except:
            logMsg('Could not assign material "{0}" to: "{1}"'.format(oNewMatSG, oMembers) , warning=True)

    mc.namespace(set=":")

    return bForce

def transferUvAndShaders(oSrcGrp, oDestGrp):

    notCompatibleShapeList = []

    sSourceNameSpace = oSrcGrp.namespace()

    notFoundList = []
    transferList = []
    oTargetList = pm.ls(oDestGrp, dag=True, tr=True)
    #searchCount = len(oTargetList)

    for oTargetXfm in oTargetList:

        oShape = oTargetXfm.getShape(ni=True)
        if isinstance(oShape, pm.nt.Mesh):
            sXfmName = oTargetXfm.nodeName()
            sSourceName = sSourceNameSpace + sXfmName
            oSourceXfm = pm.PyNode(sSourceName)
            if oSourceXfm:
                transferList.append((oSourceXfm, oTargetXfm))
#                print oSourceXfm, oTargetXfm
            else:
                notFoundList.append(oTargetXfm)
                print 'No match found for "{0}"'.format(sXfmName)

        print "Searching... {0}".format(oTargetXfm.nodeName())

#    oSet = fncTools.checkSet("noMatchFound")
#    if notFoundList:
#        pm.sets(oSet, addElement=notFoundList)

    result = pm.confirmDialog(title='Transfer Uvs',
                                message='Found {0}/{1} mismatches :'.format(len(notFoundList), len(transferList)),
                                button=['Ok', 'Cancel'],
                                defaultButton='Cancel',
                                cancelButton='Cancel',
                                dismissString='Cancel')

    if result == 'Cancel':
        return

    else :
        for oSourceXfm, oTargetXfm in transferList:
            oSourceShape = oSourceXfm.getShape(ni=True)

            oHistList = oTargetXfm.listHistory()
            oShapeList = pm.ls(oHistList, type="mesh")

            oTargetShape = None
            bShapeOrig = False

            oTargetCurrentShape = oTargetXfm.getShape(ni=True)

            if len(oShapeList) > 1:
                for oShape in oShapeList:
                    if oShape.getAttr("intermediateObject") and oShape.attr("worldMesh").outputs():
                        bShapeOrig = True
                        oShape.setAttr("intermediateObject", False)
                        oTargetShape = oShape
                        break
            else:
                oTargetShape = oTargetCurrentShape

            if oTargetShape:
                try:
                    print ('transferring uvs and shaders from "{0}" to "{1}"'
                           .format(oSourceShape, oTargetShape))

                    if oTargetCurrentShape.numVertices() != oSourceShape.numVertices():
                        notCompatibleShapeList.extend([oSourceShape, oTargetCurrentShape])

                    pm.transferAttributes(oSourceShape, oTargetShape, transferPositions=0,
                                          transferNormals=0, transferUVs=2, transferColors=2,
                                          sampleSpace=5, sourceUvSpace="map1", targetUvSpace="map1",
                                          searchMethod=3, flipUVs=0, colorBorders=1)

                    pm.transferShadingSets(oSourceShape, oTargetShape, sampleSpace=0, searchMethod=3)

                    pm.delete(oTargetShape, ch=True)
                finally:
                    if bShapeOrig:
                        oTargetShape.setAttr("intermediateObject", True)

            pm.select(clear=True)
            pm.select(oSourceShape, r=True)
            pm.select(oTargetCurrentShape, tgl=True)
            pm.transferShadingSets(sampleSpace=1, searchMethod=3)

#        oSet = fncTools.checkSet("Shapes_Without_Same_Topology")
#        if notCompatibleShapeList:
#            pm.sets(oSet, addElement=notCompatibleShapeList)
#            pm.select(notCompatibleShapeList)
#            pm.warning("The selected node's may have potentially problems on transferring uvs and materials.")

    return notFoundList, notCompatibleShapeList


def averageVertexColorsToMaterial(oMatList="NoEntry"):

    if oMatList == "NoEntry":
        oMatList = pm.selected()

    if not oMatList:
        logMsg("Nothing is selected. Select meshes to apply vertex color." , warning=True)
        return

    for oMat in oMatList:

        logMsg("Processing {0}".format(repr(oMat)))

        try:
            colorAttr = oMat.attr("color")
        except pm.MayaAttributeError:
            logMsg("\tNo color attribute found.")
            continue

        try:
            oSG = oMat.shadingGroups()[0]
        except IndexError:
            print "\tNo ShadingGroup found."
            continue

        oMemberList = oSG.members()
        if not oMemberList:
            logMsg("\tShadingGroup is empty.")
            continue

        pm.select(oMemberList, r=True)
        pm.mel.ConvertSelectionToVertices()
        sSelectedVerts = mc.ls(sl=True)
        pm.refresh()

        try:
            vtxColorList = tuple(grouper(3, mc.polyColorPerVertex(sSelectedVerts, q=True, rgb=True)))
        except:
            logMsg("\tNo vertex colors found.")
            continue

        numVtx = len(vtxColorList)
        rSum = 0.0
        gSum = 0.0
        bSum = 0.0
        for r, g, b in vtxColorList:
            rSum += r
            gSum += g
            bSum += b

        if rSum + gSum + bSum > 0.0:

            avrVtxColor = (rSum / numVtx, gSum / numVtx, bSum / numVtx)

            try:
                colorAttr.disconnect()
                colorAttr.set(avrVtxColor)
            except Exception, e:
                logMsg("\t{0}".format(e))

def duplicateShadersPerObject(oMatList):

    oNewMatList = []
    for oMat in oMatList:

        oShadEngList = oMat.outputs(type="shadingEngine")
        if not oShadEngList:
            continue

        oShadEng = oShadEngList[0]

        oShadEngMemberList = oShadEng.members()

        oMemberByGeoObjDct = {}

        for member in  oShadEngMemberList:
            oMesh = member.node() if isinstance(member, pm.MeshFace) else member
            oMemberByGeoObjDct.setdefault(oMesh, []).append(member)

        count = len(oMemberByGeoObjDct)
        if count <= 1:
            continue

        oMemberByGeoObjDct.popitem()

        for oShadingMembers in oMemberByGeoObjDct.itervalues():
            oNewMat = pm.duplicate(oMat, inputConnections=True)[0]
#            pm.select(oShadingMembers, replace=True)
#            pm.hyperShade(assign=oNewMat)
            oSG = pm.sets(renderable=True, noSurfaceShader=True, empty=True, name=oNewMat.nodeName() + "SG")
            oNewMat.attr("outColor") >> oSG.attr("surfaceShader")
            pm.sets(oSG, forceElement=oShadingMembers)

            oNewMatList.append(oNewMat)

    return oNewMatList
