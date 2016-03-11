

import os
import os.path as osp
import re
import fnmatch
import json
import stat
import hashlib

from distutils.file_util import copy_file

from .external import parse
from .sysutils import toUnicode, argToList
from .logutils import logMsg


def isDirStat(statobj):
    return stat.S_ISDIR(statobj.st_mode)

def isFileStat(statobj):
    return stat.S_ISREG(statobj.st_mode)

def pathNorm(p):
    return osp.normpath(p).replace("\\", "/")

def normCase(p):
    return osp.normcase(p).replace("\\", "/")

def pathAbs(p):
    return osp.abspath(p).replace("\\", "/")

def pathJoin(*args):
    try:
        p = osp.join(*args)
    except UnicodeDecodeError:
        p = osp.join(*tuple(toUnicode(arg) for arg in args))

    return pathNorm(p)

def pathResolve(p, recursive=True):

    rp = pathNorm(osp.expanduser(osp.expandvars(p)))

    if recursive and (rp != p) and re.findall(r'[%$]', rp):
        return pathResolve(rp)

    return rp

def pathSuffixed(sFileNameOrPath, *suffixes):

    sRootPath, sExt = osp.splitext(sFileNameOrPath)

    sJoinList = [sRootPath]
    sJoinList.extend(suffixes)

    return "".join(sJoinList) + sExt

def pathRelativeTo(*args):
    return pathNorm(osp.relpath(*args))

def pathParse(sPathFormat, sPath):

    fmtDirs = pathSplitDirs(sPathFormat)
    pDirs = pathSplitDirs(sPath)

    fmtLen = len(fmtDirs)
    pLen = len(pDirs)

    minLen = min(fmtLen, pLen)

    fmt = pathJoin(*fmtDirs[1:minLen])
    s = pathJoin(*pDirs[1:minLen])

    return parse.parse(fmt, s)

def pathReSub(pattern, repl, string, count=0, flags=0):

    if os.name == "nt":
        flags |= re.IGNORECASE

    return re.sub(pattern, repl, string, count, flags)

def pathStartsWith(sPath, sParentPath):

    sParentPath = normCase(pathAbs(sParentPath))
    sPathDirs = pathSplitDirs(normCase(pathAbs(sPath)))

    numDirs = len(pathSplitDirs(sParentPath))
    sAlignedPath = pathJoin(*sPathDirs[:numDirs])

    return sAlignedPath == sParentPath

def pathStripDrive(p):
    return pathJoin(*pathSplitDirs(p)[1:])

def pathSplitDirs(p):
    p = pathNorm(p)

    if p.startswith("//"):
        root, p = osp.splitunc(p)
    elif p.startswith("/"):
        dirs = p.split("/", 2)
        root, p = (dirs[1], "") if len(dirs) == 2 else dirs[1:]
        root = "/" + root
    else:
        root, p = osp.splitdrive(p)

    p = p.strip("/")

    res = [root + "/"] if root else []
    if p:
        res.extend(p.split("/"))

    return res


def ignorePatterns(*patterns):
    """Function that can be used as iterPaths() ignore parameters.

    Patterns is a sequence of glob-style patterns
    that are used to exclude files"""
    def _ignore_patterns(p, names):
        ignored_names = []
        for pattern in patterns:
            ignored_names.extend(fnmatch.filter(names, pattern))
        return set(ignored_names)
    return _ignore_patterns

def iterPaths(sRootDirPath, **kwargs):

    if not osp.isdir(sRootDirPath):
        raise ValueError('No such directory found: "{0}"'.format(sRootDirPath))

    bFiles = kwargs.pop("files", True)
    bDirs = kwargs.pop("dirs", True)
    bEmptyDirs = kwargs.pop("emptyDirs", True)
    bInterDirs = kwargs.pop("intermediateDirs", False)
    bRelPath = kwargs.pop("relative", False)

    bRecursive = kwargs.pop("recursive", True)

    ignoreDirsFunc = kwargs.get("ignoreDirs", None)
    ignoreFilesFunc = kwargs.get("ignoreFiles", None)

    keepFilesFunc = kwargs.get("keepFiles", None)

    for sDirPath, sDirNames, sFileNames in os.walk(sRootDirPath):

        if not bRecursive:
            del sDirNames[:] # don't walk further

        if ignoreDirsFunc is not None:
            sIgnoredDirs = ignoreDirsFunc(sDirPath, sDirNames)
            for sDir in sIgnoredDirs:
                try: sDirNames.remove(sDir)
                except ValueError: pass

        bOnly = False
        sKeepFiles = []
        if keepFilesFunc is not None:
            sKeepFiles = keepFilesFunc(sDirPath, sFileNames)
            #print "sKeepFiles", sKeepFiles, sFileNames
            bOnly = True

        sIgnoredFiles = []
        if ignoreFilesFunc is not None:
            sIgnoredFiles = ignoreFilesFunc(sDirPath, sFileNames)
            #print "sIgnoredFiles", sIgnoredFiles

        sKeptFileNames = sFileNames[:]

        for sFileName in sFileNames:

            if bOnly and (sFileName not in sKeepFiles):
                if bEmptyDirs:
                    sKeptFileNames.remove(sFileName)
                continue

            if sFileName in sIgnoredFiles:
                if bEmptyDirs:
                    sKeptFileNames.remove(sFileName)
                continue

            if bFiles:
                p = pathJoin(sDirPath, sFileName)
                yield p if not bRelPath else pathRelativeTo(p, sRootDirPath)

        if bDirs:

            p = pathNorm(sDirPath)
            if bRelPath:
                p = pathRelativeTo(p, sRootDirPath)

            bYieldDir = True
            if p == ".":
                bYieldDir = False
            elif not bInterDirs:
                bIsLeaf = (not sDirNames)
                bIsEmpty = bIsLeaf and (not sKeptFileNames)
                bYieldDir = bIsEmpty if bEmptyDirs else bIsLeaf

                #print sDirPath, bIsLeaf, bIsEmpty

            if bYieldDir:
                yield addEndSlash(p)

