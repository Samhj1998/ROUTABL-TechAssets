"""B6-R1 synthetic process. All activity is bounded and no media is accessed."""
import json
import os
import select
import signal
import sys
import time

def event(name,token,**fields):
    data=dict(event=name,token=token,pid=os.getpid(),pgid=os.getpgrp(),sid=os.getsid(0),uid=os.geteuid(),**fields)
    os.write(1,(json.dumps(data)+"\n").encode())

def stop_on_stdin(seconds):
    readable,_,_=select.select([0],[],[],seconds)
    if readable:
        os.read(0,1)

def main(scenario,token):
    if scenario=="resistant":
        signal.signal(signal.SIGTERM,signal.SIG_IGN)
    active=time.monotonic()
    event("READY",token)
    if scenario=="escape":
        if os.fork()==0:
            os.setsid()
            event("DESCENDANT",token)
            time.sleep(1.65)
            os._exit(0)
        stop_on_stdin(2.5)
        return 3
    if scenario=="slow":
        time.sleep(.43)
    elif scenario=="hang":
        stop_on_stdin(2.5)
        return 3
    elif scenario=="noncooperative":
        time.sleep(1.65)
        return 3
    elif scenario=="resistant":
        time.sleep(1.65)
        return 3
    elif scenario=="empty_success":
        return 0
    else:
        time.sleep(.02)
    event("DONE",token,elapsed_seconds=time.monotonic()-active)
    return 0

if __name__=="__main__":
    raise SystemExit(main(*sys.argv[1:]))
