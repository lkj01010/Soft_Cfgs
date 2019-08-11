import logging

import maya.cmds as cmds

logging.info('Maya`s userSetup.py')

if not cmds.commandPort(':4434', q=True):
    cmds.commandPort(n=':4434')


