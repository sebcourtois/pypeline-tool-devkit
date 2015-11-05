
import os
import sys

from pytd.util.fsutils import pathJoin

def currentMayapy():

    if sys.platform == "win32":
        p = pathJoin(os.environ["MAYA_LOCATION"], "bin", "mayapy.exe")
    else:
        raise NotImplementedError("Platform not supported yet: '{}'".format(sys.platform))

    if not os.path.exists(p):
        raise EnvironmentError("Could not found Maya's python interpreter: '{}'"
                               .format(p))

    return p
