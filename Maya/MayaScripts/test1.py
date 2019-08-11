import maya.mel as Mm

strDir = "/Users/Midstream/Documents/maya/projects/default/scenes/190802/Glacial@Glacial_Attack.FBX"

Mm.eval('string $strDir = `python "strDir"`;')

# Mm.eval('FBXImportMode -v Add')
# Mm.eval('FBXImportMode -v Exmerge')
# Mm.eval('FBXImportMergeAnimationLayers -v true')
# Mm.eval('FBXImportProtectDrivenKeys -v true')
# Mm.eval('FBXImportConvertDeformingNullsToJoint -v true')
# Mm.eval('FBXImportMergeBackNullPivots -v false')
# Mm.eval('FBXImportSetLockedAttribute -v true')
# Mm.eval('FBXImportConstraints -v false')

# Mm.eval('FBXImport -f $strDir')

# Mm.eval('file -import -type "FBX"  -ignoreVersion -ra true -mergeNamespacesOnClash false -namespace "Glacial_Glacial_Attack" -options "fbx"  -pr  -importFrameRate true  -importTimeRange "override" "/Users/Midstream/Documents/maya/projects/default/scenes/190802/Glacial@Glacial_Attack.FBX";')

import maya.cmds as cmds

# cmds.file(strDir, i=True, type="FBX", ignoreVersion=True, ra=True, options="fbx", pr=True,
#           importFrameRate=True, importTimeRange="override")

outFile = "/Users/Midstream/Documents/maya/projects/default/scenes/190807/testOutFbx.fbx"
# cmds.file(outFile, force=True, type="FBX export", options="fbx", pr=True, ea=True)
cmds.file(outFile, force=True, type="FBX export", options="v=1", pr=True, ea=True)

import threading

time = 5

def func_timer():
    global time
    time -= 1
    if time > 0:
        print("hello")


timer = threading.Timer(2, func_timer)
timer.start()


import mid

mid.import_fbx("/Users/Midstream/Documents/maya/projects/default/scenes/190802/Glacial@Glacial_Attack.FBX")
