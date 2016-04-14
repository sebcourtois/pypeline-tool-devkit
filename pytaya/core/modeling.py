
import maya.cmds as mc
import pymel.core as pm

from pytd.util.logutils import logMsg
from pytaya.core.general import lsNodes
from pytaya.util.sysutils import withSelectionRestored
from pytaya.util import apiutils as myapi

@withSelectionRestored
def bakeDiffuseToVertexColor(**kwargs):

    bOnRefs = kwargs.pop("onReferences", kwargs.pop("onRefs", False))
    fAmbient = kwargs.pop("ambient", 1.0)

    sCamShape = ""
    if mc.about(batch=True):
        sCamShape = kwargs["camera"]

    if "meshes" not in kwargs:
        sMeshList = lsNodes(sl=True, dag=True, ni=True, type="mesh",
                            not_referencedNodes=not bOnRefs, nodeNames=True)
        if not sMeshList:
            logMsg("No meshes found in selection !" , warning=True)
            return False
    else:
        sMeshList = kwargs.pop("meshes")
        if not sMeshList:
            return False

    mc.polyOptions(sMeshList, colorShadedDisplay=False)

    sLightList = tuple(sLight for sLight in mc.ls(type=mc.listNodeTypes('light'))
                                    if myapi.getDagPath(sLight).isVisible())
    for sLight in sLightList:
        try:
            mc.setAttr(sLight + ".visibility", False)
        except RuntimeError as e:
            pm.displayWarning(e)

    ambLight = pm.shadingNode("ambientLight", asLight=True)
    ambLight.setAttr("intensity", fAmbient)
    ambLight.setAmbientShade(0.0)
    ambLight.setAttr("color", (1.0, 1.0, 1.0))
    ambLight.setAttr("shadowColor", (0.0, 0.0, 0.0))
    ambLight.setAttr("useRayTraceShadows", False)

    pm.refresh()

    ##Storing if exist, reflectivity connection or value before applying the bakeTexture,
    ##as it could affects the "rendering/baking" aspect of the object.
    ##After bake, reapply the value.
    oReflDct = {}
    for oMat in lsNodes(type=mc.listNodeTypes('shader', ex="texture"), not_referencedNodes=not bOnRefs):
        if oMat.hasAttr("reflectivity"):
            oInputs = oMat.attr("reflectivity").inputs(sourceFirst=True, c=True, plugs=True)
            if oInputs:
                oReflDct[oMat] = dict(oInputs)
                pm.disconnectAttr(*oInputs)
            else:
                oReflDct[oMat] = oMat.getAttr("reflectivity")
            oMat.setAttr("reflectivity", 0)


    if sCamShape:
        sMeshList.append(sCamShape)

    try:
        mc.polyGeoSampler(sMeshList,
                          ignoreDoubleSided=True,
                          scaleFactor=1.0,
                          shareUV=True,
                          colorDisplayOption=True,
                          colorBlend="overwrite",
                          alphaBlend="overwrite",
                          flatShading=False,
                          lightingOnly=False,
                          averageColor=True,
                          clampAlphaMin=1.0,
                          clampAlphaMax=1.0)

        mc.polyOptions(sMeshList, colorMaterialChannel="ambientDiffuse")

    finally:

        for sLight in sLightList:
            try:
                mc.setAttr(sLight + ".visibility", True)
            except RuntimeError as e:
                pm.displayWarning(e)

        for oMat, oValues in oReflDct.items():
            if isinstance(oValues, dict):
                for k, v in oValues.items():
                    pm.connectAttr(k, v)
            else:
                oMat.setAttr("reflectivity", oValues)

        if ambLight:
            pm.delete(ambLight)

    return True

def disableVertexColorDisplay(**kwargs):

    bOnRefs = kwargs.pop("onReferences", kwargs.pop("onRefs", True))

    if "meshes" not in kwargs:
        sMeshList = lsNodes(sl=True, dag=True, ni=True, type="mesh",
                            not_referencedNodes=not bOnRefs, nodeNames=True)
        if not sMeshList:
            logMsg("No meshes found in selection !" , warning=True)
            return False
    else:
        sMeshList = kwargs.pop("meshes")
        if not sMeshList:
            return False

    pm.polyOptions(sMeshList, colorShadedDisplay=False)

    return True
