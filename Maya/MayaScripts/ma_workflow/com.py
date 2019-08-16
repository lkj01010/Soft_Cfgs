# -*- coding: UTF-8 -*-

import os
import maya.cmds as cmds


class WorkflowError(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


def cut_ver_string(filename):
    parts = filename.split('__')
    if len(parts) == 1:
        return filename
        pass
    elif len(parts) == 2:
        # with version
        post_parts = parts[1].split('@')
        if len(post_parts) == 1:
            # model file
            version_string, extend = post_parts[0].split('.')
            return parts[0] + '.' + extend
        elif len(post_parts) == 2:
            # animation file
            return parts[0] + '@' + post_parts[1]

    raise WorkflowError('<Workflow> Error filename = ' + filename)


def get_scene_name():
    fullpath = cmds.file(q=True, sn=True)
    dirname = os.path.dirname(fullpath)
    filename = os.path.basename(fullpath)
    raw_name, extension = os.path.splitext(filename)
    return fullpath, dirname, raw_name
