
from paramiko import SSHClient, WarningPolicy
from pytd.util.external.scp import SCPClient

sshCli = SSHClient()
try:
    sshCli.set_missing_host_key_policy(WarningPolicy())
    sshCli.load_system_host_keys()

    sshCli.connect("diskstation", 22, "sebcourtois", "z2kzombie")

#    scpCli = SCPClient(sshCli.get_transport())
#    try:
#        scpCli.put(r"C:\Users\sebcourtois\Wildlife.wmv", "/volume1/Z2K_RnD/Wildlife.wmv",
#                   preserve_times=True)
#    finally:
#        scpCli.close()

    sCmds = """cd /Z2K_RnD/
ln -s cmd_mayapy.bat cmd_mayapy_lnk.bat
ls -l
"""
    try:
        stdIn, stdOut, stdErr = sshCli.exec_command(sCmds)
        #print stdIn, stdOut, stdErr
        for s in stdOut:
            print s

        for s in stdErr:
            print s

    finally:
        stdIn.close()
        stdOut.close()
        stdErr.close()

finally:
    sshCli.close()
