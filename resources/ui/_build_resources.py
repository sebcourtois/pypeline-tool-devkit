
import os.path as osp
from pytd.util.external.uicutils import compileUiDirToPyDir
import pytd.core.ui

compileUiDirToPyDir(osp.dirname(__file__), osp.dirname(pytd.core.ui.__file__))