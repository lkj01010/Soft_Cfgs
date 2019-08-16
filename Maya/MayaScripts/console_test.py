import sys
import os
import posixpath
import subprocess
import xml.dom.minidom as dom
import maya.OpenMaya as om
import maya.OpenMayaMPx as ompx
import maya.OpenMayaUI as omui
import pymel.core as pmc
import maya.cmds as cmds
import json
import pdb


def get_object_shaderset(obj):
    shaders, sg = [], None
    sgs = obj.shadingGroups()
    if sgs:
        sg = sgs[0]
        for atrname in ('surfaceShader', 'miMaterialShader'):
            atr = getattr(sg, atrname, None)
            shaders.extend(atr.connections()) if atr else None
            pdb.set_trace()
    return shaders, sg

res = [x.node() for x in pmc.selected()]
shape = res[0].getShape()
t = type(shape)

# ss = get_object_shaderset(res[0])
# print ss

# print t
#
# sgs = pmc.ls(typ=pmc.nt.ShadingEngine)
# print sgs
#
# cns = sgs[1].dagSetMembers.connections()
# print cns