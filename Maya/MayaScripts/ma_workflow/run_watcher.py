import maya.standalone
maya.standalone.initialize(name='python')

import ma_workflow.fbx_utils as fu

inputDir = '/Users/Midstream/Documents/Temp/testConvert'
outputDir = '/Users/Midstream/Documents/Temp/testConvert/out'

watcher = fu.FbxWatcher()
watcher.start(inputDir, outputDir, once=False)
