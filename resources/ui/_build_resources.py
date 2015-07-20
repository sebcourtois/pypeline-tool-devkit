
import os.path as osp
from pytk.util.external.uicutils import compileUiDirToPyDir
import pytk.core.ui

compileUiDirToPyDir(osp.dirname(__file__), osp.dirname(pytk.core.ui.__file__))