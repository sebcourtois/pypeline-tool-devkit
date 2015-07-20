
import os.path as osp
from pytd.util.external.uicutils import compileUiDirToPyDir
import pytd.gui.ui

compileUiDirToPyDir(osp.dirname(__file__), osp.dirname(pytd.gui.ui.__file__))