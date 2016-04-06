
import maya.cmds as mc
import pymel.core as pm

from pytd.util.logutils import logMsg
from pytaya.core.general import lsNodes
from pytaya.util.sysutils import withSelectionRestored
from pytaya.util import apiutils as myapi

@withSelectionRestored
def bakeDiffuseToVertexColor(in_objList="NoEntry", **kwargs):

    bIgnoreRef = kwargs.pop("ignoreReference", True)

    sMeshList = []
    if in_objList == "NoEntry":
        sMeshList = lsNodes(sl=True, dag=True, type="mesh", not_referencedNodes=bIgnoreRef, nodeNames=True)
    elif in_objList:
        sMeshList = lsNodes(in_objList, dag=True, type="mesh", not_referencedNodes=bIgnoreRef, nodeNames=True)

    if not sMeshList:
        logMsg("No meshes found in selection !" , warning=True)
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
    ambLight.setAttr("intensity", 1.0)
    ambLight.setAmbientShade(0.0)
    ambLight.setAttr("color", (1.0, 1.0, 1.0))
    ambLight.setAttr("shadowColor", (0.0, 0.0, 0.0))
    ambLight.setAttr("useRayTraceShadows", False)

    pm.refresh()

    ##Storing if exist, reflectivity connection or value before applying the bakeTexture,
    ##as it could affects the "rendering/baking" aspect of the object.
    ##After bake, reapply the value.
    oReflDct = {}
    for oMat in lsNodes(type=mc.listNodeTypes('shader', ex="texture"), not_referencedNodes=True):
        if oMat.hasAttr("reflectivity"):
            oInputs = oMat.attr("reflectivity").inputs(sourceFirst=True, c=True, plugs=True)
            if oInputs:
                oReflDct[oMat] = dict(oInputs)
                pm.disconnectAttr(*oInputs)
            else:
                oReflDct[oMat] = oMat.getAttr("reflectivity")
            oMat.setAttr("reflectivity", 0)

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

        pm.delete(ambLight)

    return True

def disableVertexColorDisplay(in_sSelList=None, **kwargs):

    bWarn = kwargs.pop("warning", True)

    if in_sSelList is None:
        sSelList = mc.ls(sl=True, dag=True, o=True)

    if bWarn and not sSelList:
        logMsg("Nothing is selected. Select meshes to remove vertex color." , warning=True)
        return

    sMeshList = pm.ls(sSelList, type="mesh", ni=True)
    if sMeshList:
        pm.polyOptions(sMeshList, colorShadedDisplay=False)
