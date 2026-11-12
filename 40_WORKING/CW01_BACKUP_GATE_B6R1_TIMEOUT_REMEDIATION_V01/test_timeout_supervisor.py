"""Isolated integration and OS probes."""
import errno
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch
import timeout_supervisor as candidate

ROOT=Path(__file__).resolve().parent

def approval():
    return dict(scope="ISOLATED_FIXTURE_ONLY",production_enabled=False,pins=candidate.fingerprint())

def setup(parent,name):
    path=parent/name
    path.mkdir(mode=0o700)
    candidate.prepare(path)
    return path

def later_exit(path,run_id,seconds=3):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        status=candidate.reconcile(path,run_id,media_clear=lambda:True,review_approved=True)
        if status=="RECONCILED":
            return status
        time.sleep(.05)
    return status

def main():
    cases=[]
    def check(case,wanted,actual,detail=None):
        cases.append(dict(case=case,expected=wanted,actual=actual,detail=detail,
                          verdict="PASS" if wanted==actual else "FAIL"))
    with tempfile.TemporaryDirectory(dir=ROOT,prefix="r1-tests-") as folder:
        root=Path(folder)
        path=setup(root,"normal")
        def run_at(path,scenario,**opts):
            p=opts.pop("policy",None)
            if p is None:
                p=approval()
            return candidate.run(path,scenario,p,**opts)
        def check_run(case,status,path,scenario,**opts):
            report=run_at(path,scenario,**opts)
            check(case,status,report["status"] if report["actual_backup_success"] is False else "UNSAFE_SUCCESS",
                  report)
            return report
        check_run("normal_owner_finishes","FIXTURE_COMPLETED",path,"normal")
        check_run("healthy_delay_warns_but_completes","FIXTURE_COMPLETED_DELAYED",path,"slow",
                  work_timeout=1.1)
        check_run("real_child_timeout_then_cooperative_exit","TIMEOUT_CLEANED",path,"hang",
                  work_timeout=.15)
        terminated=check_run("direct_owned_child_sigterm_after_timeout","TIMEOUT_CLEANED",path,"noncooperative",
                             work_timeout=.15,cleanup_timeout=1.1)
        check("direct_termination_observed",-15,terminated.get("exit_code"))
        check_run("exit_zero_without_new_evidence","FIXTURE_RESULT_UNPROVEN",path,"empty_success")
        old=path/"SUCCESS.json"
        old.write_bytes(b'{"status":"SUCCESS","run_id":"historical"}\n')
        original=old.read_bytes()
        check_run("old_receipt_cannot_convert_failure_to_success","FIXTURE_RESULT_UNPROVEN",path,"empty_success")
        check("old_receipt_unchanged",True,old.read_bytes()==original)
        check_run("uncertain_media_blocks_entry","BLOCKED_MEDIA_STATE",path,"normal",media_clear=lambda:None)
        bad=approval()
        bad["pins"]["timeout_fixture.py"]="0"*64
        check_run("wrong_pin_before_launch","BLOCKED_APPROVAL_OR_PIN",path,"normal",policy=bad)
        policy=approval()
        check_run("approval_changes_during_run","BLOCKED_PIN_CHANGED",path,"normal",policy=policy,
                  after_ready=lambda:policy.update(production_enabled=True))
        def deny(_):
            raise PermissionError(errno.EPERM,"simulated test-only signal refusal")
        p=setup(root,"denial")
        failed=check_run("injected_signal_refusal_is_distinct","CLEANUP_PERMISSION_DENIED",p,"resistant",
                         work_timeout=.12,send_signal=deny)
        check("permission_errno_preserved",errno.EPERM,failed.get("cleanup",{}).get("errno"))
        stored=p/("result-"+failed["run_id"]+".json")
        saved=stored.read_bytes()
        check("durable_unresolved_fence", "UNRESOLVED",candidate.read(p/"pending.json")["state"])
        check_run("released_flock_does_not_allow_reentry","BLOCKED_UNRESOLVED_RUN",p,"normal")
        check("manual_review_required","BLOCKED_RECONCILIATION",
              candidate.reconcile(p,failed["run_id"],media_clear=lambda:True))
        check("media_recheck_required","BLOCKED_RECONCILIATION",
              candidate.reconcile(p,failed["run_id"],review_approved=True,media_clear=lambda:None))
        check("verified_exit_allows_reconciliation","RECONCILED",later_exit(p,failed["run_id"]))
        check_run("admission_reopens_after_reconciliation","FIXTURE_COMPLETED",p,"normal")
        check("original_failure_evidence_retained",True,stored.read_bytes()==saved)
        p=setup(root,"escape")
        escaped=check_run("escaped_descendant_keeps_run_unresolved","CLEANUP_UNCONFIRMED",p,"escape",
                          work_timeout=.12,cleanup_timeout=.35)
        descendants=[row for row in escaped.get("children",[]) if row["event"]=="DESCENDANT"]
        parent=next(row for row in escaped["children"] if row["event"]=="READY")
        check("escaped_fixture_sid_and_pgid",True,bool(descendants and descendants[0]["sid"]!=parent["sid"]
                  and descendants[0]["pgid"]!=parent["pgid"] and descendants[0]["uid"]==parent["uid"]),descendants)
        check_run("escaped_child_prevents_reentry","BLOCKED_UNRESOLVED_RUN",p,"normal")
        check("escaped_fixture_self_exit_confirmed","RECONCILED",later_exit(p,escaped["run_id"]))
        p=setup(root,"inode")
        def swap():
            (p/"run.lock").rename(p/"old.lock")
            fd=os.open(p/"run.lock",os.O_CREAT|os.O_EXCL|os.O_RDWR,0o600)
            os.close(fd)
        check_run("inode_swap_never_releases_fence","BLOCKED_LOCK_REPLACED",p,"normal",after_ready=swap)
        check_run("new_inode_cannot_admit_next_run","BLOCKED_LOCK_OR_STATE",p,"normal")
        check("inode_swap_active_fence_preserved",True,(p/"pending.json").is_file())
        p=setup(root,"pin")
        good=approval()
        altered={**good["pins"],"timeout_supervisor.py":"a"*64}
        with patch.object(candidate,"fingerprint",side_effect=[good["pins"],altered]):
            check_run("post_run_code_pin_change","BLOCKED_PIN_CHANGED",p,"normal",policy=good)
        p=setup(root,"contend")
        # Separate real process obtains the exact lock before notifying the test.
        code=("import fcntl,sys; f=open(sys.argv[1],'rb'); "
              "fcntl.flock(f,fcntl.LOCK_EX); print('LOCKED',flush=True); sys.stdin.read()")
        holder=subprocess.Popen([sys.executable,"-I","-B","-c",code,str(p/"run.lock")],
            cwd=p,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        try:
            import select
            ready,_,_=select.select([holder.stdout],[],[],5)
            check("lock_holder_process_ready",True,bool(ready and holder.stdout.readline()==b"LOCKED\n"))
            check_run("real_cross_process_contention","SKIPPED_LOCK_HELD",p,"normal")
        finally:
            holder.communicate(timeout=5)
        check_run("real_lock_released_with_no_pending","FIXTURE_COMPLETED",p,"normal")
        # Signal zero is a kernel existence/permission probe, never delivers a signal.
        proc=subprocess.Popen([sys.executable,"-I","-B","-c","pass"],cwd=root,start_new_session=True)
        proc.wait(timeout=5)
        try:
            os.killpg(proc.pid,0)
        except OSError as error:
            actual=error.errno in (errno.ESRCH,errno.EPERM,errno.EACCES)
            check("real_os_signal_zero_error_on_ended_fixture_group",True,actual,
                  dict(pid=proc.pid,pgid=proc.pid,errno=error.errno,name=errno.errorcode.get(error.errno),
                       operation="os.killpg(pgid,0)",exit_code=proc.returncode))
        else:
            check("real_os_signal_zero_error_on_ended_fixture_group",True,False)
    passed=sum(row["verdict"]=="PASS" for row in cases)
    print(json.dumps(dict(passed=passed,total=len(cases),cases=cases),indent=2))
    return 0 if passed==len(cases) else 1

if __name__=="__main__":
    raise SystemExit(main())
