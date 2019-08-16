# -*- coding: UTF-8 -*-

import maya.cmds as cmds
import os.path
import time
import sys
import threading
import maya.OpenMaya as om
import maya.OpenMayaMPx as ompx
import maya.OpenMayaUI as omui
import pymel.core as pmc
import maya.cmds as cmds
import maya.mel as mm
import com


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


# 在导出带有引用模型的文件时，这个函数导出的FBX的节点是第二层之后的[Bip001 Footsteps, Bip001 Pelvis]
# 而从maya ui中导出的FBX，节点是 第一层的Bip001。还好Unity只可以支持从第二层开始。
def export_fbx_ani_bip(mapath):
    cmds.select(clear=True)
    # joints = cmds.ls(type="joint")
    # cmds.select(joints)
    cmds.select("Bip*", hierarchy=True)

    mm.eval('FBXResetExport')
    mm.eval('FBXExportAnimationOnly -v true')
    mm.eval('FBXExportBakeComplexAnimation -v true')

    # mm.eval('FBXExportSmoothingGroups -v false')
    # mm.eval('FBXExportSmoothMesh -v false')
    mm.eval('FBXExportInputConnections -v false')
    # mm.eval('FBXExportInstances -v false')
    # mm.eval('FBXExportReferencedAssetsContent -v false')

    mm.eval('FBXExport -f "' + mapath + '" -s')
    # mm.eval('FBXExport -f "' + path + '"')


def export_fbx_model(mapath):
    cmds.select(clear=True)
    # cmds.select(all=True)

    objs = cmds.ls(type=('geometryShape', 'joint'))
    cmds.select(objs)

    mm.eval('FBXResetExport')
    mm.eval('FBXExportAnimationOnly -v false')
    mm.eval('FBXExportBakeComplexAnimation -v false')

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


class FbxWatcher(object):

    def __init__(self):
        self._running = False
        self._timer = None

        self.inDir = ''
        self.outDir = ''

    # def _convert_fbx(self):
    #
    #     if os.path.isdir(self.inDir) and \
    #             os.path.isdir(self.outDir):
    #
    #         for filename in os.listdir(self.inDir):
    #             filepath = os.path.join(self.inDir, filename)
    #             if os.path.isfile(filepath):
    #                 print '<FbxWatcher> inFbx=' + filepath
    #                 fu.clear_and_import_fbx(filepath)
    #                 fu.export_fbx_model(os.path.join(self.outDir, filename))
    #                 print '<FbxWatcher> success convert, out=', filepath
    #
    #     if self._running:
    #         t = threading.Timer(2, self._convert_fbx)
    #         t.start()
    #         print 'timer go'
    #
    #     else:
    #         print '<FbxWatcher> success convert'

    def _convert_fbx_2(self, once):
        while self._running:
            if os.path.isdir(self.inDir) and \
                    os.path.isdir(self.outDir):

                for filename in os.listdir(self.inDir):

                    filepath = os.path.join(self.inDir, filename)
                    if os.path.isfile(filepath):
                        clear_and_import_fbx(filepath)

                        filename_without_ver = com.cut_ver_string(filename)
                        final_filename = os.path.join(self.outDir, filename_without_ver)
                        if filename.find('@') != -1:
                            export_fbx_ani_bip(final_filename)
                        else:
                            export_fbx_model(final_filename)

                        # cmds.file(final_filename, force=True, save=True, options='v=1;p=17', type='mayaBinary')
                        print 'finish ------> ' + filename
                        os.remove(filepath)

            if once:
                return
            time.sleep(2)

    def start(self, inDir, outDir, once):
        self.inDir = inDir
        self.outDir = outDir

        print 'From -----> ' + inDir
        print 'To   -----> ' + outDir

        self._running = True
        self._convert_fbx_2(once)

        # t = threading.Thread(target=self._convert_fbx_2)
        # t.start()
        # t.join()

    def stop(self):
        self._running = False
        # try:
        #     pass
        # except Exception, e:
        #     pmc.warning('<fbx_transfer> %s' % e)
        # pass
