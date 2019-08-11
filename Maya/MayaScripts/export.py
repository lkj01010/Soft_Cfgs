# -*- coding: UTF-8 -*-
import maya.cmds as cmds
import maya.mel as mm


def export_fbx_ani(path):
    joints = cmds.ls(type="joint")
    cmds.select(joints)

    mm.eval('FBXExportAnimationOnly -v true')
    mm.eval('FBXExport -f "' + path + '" -s')
    # mm.eval('FBXExport -f "' + path + '"')


path = "/Users/Midstream/Documents/maya/projects/default/scenes/190802/Glacial@Glacial_Attack_output.FBX"


# exportFbxAni(path)


def export_fbx_model(path):
    cmds.select(all=True)

    mm.eval('FBXExportBakeComplexAnimation -v false')
    # mm.eval('FBXExportBakeResampleAnimation -v false')
    # mm.eval('FBXExportConstraints -v false')
    #
    # mm.eval('FBXExportCacheFile -v false')
    # mm.eval('FBXExportCameras -v false')
    # mm.eval('FBXExportEmbeddedTextures -v false')
    # mm.eval('FBXExportHardEdges -v false')
    # mm.eval('FBXExportInAscii -v false')
    # mm.eval('FBXExportLights -v false')
    #
    # mm.eval('FBXExportShapes -v false')
    #
    # mm.eval('FBXExportSmoothingGroups -v false')
    # mm.eval('FBXExportSmoothMesh -v false')
    # mm.eval('FBXExportInputConnections -v false')
    # mm.eval('FBXExportInstances -v false')
    # mm.eval('FBXExportReferencedAssetsContent -v false')
    # mm.eval('FBXExportTangents -v false')
    # mm.eval('FBXExportTangents -v false')

    # note: 不要用 全部导出，而要导出选择 -s, 否则有些选项会无效，比如烘焙动画等
    mm.eval('FBXExport -f "' + path + '" -s')


path = "/Users/Midstream/Documents/maya/projects/default/scenes/190802/Glacial_output.FBX"
# meshes = cmds.ls(type="mesh")
# cmds.select(meshes[0])
export_fbx_model(path)
