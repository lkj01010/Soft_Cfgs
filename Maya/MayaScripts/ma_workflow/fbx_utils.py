# -*- coding: UTF-8 -*-
import maya.cmds as cmds
import maya.mel as mm


def clear_and_import_fbx(fbxpath):
    cmds.select(all=True)
    cmds.delete()

    mm.eval('FBXImportMode -v Add')
    # Mm.eval('FBXImportMode -v Exmerge')
    mm.eval('FBXImportCameras -v false')
    # mm.eval('FBXImportConstrains -v true')
    # FBXImportConvertUnitString [mm|dm|cm|m|km|In|ft|yd|mi];
    mm.eval('FBXImportConvertUnitString cm')
    # 开启时，动画无法导入
    mm.eval('FBXImportProtectDrivenKeys -v false')
    mm.eval('FBXImportConvertDeformingNullsToJoint -v false')
    mm.eval('FBXImportMergeBackNullPivots -v true')
    mm.eval('FBXImportMergeAnimationLayers -v true')
    mm.eval('FBXImportSetLockedAttribute -v true')

    mm.eval('FBXImport -f "' + fbxpath + '"')


def export_fbx_ani(mapath):
    joints = cmds.ls(type="joint")
    cmds.select(joints)

    mm.eval('FBXResetExport')
    mm.eval('FBXExportAnimationOnly -v true')
    mm.eval('FBXExportBakeComplexAnimation -v true')
    mm.eval('FBXExport -f "' + mapath + '" -s')
    # mm.eval('FBXExport -f "' + path + '"')


def export_fbx_model(mapath):
    cmds.select(all=True)

    mm.eval('FBXResetExport')
    mm.eval('FBXExportAnimationOnly -v false')

    # mm.eval('FBXExportConstraints -v false')

    # mm.eval('FBXExportCacheFile -v false')
    # mm.eval('FBXExportCameras -v false')
    # mm.eval('FBXExportEmbeddedTextures -v false')
    # mm.eval('FBXExportHardEdges -v false')
    # mm.eval('FBXExportInAscii -v false')
    # mm.eval('FBXExportLights -v false')

    mm.eval('FBXExportShapes -v true')
    mm.eval('FBXExportSkins -v true')
    mm.eval('FBXExportSkeletonDefinitions -v false')

    # mm.eval('FBXExportShapes -v true')
    # mm.eval('FBXExportShapes -v true')
    #
    # mm.eval('FBXExportSmoothingGroups -v false')
    # mm.eval('FBXExportSmoothMesh -v false')
    # mm.eval('FBXExportInputConnections -v false')
    # mm.eval('FBXExportInstances -v false')
    # mm.eval('FBXExportReferencedAssetsContent -v false')
    # mm.eval('FBXExportTangents -v false')
    # mm.eval('FBXExportTangents -v false')

    # note: 不要用 全部导出，而要导出选择 -s, 否则有些选项会无效，比如烘焙动画等
    mm.eval('FBXExport -f "' + mapath + '" -s')

# cmds.file(force=True, new=True)

def export_humanik_ani(mapath):
