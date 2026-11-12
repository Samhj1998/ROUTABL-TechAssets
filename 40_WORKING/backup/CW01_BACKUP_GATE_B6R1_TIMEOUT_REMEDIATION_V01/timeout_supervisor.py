"""B6-R1 candidate. Launches one fixed isolated worker, never a backup program."""
import errno
import fcntl
import hashlib
import json
import os
import selectors
import stat
import subprocess
import sys
import tempfile
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORKER = ROOT/"timeout_fixture.py"
PIN_NAMES = ("timeout_supervisor.py","timeout_fixture.py")
SCENARIOS = {"normal","slow","hang","resistant","noncooperative","escape","empty_success"}
MAX_OUTPUT = 65536

def fingerprint():
    return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in PIN_NAMES}

def atom(path,data):
    with tempfile.NamedTemporaryFile(dir=path.parent,prefix=".state-",delete=False) as f:
        name=Path(f.name)
        try:
            f.write((json.dumps(data,sort_keys=True)+"\n").encode())
            f.flush()
            os.fsync(f.fileno())
            os.replace(name,path)
        finally:
            name.unlink(missing_ok=True)
    fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)

def read(path):
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    with os.fdopen(fd,"rb") as f:
        if not stat.S_ISREG(os.fstat(f.fileno()).st_mode):
            raise ValueError("STATE_NOT_REGULAR")
        data=f.read(MAX_OUTPUT+1)
    if len(data)>MAX_OUTPUT:
        raise ValueError("STATE_TOO_LARGE")
    return json.loads(data)

def workspace(path):
    path=Path(path)
    if ROOT not in path.parents or path.resolve()!=path:
        raise ValueError("FIXTURE_ROOT_REQUIRED")
    info=path.stat()
    if info.st_uid!=os.geteuid() or stat.S_IMODE(info.st_mode)!=0o700:
        raise ValueError("PRIVATE_ROOT_REQUIRED")
    return path

def inode(info):
    return [info.st_dev,info.st_ino]

def prepare(path):
    path=workspace(path)
    fd=os.open(path/"run.lock",os.O_CREAT|os.O_EXCL|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        atom(path/"lock-id.json",inode(os.fstat(fd)))
    finally:
        os.close(fd)

@contextmanager
def locked(path):
    fd=os.open(path/"run.lock",os.O_RDWR|os.O_NOFOLLOW)
    try:
        info=os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid!=os.geteuid() or info.st_nlink!=1
                or stat.S_IMODE(info.st_mode)!=0o600 or inode(info)!=read(path/"lock-id.json")):
            raise ValueError("LOCK_IDENTITY_MISMATCH")
        try:
            fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            yield None
        else:
            if not lock_ok(path,fd):
                raise ValueError("LOCK_IDENTITY_MISMATCH")
            yield fd
    finally:
        os.close(fd)

def lock_ok(path,fd):
    return inode(os.fstat(fd))==inode((path/"run.lock").lstat())==read(path/"lock-id.json")

def os_identity(pid):
    return dict(pid=pid,pgid=os.getpgid(pid),sid=os.getsid(pid),uid=os.geteuid())

def process_state(pid):
    result=subprocess.run(["/bin/ps","-p",str(pid),"-o","pid=,uid=,pgid=,stat="],
                          capture_output=True,text=True,timeout=1)
    if result.returncode==1 and not result.stdout.strip() and not result.stderr.strip():
        return "ABSENT"
    if result.returncode!=0:
        return "UNKNOWN"
    cols=result.stdout.split()
    if len(cols)!=4 or int(cols[0])!=pid:
        return "UNKNOWN"
    return "ZOMBIE" if cols[3].startswith("Z") else "LIVE"

class Channel:
    def __init__(self,proc,token):
        self.token=token
        self.select=selectors.DefaultSelector()
        self.fd=proc.stdout.fileno()
        self.select.register(proc.stdout,selectors.EVENT_READ)
        self.buffer=b""
        self.read_bytes=0
        self.events=[]
        self.eof=False

    def read(self,seconds):
        if self.eof or not self.select.select(max(0,seconds)):
            return
        chunk=os.read(self.fd,8192)
        if not chunk:
            self.eof=True
            return
        self.read_bytes+=len(chunk)
        if self.read_bytes>MAX_OUTPUT:
            raise ValueError("FIXTURE_OUTPUT_LIMIT")
        self.buffer+=chunk
        while b"\n" in self.buffer:
            line,self.buffer=self.buffer.split(b"\n",1)
            event=json.loads(line)
            if event["token"]!=self.token:
                raise ValueError("FIXTURE_TOKEN_MISMATCH")
            self.events.append(event)

    def has(self,event):
        return any(row["event"]==event for row in self.events)

