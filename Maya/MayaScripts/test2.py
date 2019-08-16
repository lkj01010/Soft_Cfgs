import os, sys
import pymel.core as pmc

str = 'feffff__221@xx.vvv'
str2 = 'xxxxx@2222.fff'
str3 = 'xxx__@.xjf'
str4 = 'xxxx__333.fbx'

xxx = str.split('__')
xxx2 = str2.split('__')

class WorkflowError(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)

def ClearVerString(filename):
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


bbb = ClearVerString(str)

ccc = ClearVerString(str2)

ddd = ClearVerString(str3)

eee = ClearVerString(str4)


a = 1
b = 2
c = a + b
