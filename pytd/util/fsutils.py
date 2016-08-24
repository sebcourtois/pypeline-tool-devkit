

import os
import re
import fnmatch
import json
import hashlib
from stat import ST_ATIME, ST_MTIME, ST_MODE, S_IMODE, S_ISDIR, S_ISREG

from distutils.file_util import copy_file

from .external import parse
from .sysutils import toUnicode, argToList
from .logutils import logMsg
from .systypes import MemSize

osp = os.path

def isDirStat(statobj):
    return S_ISDIR(statobj.st_mode)

def isFileStat(statobj):
    return S_ISREG(statobj.st_mode)

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

def pathParse(sPathFormat, sPath, log=False):

    fmtDirs = pathSplitDirs(sPathFormat)
    pathDirs = pathSplitDirs(sPath)

    numFmtDirs = len(fmtDirs)
    numPathDirs = len(pathDirs)

    minLen = min(numFmtDirs, numPathDirs)

    fmt = pathJoin(*fmtDirs[1:minLen])
    s = pathJoin(*pathDirs[1:minLen])

    res = parse.parse(fmt, s)

    if log:
        print "\n", fmt, sPathFormat
        print s, sPath
        print res

    return res

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

def pathRename(sSrcPath, sDstPath):
    try:
        os.rename(sSrcPath, sDstPath)
    except WindowsError as e:
        raise WindowsError(toUnicode("{} - {}: {}".format(e.args[0], e.strerror , sSrcPath)))

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

    onlyFilesFunc = kwargs.get("onlyFiles", None)

    for sDirPath, sDirNames, sFileNames in os.walk(sRootDirPath):

        if not bRecursive:
            del sDirNames[:] # don't walk further

        if ignoreDirsFunc is not None:
            sIgnoredDirs = ignoreDirsFunc(sDirPath, sDirNames)
            for sDir in sIgnoredDirs:
                try: sDirNames.remove(sDir)
                except ValueError: pass

        bOnly = False
        sOnlyFiles = []
        if onlyFilesFunc is not None:
            sOnlyFiles = onlyFilesFunc(sDirPath, sFileNames)
            #print "sOnlyFiles", sOnlyFiles, sFileNames
            bOnly = True

        sIgnoredFiles = []
        if ignoreFilesFunc is not None:
            sIgnoredFiles = ignoreFilesFunc(sDirPath, sFileNames)
            #print "sIgnoredFiles", sIgnoredFiles

        sKeptFileNames = sFileNames[:]

        for sFileName in sFileNames:

            if bOnly and (sFileName not in sOnlyFiles):
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

def copyFileOld(sSrcPath, sDstPath, **kwargs):

    if osp.isdir(sDstPath):
        sDstPath = pathJoin(sDstPath, osp.basename(sSrcPath))

    if sameFile(sSrcPath, sDstPath):
        sMsg = u"Source and destination files are the same:"
        sMsg += u"\n    source:      ", sSrcPath
        sMsg += u"\n    destination: ", sDstPath
        raise EnvironmentError(sMsg)

    logMsg(u"\nCopying '{}'\n     to '{}'".format(sSrcPath, sDstPath))

    return copy_file(sSrcPath, sDstPath, **kwargs)

_copy_action = {
'': 'copying',
'hard': 'hard linking',
'symb': 'symbolically linking'}

