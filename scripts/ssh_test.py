from paramiko import SSHClient, WarningPolicy
from pytd.util.external.scp import SCPClient
from pytd.util.sysutils import timer
#from pytd.util.qtutils import setWaitCursor

def progressLog(sFilename, iSize, iSent):
    print "copying", sFilename, (iSent * 100 / iSize * 100) * .01, '%'

#@setWaitCursor
@timer
def sshCopy():

    sshCli = SSHClient()
    try:
        sshCli.set_missing_host_key_policy(WarningPolicy())
        sshCli.load_system_host_keys()

        sshCli.connect("diskstation", 22, "sebcourtois", "z2kzombie")
        t = sshCli.get_transport()

#        secOpt = t.get_security_options()
#        print secOpt.compression
#        print secOpt.ciphers
#        raise RuntimeError

        scpCli = SCPClient(t, progress=progressLog)
        try:
            scpCli.put(r"C:\Users\sebcourtois\Downloads\Autodesk_Maya_2016_EN_JP_ZH_Windows_dlm.sfx.exe",
                       "/volume1/Z2K_RnD/maya_third_party",
                       preserve_times=True, recursive=True)
        finally:
            scpCli.close()

        print "secured copy finished"

    #    sCmds = """cd /volume1/Z2K_RnD/
    #ln -s cmd_mayapy.bat cmd_mayapy_lnk.bat
    #ls -l
    #"""
    #    try:
    #        stdIn, stdOut, stdErr = sshCli.exec_command(sCmds)
    #        #print stdIn, stdOut, stdErr
    #        for s in stdOut:
    #            print s
    #
    #        for s in stdErr:
    #            print s
    #
    #    finally:
    #        stdIn.close()
    #        stdOut.close()
    #        stdErr.close()

    finally:
        sshCli.close()

sshCopy()
