import platform
import re
import subprocess
import sys
import time
import os
import signal
import errno

def pstreekill(process):
    pid = process.pid
    if platform_is_windows():
        # Try allowing a clean shutdown first
        subprocess.call(['taskkill','/t','/pid',str(pid)])
        confirmed_termination = False
        timeout = time.time() + 10 # Timeout in seconds
        while time.time() < timeout:
            # Check the current status of the process
            status = subprocess.call(['tasklist','/nh','/fi','"PID eq %s"' % pid])
            if status.startswith("INFO: No tasks are running which match the specified criteria"):
                # Process has shutdown
                confirmed_termination = True
                break
            time.sleep(0.1) # Avoid spinning too fast while in the timeout loop
        if not confirmed_termination:
            # If the process hasn't shutdown politely yet kill it
            print "Force kill PID %d that hasn't responded to kill" % pid
            subprocess.call(['taskkill','/t','/f','/pid',str(pid)])
    else:
        # Send SIGINT to the process group to notify all processes that we
        # are going down now
        os.killpg(os.getpgid(pid), signal.SIGINT)

        # Now terminate and join the main process.  If the join has not returned
        # within 10 seconds then we will have to forcibly kill the process group
        process.terminate()
        for i in range(0,10):
          time.sleep(1)
          if process.poll() is not None:
            break

        if process.poll() is None:
            # If the process hasn't shutdown politely yet kill it
            try:
                print "Sending SIGKILL to PID %d that hasn't responded to SIGINT" % pid
                os.killpg(os.getpgid(pid), signal.SIGKILL)
            except OSError as err:
                # ESRCH == No such process - presumably exited since timeout...
                if err.errno != errno.ESRCH:
                    raise

## Annoying OS incompatability, not sure why this is needed

def platform_is_osx():
    ostype = platform.system()
    if re.match('.*Darwin.*', ostype):
        return True
    else:
        return False

def platform_is_windows():
    ostype = platform.system()
    if not re.match('.*Darwin.*', ostype) and re.match('.*[W|w]in.*', ostype):
        return True
    else:
        return False

if platform_is_windows():
    concat_args = True
    use_shell = True
    # Windows version of Python 2.7 doesn't support SIGINT
    SIGINT = signal.SIGTERM
else:
    concat_args = False
    use_shell = False
    SIGINT = signal.SIGINT