def copyFile(sSrcPath, sDstPath, preserve_mode=True, preserve_times=True, in_place=False,
             update=False, link="", verbose=1, dry_run=False, buffer_size=64 * 1024):
    """Copy a file 'sSrcPath' to 'sDstPath'. (Stolen and updated from distutils.file_util)

    If 'sDstPath' is a directory, then 'sSrcPath' is copied there with the same name;
    otherwise, it must be a filename.  (If the file exists, it will be
    ruthlessly clobbered.)  If 'preserve_mode' is true (the default),
    the file's mode (type and permission bits, or whatever is analogous on
    the current platform) is copied.  If 'preserve_times' is true (the
    default), the last-modified and last-access times are copied as well.
    If 'update' is true, 'sSrcPath' will only be copied if 'sDstPath' does not exist,
    or if 'sDstPath' does exist but is older than 'sSrcPath'.

    'link' allows you to make hard links (os.link) or symbolic links
    (os.symlink) instead of copying: set it to "hard" or "sym"; if it is
    None (the default), files are copied.  Don't set 'link' on systems that
    don't support it: 'copy_file()' doesn't check if hard or symbolic
    linking is available.

    Under Mac OS, uses the native file copy function in macostools; on
    other systems, uses '_copy_file_contents()' to copy file contents.

    Return a tuple (dest_name, copied): 'dest_name' is the actual name of
    the output file, and 'copied' is true if the file was copied (or would
    have been copied, if 'dry_run' true).
    """
    # XXX if the destination file already exists, we clobber it if
    # copying, but blow up if linking.  Hmmm.  And I don't know what
    # macostools.copyfile() does.  Should definitely be consistent, and
    # should probably blow up if destination exists and we would be
    # changing it (ie. it's not already a hard/soft link to sSrcPath OR
    # (not update) and (sSrcPath newer than sDstPath).

    try:
        sAction = _copy_action[link].capitalize()
    except KeyError:
        raise ValueError(u"Invalid value for 'link' argument: '{}'. Expected one of {}."
                         .format(link, _copy_action.keys()))

    srcStat = os.stat(sSrcPath)
    if not S_ISREG(srcStat.st_mode):
        raise EnvironmentError(u"Source file NOT found: '{}'.".format(sSrcPath))

    if osp.isdir(sDstPath):
        sDirPath = sDstPath
        sDstPath = osp.join(sDstPath, osp.basename(sSrcPath))
    else:
        sDirPath = osp.dirname(sDstPath)

    if update and (not pathNewer(sSrcPath, sDstPath)):
        if verbose >= 1:
            logMsg(u"Not copying (output up-to-date): '{}'".format(sSrcPath), log="debug")
        return sDstPath, False

    if verbose >= 1:
        if osp.basename(sDstPath) == osp.basename(sSrcPath):
            logMsg(u"\n{} '{}'\n     -> '{}'".format(sAction, sSrcPath, sDirPath))
        else:
            logMsg(u"\n{} '{}'\n     -> '{}'".format(sAction, sSrcPath, sDstPath))

    if dry_run:
        return (sDstPath, True)

    # If linking (hard or symbolic), use the appropriate system call
    # (Unix only, of course, but that's the caller's responsibility)
    if link == 'hard':
        if not (osp.exists(sDstPath) and osp.samefile(sSrcPath, sDstPath)):
            os.link(sSrcPath, sDstPath)
    elif link == 'symb':
        if not (osp.exists(sDstPath) and osp.samefile(sSrcPath, sDstPath)):
            os.symlink(sSrcPath, sDstPath)

    # Otherwise (non-Mac, not linking), copy the file contents and
    # (optionally) copy the times and mode.
    else:
        if sameFile(sSrcPath, sDstPath):
            sMsg = u"Source and destination files are the same:"
            sMsg += u"\n    source:      ", sSrcPath
            sMsg += u"\n    destination: ", sDstPath
            raise EnvironmentError(sMsg)

        sTmpPath = ""
        try:
            dstStat = os.stat(sDstPath)
        except OSError:
            pass
        else:# destination  path exists
            if not S_ISREG(dstStat.st_mode):
                raise EnvironmentError(u"Path already exists but NOT a regular file: '{}'."
                                       .format(sDstPath))
            if not in_place:
                pathRename(sDstPath, sDstPath)
                sTmpPath = sDstPath + ".tmpcopy"

        sCopyPath = sTmpPath if sTmpPath else sDstPath
        try:
            with open(sSrcPath, 'rb') as srcFobj:
                with open(sCopyPath, 'wb') as dstFobj:
                    while True:
                        buf = srcFobj.read(buffer_size)
                        if not buf:
                            break
                        dstFobj.write(buf)

            dstStat = os.stat(sCopyPath)
            if dstStat.st_size != srcStat.st_size:
                srcSize = MemSize(srcStat.st_size)
                dstSize = MemSize(dstStat.st_size)
                raise IOError(u"Incomplete copy: {:.1cM}/{:.1cM} copied."
                              .format(dstSize, srcSize))

            if preserve_mode or preserve_times:
                # According to David Ascher <da@ski.org>, utime() should be done
                # before chmod() (at least under NT).
                if preserve_times:
                    os.utime(sCopyPath, (srcStat[ST_ATIME], srcStat[ST_MTIME]))
                if preserve_mode:
                    os.chmod(sCopyPath, S_IMODE(srcStat[ST_MODE]))

            if sTmpPath:
                if os.name == "nt": # on nt platform, destination must be removed first
                    os.remove(sDstPath)
                pathRename(sTmpPath, sDstPath)

        finally:
            if sTmpPath and osp.exists(sTmpPath):
                os.remove(sTmpPath)

    return (sDstPath, True)

def pathNewer(sSrcPath, sDstPath):
    """Tells if the sDstPath is newer than the sSrcPath.

    Return true if 'sSrcPath' exists and is more recently modified than
    'sDstPath', or if 'sSrcPath' exists and 'sDstPath' doesn't.

    Return false if both exist and 'sDstPath' is the same age or younger
    than 'sSrcPath'. Raise DistutilsFileError if 'sSrcPath' does not exist.

    Note that this test is not very accurate: files created in the same second
    will have the same "age".
    """
    if not osp.exists(sSrcPath):
        raise EnvironmentError(u"No such file: '{}'.".format(osp.abspath(sSrcPath)))
    if not osp.exists(sDstPath):
        return True

    return os.stat(sSrcPath)[ST_MTIME] > os.stat(sDstPath)[ST_MTIME]

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

    if not osp.isfile(sFile):
        raise EnvironmentError("No such file: '{}'".format(sFile))

    with open(sFile, 'rb') as fp:
        pyobj = json.load(fp, encoding='utf-8')

    return pyobj

def sha1HashFile(sFilePath, chunk_size=16 * 1024):

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


