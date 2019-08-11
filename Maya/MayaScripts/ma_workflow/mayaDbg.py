import sys

sys.path.append('/Applications/PyCharm.app/Contents/debug-eggs/pydevd-pycharm.egg')

import pydevd

try:
    print("trace start")
    pydevd.settrace('localhost', port=4434, stdoutToServer=True, stderrToServer=True)
    print ("trace stop")
except:
    pydevd.stoptrace()
    print ("trace stop")