def addEndSlash(p):
    return p if p.endswith("/") else p + "/"

def delEndSlash(p):
    return p[:-1] if p.endswith("/") else p

def commonDir(sPathList):
    sDir = osp.commonprefix(sPathList)
    return sDir if (sDir[-1] in ("\\", "/")) else (osp.dirname(sDir) + "/")

def copyFile(sSrcPath, sDestPath, **kwargs):

    if osp.isdir(sDestPath):
        sDestPath = pathJoin(sDestPath, osp.basename(sSrcPath))

    if sameFile(sSrcPath, sDestPath):
        sMsg = u"Source and destination are the same file:"
        sMsg += u"\n    source:      ", sSrcPath
        sMsg += u"\n    destination: ", sDestPath
        raise EnvironmentError(sMsg)

    logMsg(u"\nCopying '{}'\n     to '{}'".format(sSrcPath, sDestPath))

    return copy_file(sSrcPath, sDestPath, **kwargs)

def sameFile(sSrcPath, sDestPath):
    # Macintosh, Unix.
    if hasattr(osp, 'samefile'):
        try:
            return osp.samefile(sSrcPath, sDestPath)
        except OSError:
            return False

    # All other platforms: check for same pathname.
    return (osp.normcase(osp.abspath(sSrcPath)) == osp.normcase(osp.abspath(sDestPath)))