def wait_for(channel,predicate,deadline):
    while not predicate() and time.monotonic()<deadline:
        if channel.eof:
            time.sleep(.01)
        else:
            channel.read(min(.03,deadline-time.monotonic()))
    return predicate()

def pid_cleanup(proc,channel,seconds,send_signal=None):
    end=time.monotonic()+seconds
    try:
        if proc.stdin and not proc.stdin.closed:
            proc.stdin.close()  # cooperative stop, including owned escaped fixtures
        if wait_for(channel,lambda:proc.poll() is not None and channel.eof,min(end,time.monotonic()+.18)):
            return None
        if proc.poll() is None:
            if send_signal is None:
                proc.terminate()  # only the unreaped Popen child created by this run
            else:
                send_signal(proc)
        wait_for(channel,lambda:proc.poll() is not None and channel.eof,end)
        if proc.poll() is None or not channel.eof:
            return "CLEANUP_UNCONFIRMED"
    except PermissionError as error:
        return dict(code="CLEANUP_PERMISSION_DENIED",errno=error.errno,call="direct_child_terminate")
    except (OSError,ValueError,KeyError):
        return "CLEANUP_UNCONFIRMED"
    return None

def _run(path,scenario,approval,*,work_timeout=1.1,slow_after=.20,cleanup_timeout=.85,
        media_clear=lambda:True,send_signal=None,after_ready=None):
    path=workspace(path)
    if scenario not in SCENARIOS:
        raise ValueError("INVALID_FIXTURE_SCENARIO")
    with locked(path) as fd:
        if fd is None:
            return dict(status="SKIPPED_LOCK_HELD",actual_backup_success=False)
        if (path/"pending.json").exists() or (path/"pending.json").is_symlink():
            return dict(status="BLOCKED_UNRESOLVED_RUN",actual_backup_success=False)
        if media_clear() is not True:
            return dict(status="BLOCKED_MEDIA_STATE",actual_backup_success=False)
        before=fingerprint()
        if approval!={"scope":"ISOLATED_FIXTURE_ONLY","pins":before,"production_enabled":False}:
            return dict(status="BLOCKED_APPROVAL_OR_PIN",actual_backup_success=False)
        approval_before=json.dumps(approval,sort_keys=True)
        run_id=uuid.uuid4().hex
        journal=dict(run_id=run_id,state="ACTIVE",scenario=scenario,pids=[],fixture_only=True)
        atom(path/"pending.json",journal)
        began=time.monotonic()
        proc=subprocess.Popen([sys.executable,"-I","-B",str(WORKER),scenario,run_id],
            cwd=path,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
            start_new_session=True,close_fds=True,env={"PATH":"/usr/bin:/bin","HOME":str(path),"TMPDIR":str(path)})
        channel=Channel(proc,run_id)
        startup=work=0
        timed_out=False
        failure=None
        try:
            # Startup and active-work budgets are deliberately independent.
            ready=wait_for(channel,lambda:channel.has("READY") or proc.poll() is not None,time.monotonic()+5)
            startup=time.monotonic()-began
            if not ready or not channel.has("READY"):
                failure="FIXTURE_STARTUP_INCOMPLETE"
            else:
                owner=next(row for row in channel.events if row["event"]=="READY")
                if (owner["pid"]!=proc.pid or owner["pgid"]!=proc.pid or owner["sid"]!=proc.pid
                        or owner["uid"]!=os.geteuid()):
                    raise ValueError("FIXTURE_IDENTITY_MISMATCH")
                journal["pids"]=[owner]
                atom(path/"pending.json",journal)
                active=time.monotonic()
                if after_ready is not None:
                    after_ready()
                completed=wait_for(channel,lambda:proc.poll() is not None and channel.eof,active+work_timeout)
                work=time.monotonic()-active
                timed_out=not completed
                if timed_out:
                    failure="WORK_TIMEOUT"
        except (OSError,ValueError,KeyError,TypeError):
            failure="FIXTURE_OBSERVATION_ERROR"
        cleanup=None
        if failure:
            cleanup=pid_cleanup(proc,channel,cleanup_timeout,send_signal)
        if proc.stdin and not proc.stdin.closed:
            proc.stdin.close()
        owner_exit=proc.poll()
        observed=channel.events
        journal["pids"]=[row for row in observed if row["event"] in ("READY","DESCENDANT")]
        for row in journal["pids"]:
            row["observed_exit"]=owner_exit if row["pid"]==proc.pid else None
        channel.select.close()
        proc.stdout.close()
        try:
            current_lock=lock_ok(path,fd)
        except (OSError,ValueError,TypeError):
            current_lock=False
        current_pins=fingerprint()
        pins_unchanged=current_pins==before and json.dumps(approval,sort_keys=True)==approval_before
        clean=cleanup is None and owner_exit is not None and channel.eof
        if clean:
            try:
                clean=all(process_state(row["pid"]) in ("ABSENT","ZOMBIE") for row in journal["pids"])
            except (OSError,ValueError,subprocess.TimeoutExpired):
                clean=False
        if failure=="FIXTURE_OBSERVATION_ERROR":
            clean=False
        done=[row for row in observed if row["event"]=="DONE" and row["pid"]==proc.pid]
        elapsed=done[0].get("elapsed_seconds") if len(done)==1 else None
        if not clean:
            status=(cleanup["code"] if isinstance(cleanup,dict) else "CLEANUP_UNCONFIRMED")
        elif not current_lock:
            status="BLOCKED_LOCK_REPLACED"
        elif not pins_unchanged:
            status="BLOCKED_PIN_CHANGED"
        elif media_clear() is not True:
            status="BLOCKED_MEDIA_STATE"
        elif failure:
            status="TIMEOUT_CLEANED" if timed_out else failure
        elif owner_exit!=0 or type(elapsed) not in (int,float) or not 0<=elapsed<=work_timeout:
            status="FIXTURE_RESULT_UNPROVEN"
        else:
            status="FIXTURE_COMPLETED_DELAYED" if elapsed>slow_after else "FIXTURE_COMPLETED"
        report=dict(status=status,run_id=run_id,actual_backup_success=False,exit_code=owner_exit,
                    cleanup=cleanup,cleanup_verified=clean,stdout_eof=channel.eof,
                    startup_seconds=round(startup,4),work_seconds=round(work,4),
                    fixture_reported_active_seconds=elapsed,work_timeout=work_timeout,cleanup_timeout=cleanup_timeout,
                    children=journal["pids"])
        if current_lock:
            atom(path/("result-"+run_id+".json"),report)
            if clean and pins_unchanged and status!="BLOCKED_MEDIA_STATE":
                # Resolved history is durable before removing the admission fence.
                atom(path/"pending.json",dict(journal,state="RESOLVED",final_status=status))
                (path/"pending.json").unlink()
                directory=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
                try: os.fsync(directory)
                finally: os.close(directory)
            else:
                atom(path/"pending.json",dict(journal,state="UNRESOLVED",final_status=status,cleanup=cleanup))
        return report

