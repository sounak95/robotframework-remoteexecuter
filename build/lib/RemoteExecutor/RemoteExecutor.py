import os
from robot.api import logger
import shutil
try:
    import wmi
    import win32wnet
except ImportError:
    wmi = None
    win32wnet = None
import time


class RemoteExecutor(object):
    """
    Library for remote script execution.
    """    
    
    def _exec(self, host, user, password, command):
        c = wmi.WMI(computer=host, user=user, password=password)
        tmpfilename = 'rf-{}.txt'.format(int(time.time() * 1000))
        local_tmp = r'c:\{}'.format(tmpfilename)
        remote_tmp = r'\\{}\c$\{}'.format(host, tmpfilename)
        command = r'{} > {}'.format(command, local_tmp)
        logger.debug("Process commandline: %s" % command)
        process_id, return_value = c.Win32_Process.Create(CommandLine=command)
        watcher = c.watch_for (
            notification_type="Deletion",
            wmi_class="Win32_Process",
            delay_secs=1,
            ProcessId=process_id
        )
        watcher()
        win32wnet.WNetAddConnection2(0, None, r"\\{}".format(host), None, user, password)
        shutil.copyfile(remote_tmp, local_tmp)
        buf = ''
        with open(local_tmp) as f:
            buf = f.read()
        logger.debug("Process output: %s" % buf)
        process_id, return_value = c.Win32_Process.Create(CommandLine='cmd /c del {}'.format(local_tmp))
        os.remove(local_tmp)
        return buf

    def execute_remotely(self, host, user, password, command):
        """
        Execute a command remotely.
        Remote host, user, password and command are required.
        A new commandline is spawned on the remote host automatically ("cmd.exe /c").
        Standard output is returned.
        Example:
        | Execute Remotely | MACHINE01 | misysroot\\user | pass | C:\\scripts\\my_script.py param1 param2 param3 |
        """
        if wmi is None or win32wnet is None:
            raise AssertionError("This keyword is supported on Windows platform only.")
        cmd = 'cmd.exe /c {}'.format(command)
        return self._exec(host, user, password, cmd)