def distribTree(in_sSrcRootDir, in_sDestRootDir, **kwargs):

    bDryRun = kwargs.get("dry_run", False)

    bPrintSrcOnly = kwargs.pop("printSourceOnly", False)
    sFilePathList = kwargs.pop("filePaths", "NoEntry")

    sReplaceExtDct = kwargs.pop("replaceExtensions", kwargs.pop("replaceExts", {}))
    if not isinstance(sReplaceExtDct, dict):
        raise TypeError('"replaceExtensions" kwarg expects {0} but gets {1}.'
                        .format(dict, type(sReplaceExtDct)))

    sEncryptExtList = kwargs.pop("encryptExtensions", kwargs.pop("encryptExts", []))
    if not isinstance(sEncryptExtList, list):
        raise TypeError('"encryptExtensions" kwarg expects {0} but gets {1}.'
                        .format(list, type(sEncryptExtList)))

    if sEncryptExtList:
        raise NotImplementedError, "Sorry, feature has been removed."
        # import cryptUtil
        sEncryptExtList = list(e.strip(".") for e in sEncryptExtList)

    sSrcRootDir = addEndSlash(pathNorm(in_sSrcRootDir))
    sDestRootDir = addEndSlash(pathNorm(in_sDestRootDir))

    if not osp.isdir(sSrcRootDir):
        raise ValueError, 'No such directory found: "{0}"'.format(sSrcRootDir)

    if not osp.isdir(sDestRootDir):
        print 'Creating destination directory: "{0}"'.format(sDestRootDir)
        if not bDryRun:
            os.makedirs(sDestRootDir)

    sCopiedFileList = []

    if sFilePathList == "NoEntry":

        raise NotImplementedError, "Sorry, but for now, you must provide a list of file paths to copy."

    else:

        sFilePathList = argToList(sFilePathList)
        sFilePathList.sort()

        srcRootDirRexp = re.compile("^" + sSrcRootDir, re.I)
        destRootDirRexp = re.compile("^" + sDestRootDir, re.I)

        # building destination directories
        sDestDirList = sFilePathList[:]

        iMaxPathLen = 0
        for i, sFilePath in enumerate(sFilePathList):

            sSrcDir = addEndSlash(pathNorm(osp.dirname(sFilePath)))

            sRexpList = srcRootDirRexp.findall(sSrcDir)
            if not sRexpList:
                raise RuntimeError, "File outside of source directory: {0}.".format(sSrcDir)

            sDestDirList[i] = sSrcDir.replace(sRexpList[0], sDestRootDir)

            iPathLen = len(srcRootDirRexp.split(sFilePath, 1)[1])
            if iPathLen > iMaxPathLen:
                iMaxPathLen = iPathLen

        iNumFiles = len(sFilePathList)
        iDoneFileCount = 0
        iCountLen = len(str(iNumFiles)) * 2 + 5

        sPrintFormat = "{0:^{width1}} {1:<{width2}} >> {2}"
        sPrintFormat = sPrintFormat if not bPrintSrcOnly else sPrintFormat.split(">>", 1)[0]

        def endCopy(sFilePath, sDestPath, bCopied, iDoneFileCount):

            iDoneFileCount += 1

            if bCopied:
                sCount = "{0}/{1}".format(iDoneFileCount, iNumFiles)
                print sPrintFormat.format(sCount,
                                          srcRootDirRexp.split(sFilePath, 1)[1],
                                          destRootDirRexp.split(sDestPath, 1)[1],
                                          width1=iCountLen,
                                          width2=iMaxPathLen)

                sCopiedFileList.append(sDestPath)

            return iDoneFileCount

        print '{0} files to copy from "{1}" to "{2}":'.format(iNumFiles, sSrcRootDir, sDestRootDir)

        # creating directories
        for sDestDir in sorted(set(sDestDirList)):
            if (not osp.isdir(sDestDir)) and (not bDryRun):
                os.makedirs(sDestDir)

        # copying files
        if sReplaceExtDct:

            for sFilePath, sDestDir in zip(sFilePathList, sDestDirList):

                sPath, sExt = osp.splitext(sFilePath); sExt = sExt.strip(".")
                sNewExt = sReplaceExtDct.get(sExt, "")
                if sNewExt:
                    sDestPath = pathJoin(sDestDir, osp.basename(sPath)) + "." + sNewExt.strip(".")
                else:
                    sDestPath = pathJoin(sDestDir, osp.basename(sFilePath))

                bCopied = True
                if sExt in sEncryptExtList:
                    pass# bCopied = cryptUtil.encryptFile(sFilePath, sDestPath, **kwargs)
                else:
                    sDestPath, bCopied = copyFile(sFilePath, sDestPath, **kwargs)

                iDoneFileCount = endCopy(sFilePath, sDestPath, bCopied, iDoneFileCount)

        elif sEncryptExtList:

            for sFilePath, sDestDir in zip(sFilePathList, sDestDirList):

                sExt = osp.splitext(sFilePath)[1].strip(".")

                # print "\t{0} >> {1}".format( srcRootDirRexp.split( sFilePath, 1 )[1], destRootDirRexp.split( sDestDir, 1 )[1] )

                sDestPath = pathJoin(sDestDir, osp.basename(sFilePath))

                bCopied = True
                if sExt in sEncryptExtList:
                    pass# bCopied = cryptUtil.encryptFile(sFilePath, sDestPath, **kwargs)
                else:
                    _, bCopied = copyFile(sFilePath, sDestPath, **kwargs)

                iDoneFileCount = endCopy(sFilePath, sDestPath, bCopied, iDoneFileCount)

        else:

            for sFilePath, sDestDir in zip(sFilePathList, sDestDirList):

                sDestPath = pathJoin(sDestDir, osp.basename(sFilePath))

                _, bCopied = copyFile(sFilePath, sDestPath, **kwargs)

                iDoneFileCount = endCopy(sFilePath, sDestPath, bCopied, iDoneFileCount)

    return sCopiedFileList

def jsonWrite(sFile, pyobj, **kwargs):
    with open(sFile, mode='wb') as fp:
        json.dump(pyobj, fp, indent=2, encoding='utf-8', **kwargs)

def jsonRead(sFile):
    with open(sFile, 'rb') as fp:
        pyobj = json.load(fp, encoding='utf-8')
    return pyobj

def sha1HashFile(sFilePath, chunk_size=1024 * 8):

    with open(sFilePath, "rb") as fp:

        h = hashlib.sha1()

        while True:

            chunk = fp.read(chunk_size)
            if not chunk:
                break

            h.update(chunk)

    return h.hexdigest()

def topmostFoundDir(sPath):

    sTestPath = sPath
    while not osp.exists(sTestPath):

        sSplitPath, _ = osp.split(sTestPath)

        if sSplitPath == sTestPath:
            return ""

        sTestPath = sSplitPath

    return sTestPath


