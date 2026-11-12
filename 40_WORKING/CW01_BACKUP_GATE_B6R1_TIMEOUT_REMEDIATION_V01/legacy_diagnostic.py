"""Run against verified copies of B4 in a scratch fixture directory."""
import errno,json,os,runpy,subprocess,sys,time
from pathlib import Path
import test_backup_gate_b4 as t
from ROUTABL_BackupHeadlessSupervisor_v0_3 import LABEL,pins
root=Path.cwd()
t.write(root/"fixture_approval.json",dict(schema_version="0.1",scope="ISOLATED_FIXTURE_ONLY",
    allowed_label=LABEL,pinned_programs=pins()))
first=t.seed("first",gate="hold")
t.seed("second")
wrapper=root/"diagnostic_entry.py"
wrapper.write_text("""import errno,json,os,runpy,subprocess,sys,time
from pathlib import Path
native_popen=subprocess.Popen
native_killpg=os.killpg
workers={}
def log(event,**fields):
    print(json.dumps(dict(event=event,monotonic=time.monotonic(),**fields)),file=sys.stderr,flush=True)
def lookup(pid):
    try:
        return dict(pid=pid,pgid=os.getpgid(pid),sid=os.getsid(pid),supervisor_uid=os.geteuid())
    except OSError as e:
        return dict(pid=pid,lookup_errno=e.errno)
class Measured(native_popen):
    def __init__(self,args,*a,**kw):
        begin=time.monotonic()
        super().__init__(args,*a,**kw)
        if len(args)==6 and str(args[3]).endswith('/fixture_worker.py'):
            workers[self.pid]=self
            self.ready_path=Path(kw['cwd'])/'cases'/args[4]/'ready.json'
            log('child_spawn',spawn_seconds=time.monotonic()-begin,**lookup(self.pid))
    def communicate(self,*a,**kw):
        if self.pid not in workers:
            return super().communicate(*a,**kw)
        begin=time.monotonic()
        wall=time.time_ns()
        try:
            output=super().communicate(*a,**kw)
        except subprocess.TimeoutExpired as e:
            log('communicate_timeout',elapsed=time.monotonic()-begin,timeout=kw.get('timeout'),
                stdout_bytes=len(e.output or b''),ready_seen=self.ready_path.exists(),
                ready_offset_seconds=((self.ready_path.stat().st_mtime_ns-wall)/1e9 if self.ready_path.exists() else None),
                **lookup(self.pid))
            raise
        log('communicate_return',elapsed=time.monotonic()-begin,returncode=self.returncode,
            ready_offset_seconds=((self.ready_path.stat().st_mtime_ns-wall)/1e9 if self.ready_path.exists() else None),
            **lookup(self.pid))
        return output
def measured_killpg(group,sig):
    if group not in workers or workers[group].returncode is not None:
        raise RuntimeError('UNOWNED_FIXTURE_SIGNAL_BLOCKED')
    context=lookup(group)
    if 'pgid' in context and (context['pgid']!=group or context['sid']!=group):
        raise RuntimeError('FIXTURE_GROUP_ID_CHANGED')
    try:
        native_killpg(group,sig)
    except OSError as error:
        log('killpg_error',signal=int(sig),errno=error.errno,name=errno.errorcode.get(error.errno),**context)
        try:
            native_killpg(group,0)
        except OSError as probe:
            log('killpg_zero_after_error',errno=probe.errno,name=errno.errorcode.get(probe.errno),**lookup(group))
        ps=native_popen(['/bin/ps','-axo','pid=,pgid=,stat='],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        out,_=ps.communicate(timeout=2)
        log('group_status_after_error',rows=[row.split() for row in out.splitlines()
            if len(row.split())==3 and row.split()[1]==str(group)],probe_exit=ps.returncode)
        raise
    else:
        log('killpg_returned',signal=int(sig),**context)
subprocess.Popen=Measured
os.killpg=measured_killpg
sys.argv.pop(0)
runpy.run_path(sys.argv[0],run_name='__main__')
""")
args=lambda name,entry:[sys.executable,"-B",str(wrapper),t.ENTRY,name,entry,"--label",LABEL]
owner=subprocess.Popen(args("first","scheduled"),cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
try:
    until=time.monotonic()+3
    while not (first/"ready.json").exists() and owner.poll() is None and time.monotonic()<until:
        time.sleep(.02)
    contender=subprocess.run(args("second","manual"),capture_output=True,cwd=root,timeout=8)
    out,owner_stderr=owner.communicate(timeout=8)
finally:
    if owner.poll() is None:
        owner.terminate()
        owner.communicate(timeout=5)
def trace(raw):
    rows=[]
    for line in raw.decode(errors="replace").splitlines():
        try:rows.append(json.loads(line))
        except ValueError:rows.append(dict(non_json_trace=line))
    return rows
# Independently probe the platform while an owned direct child is an unreaped zombie.
p=subprocess.Popen([sys.executable,"-I","-B","-c","pass"],cwd=root,start_new_session=True)
deadline=time.monotonic()+4
status=""
while time.monotonic()<deadline:
    q=subprocess.run(["/bin/ps","-p",str(p.pid),"-o","stat="],capture_output=True,text=True)
    status=q.stdout.strip()
    if status.startswith("Z"):break
    time.sleep(.02)
probe=dict(pid=p.pid,pgid=p.pid,pre_reap_state=status)
if status.startswith("Z"):
    try:os.killpg(p.pid,0)
    except OSError as err:probe.update(errno=err.errno,name=errno.errorcode.get(err.errno))
    else:probe.update(errno=0)
probe["exit"]=p.wait(timeout=4)
print(json.dumps(dict(legacy_owner=json.loads(out),legacy_contender=json.loads(contender.stdout),
                      owner_trace=trace(owner_stderr),
                      contender_trace=trace(contender.stderr),owned_zombie_signal_zero=probe)))
