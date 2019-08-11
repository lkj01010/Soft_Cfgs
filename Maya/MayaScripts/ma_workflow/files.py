import maya.cmds as cmds
import os.path

projectDirectory = cmds.workspace(q=True, rd=True)
if os.path.exists(projectDirectory+"scripts"):
    print (projectDirectory+"scripts")
else:
    print "Current Workspace doesnt have Scriprs folder"