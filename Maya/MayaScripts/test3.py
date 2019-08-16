import maya.cmds as cmds
import maya.mel as mm
import pymel.core as pmc


def export_fbx_model_111(mapath):
    pmc.select(clear=True)
    # cmds.select(all=True)

    objs = pmc.ls(type=('geometryShape', 'joint'))
    pmc.select(objs)

    mm.eval('FBXResetExport')
    mm.eval('FBXExportAnimationOnly -v false')
    mm.eval('FBXExportBakeComplexAnimation -v false')

    mm.eval('FBXExportShapes -v false')
    mm.eval('FBXExportSkins -v true')
    mm.eval('FBXExportSkeletonDefinitions -v false')

    mm.eval('FBXExportConstraints -v false')
    mm.eval('FBXExportCacheFile -v false')
    mm.eval('FBXExportCameras -v false')
    mm.eval('FBXExportEmbeddedTextures -v false')
    mm.eval('FBXExportHardEdges -v false')
    mm.eval('FBXExportInAscii -v false')
    mm.eval('FBXExportLights -v false')



    # mm.eval('FBXExportShapes -v true')
    # mm.eval('FBXExportShapes -v true')
    #
    mm.eval('FBXExportSmoothingGroups -v false')
    mm.eval('FBXExportSmoothMesh -v false')
    mm.eval('FBXExportInputConnections -v false')
    mm.eval('FBXExportInstances -v false')
    mm.eval('FBXExportReferencedAssetsContent -v false')
    mm.eval('FBXExportTangents -v false')
    # mm.eval('FBXExportTangents -v false')

    mm.eval('FBXExport -f "' + mapath + '" -s')


export_fbx_model_111('/Users/Midstream/Documents/Temp/testConvert/out/newModel.fbx')