def run(*args,**kwargs):
    try:
        return _run(*args,**kwargs)
    except (OSError,ValueError,TypeError,KeyError):
        return dict(status="BLOCKED_LOCK_OR_STATE",actual_backup_success=False)

def reconcile(path,run_id,*,media_clear=lambda:False,review_approved=False):
    """Read-only identity checks plus explicit acknowledgement, never sends a signal."""
    path=workspace(path)
    with locked(path) as fd:
        if fd is None:
            return "SKIPPED_LOCK_HELD"
        data=read(path/"pending.json")
        if (review_approved is not True or media_clear() is not True or data.get("run_id")!=run_id
                or data.get("state")!="UNRESOLVED" or not data.get("pids")):
            return "BLOCKED_RECONCILIATION"
        for row in data["pids"]:
            if process_state(row["pid"]) not in ("ABSENT","ZOMBIE"):
                return "BLOCKED_RECONCILIATION"
        if not lock_ok(path,fd):
            return "BLOCKED_RECONCILIATION"
        atom(path/("reconciled-"+run_id+".json"),dict(run_id=run_id,state="REVIEWED_EXIT_CONFIRMED",
                 children=data["pids"],fixture_only=True))
        (path/"pending.json").unlink()
        directory=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        try: os.fsync(directory)
        finally: os.close(directory)
        return "RECONCILED"

if __name__=="__main__":
    print(json.dumps(dict(status="DISABLED_NO_PRODUCTION_ADAPTER",actual_backup_success=False)))
    raise SystemExit(30)
