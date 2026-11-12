"""Tests execute a complete isolated package in disposable subdirectories."""
from datetime import timedelta
import errno
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

BASE=Path(__file__).resolve().parent
MODULES=("r2_supervisor.py","r2_oneshot.py","r2_worker.py","r2_lifecycle.py","b4_evidence.py","b6_evidence.py",
         "backup_runner_candidate.py","ROUTABL_BackupEvidenceNormalizer_v0_1.py")

def pack(directory):
    for name in MODULES:
        shutil.copyfile(BASE/name,directory/name)
    script=directory/"isolated_test_driver.py"
    script.write_bytes(Path(__file__).read_bytes())
    return script

def seed(case,gate="new",nas="new",age=0,stale=False,old_success=False):
    from r2_supervisor import ROOT
    import b4_evidence as evidence
    import r2_worker as worker
    from dataclasses import replace
    from datetime import datetime
    base=ROOT/"cases"/case
    (base/"registry").mkdir(parents=True)
    (base/"assets").mkdir()
    (base/"registry/asset_manifest_v0.9.json").write_bytes(b'{"version":9}')
    (base/"registry/asset_manifest_v0.27.json").write_bytes(b'{"version":27}')
    (base/"assets/asset").write_bytes(b"independent fixture bytes")
    (base/"cas_blob.bin").write_bytes(b"fixture ciphertext")
    worker.write(base,"selection.json",{"files":[dict(name="asset",target="asset",category="registry")]})
    worker.write(base,"config.json",dict(gate=gate,nas=nas))
    if gate=="reuse":
        current=evidence.inventory(base)
        if stale:
            current=replace(current,manifest_name="asset_manifest_v0.19.json",manifest_sha256="a"*64)
        when=datetime.now(worker.KST)-timedelta(days=age,seconds=5)
        worker.local_receipt(base,when,current)
        worker.cas_receipt(base,when+timedelta(seconds=1),"new")
    if old_success:
        worker.write(base,"SUCCESS.json",{"status":"SUCCESS","run_id":"historical"})
    return base

def driver(kind):
    import r2_supervisor as s
    from r2_supervisor import LABEL,ROOT
    import r2_lifecycle as life
    results=[]
    def add(name,expected,actual,detail=None):
        results.append(dict(case=name,expected=expected,actual=actual,detail=detail,
                            verdict="PASS" if expected==actual else "FAIL"))
    s.initialize()
    policy=s.fixture_policy()
    life.atom(ROOT/"fixture_approval.json",policy)
    def spawn(case,entry):
        return subprocess.Popen([sys.executable,"-B",str(ROOT/"r2_supervisor.py"),case,entry,"--label",LABEL],
              cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    def take(proc):
        out,err=proc.communicate(timeout=20)
        if not out:
            raise RuntimeError(err.decode(errors="replace"))
        return json.loads(out),proc.returncode
    def check(name,expected,case=None,reason=None,**kwargs):
        result=s.run(case or name,"manual",[LABEL],kwargs.pop("policy",policy),**kwargs)
        actual=result["status"] if (not result["actual_backup_success"] and not result["production_deployment"]
                                    and (reason is None or result["reason"]==reason)) else "CONTRACT_MISMATCH"
        add(name,expected,actual,result)
        return result
    if kind=="equivalence":
        seed("new")
        check("new","CANDIDATE_NEW_EVIDENCE")
        base=seed("first",gate="hold")
        seed("second")
        first=spawn("first","scheduled")
        try:
            limit=time.monotonic()+7
            while not (base/"ready.json").is_file() and first.poll() is None and time.monotonic()<limit:
                time.sleep(.01)
            # The hard active budget is unchanged. Start contender immediately;
            # a pre-launched kernel-lock waiter below covers slower CLI startups.
            contender,exit_code=take(spawn("second","manual"))
            add("manual_vs_scheduled_same_lock","SKIPPED_LOCK_HELD",contender["status"],
                dict(exit=exit_code,owner_ready=(base/"ready.json").is_file(),stages=contender["stages"]))
        finally:
            owner,code=take(first)
        add("normal_owner_finishes_with_original_0_8s_hold","CANDIDATE_NEW_EVIDENCE",owner["status"],owner)
        add("hold_classified_as_delay","FIXTURE_COMPLETED_DELAYED",
            owner["stages"][0]["status"] if owner["stages"] else None)
        for name,gate,nas,status,reason in [
            ("child_lock","child_lock","new","SKIPPED_LOCK_HELD","CHILD_LOCK_HELD"),
            ("no_work","no_work","new","NO_NEW_BACKUP_EVIDENCE","LOCAL_WORK_NOT_PROVEN"),
            ("nonzero","exit7","new","FAILED_SAFE","CHILD_NONZERO"),
            ("malformed","malformed","new","FAILED_SAFE","LOCAL_RESULT_CONTRADICTORY_OR_FAILED"),
            ("selection_change","new","change","FAILED_SAFE","INVENTORY_CHANGED"),
            ("missing_nas","new","missing","NAS_CHAIN_NOT_VERIFIED","NAS_EVIDENCE_MISSING_OR_MISMATCH"),
            ("incomplete_nas","new","incomplete","NAS_CHAIN_NOT_VERIFIED","NAS_EVIDENCE_MISSING_OR_MISMATCH"),
            ("mismatched_nas","new","mismatch","NAS_CHAIN_NOT_VERIFIED","NAS_EVIDENCE_MISSING_OR_MISMATCH"),
            ("already_indexed_new","new","reindex","NAS_CHAIN_NOT_VERIFIED","NAS_WORK_STATE_MISMATCH"),
        ]:
            seed(name,gate,nas,old_success=name=="no_work")
            check(name,status,reason=reason)
        add("old_receipt_preserved","historical",life.read(ROOT/"cases/no_work/SUCCESS.json")["run_id"])
        seed("reuse","reuse","reindex")
        check("reuse","CANDIDATE_SAME_DAY_RECHECK")
        seed("yesterday","reuse","reindex",age=1)
        check("yesterday","STALE_REGISTRY_BACKUP",reason="LOCAL_NOT_SAME_KST_DAY")
        seed("stale","reuse","reindex",stale=True)
        check("stale","STALE_REGISTRY_BACKUP",reason="LOCAL_INVENTORY_MISMATCH")
        seed("pin")
        bad={**policy,"pins":{**policy["pins"],"r2_worker.py":"0"*64}}
        check("pin","FAILED_SAFE",policy=bad,reason="PROGRAM_PIN_MISMATCH")
        duplicate=s.run("pin","manual",[LABEL,"com.routabl.assetbackup.native.v042"],policy)
        add("duplicate_entry_rejected","SCHEDULE_NOT_SINGLE_AUTHORIZED_ENTRY",duplicate["reason"])
        outside=s.run("../outside","manual",[LABEL],policy)
        add("outside_fixture_rejected","INVALID_CASE_NAME",outside["reason"])
        check("media_unknown","BLOCKED_MEDIA_STATE",case="pin",media_clear=lambda:None)
    if kind=="lifecycle":
        seed("hang","hang")
        timed=check("hang","FAILED_SAFE",timeout=.16,reason="TIMEOUT_CLEANED")
        add("cleaned_timeout_does_not_leave_fence",False,(s.STATE/"active.json").exists())
        seed("resistant","resistant")
        def deny(_):
            raise PermissionError(errno.EPERM,"fixture signal denied")
        denied=check("resistant","BLOCKED_UNRESOLVED_RUN",timeout=.12,send_signal=deny,
                     reason="CLEANUP_PERMISSION_DENIED")
        add("errno_retained",1,denied["stages"][0]["cleanup"]["errno"])
        result_path=s.STATE/("result-"+denied["run_id"]+".json")
        old=result_path.read_bytes()
        seed("after_deny")
        after,code=take(spawn("after_deny","scheduled"))
        add("new_supervisor_process_cannot_reenter_after_denial","BLOCKED_UNRESOLVED_RUN",after["status"],after)
        add("no_worker_launched_on_reentry",[],after["stages"])
        add("approval_required","BLOCKED_RECONCILIATION",
            s.reconcile(denied["run_id"],media_clear=lambda:True))
        add("media_check_required","BLOCKED_RECONCILIATION",
            s.reconcile(denied["run_id"],review_approved=True,media_clear=lambda:None))
        def settle(run_id):
            until=time.monotonic()+4
            while time.monotonic()<until:
                state=s.reconcile(run_id,review_approved=True,media_clear=lambda:True)
                if state=="RECONCILED":
                    return state
                time.sleep(.05)
            return "STILL_BLOCKED"
        add("reconciled_after_verified_exit","RECONCILED",settle(denied["run_id"]))
        check("after_deny","CANDIDATE_NEW_EVIDENCE")
        add("failure_receipt_survives_recovery",True,old==result_path.read_bytes())
        seed("escape","escape")
        escaped=check("escape","BLOCKED_UNRESOLVED_RUN",timeout=.13,cleanup=.22,reason="CLEANUP_UNCONFIRMED")
        children=escaped["stages"][0]["children"]
        add("escape_records_new_session",True,any(row["event"]=="DESCENDANT" and
            row["sid"]==row["pid"] and row["sid"]!=children[0]["sid"] for row in children),children)
        seed("next")
        check("escaped_descendant_blocks_next","BLOCKED_UNRESOLVED_RUN",case="next")
        add("escaped_fixture_self_exit_and_review","RECONCILED",settle(escaped["run_id"]))
        check("next","CANDIDATE_NEW_EVIDENCE")
    if kind=="inode":
        seed("new")
        def replace():
            lock=s.STATE/"run.lock"
            lock.rename(s.STATE/"prior.lock")
            fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_RDWR,0o600)
            os.close(fd)
        check("inode_replaced","BLOCKED_LOCK_REPLACED",case="new",after_capture=replace)
        check("replacement_inode_rejected","BLOCKED_LOCK_OR_STATE",case="new")
        add("inode_failure_leaves_fence",True,(s.STATE/"active.json").is_file())
    if kind=="policy":
        seed("new")
        check("midrun_pin_change","BLOCKED_PIN_CHANGED",case="new",
              after_capture=lambda:policy["pins"].update({"r2_worker.py":"0"*64}))
        check("policy_failure_leaves_fence","BLOCKED_UNRESOLVED_RUN",case="new")
    if kind=="crash":
        seed("crash")
        seed("next")
        argv=[sys.executable,"-B","-c","import os,r2_supervisor as s; s.run('crash','manual',[s.LABEL],s.fixture_policy(),after_capture=lambda:os._exit(42))"]
        proc=subprocess.run(argv,cwd=ROOT,capture_output=True,timeout=18)
        add("fixture_supervisor_abrupt_exit",42,proc.returncode)
        next_result,_=take(spawn("next","scheduled"))
        add("supervisor_restart_keeps_unfinished_journal","BLOCKED_UNRESOLVED_RUN",next_result["status"])
        data=life.read(s.STATE/"active.json")
        add("crash_without_terminal_state_requires_manual_review","BLOCKED_RECONCILIATION",
            s.reconcile(data["run_id"],review_approved=True,media_clear=lambda:True))
    print(json.dumps(results))

def main():
    all_cases=[]
    for kind in ("equivalence","lifecycle","inode","policy","crash"):
        with tempfile.TemporaryDirectory(prefix="r2-fixture-",dir=BASE) as temp:
            directory=Path(temp)
            entry=pack(directory)
            proc=subprocess.run([sys.executable,"-B",str(entry),kind],cwd=directory,capture_output=True,timeout=110)
            try:
                all_cases.extend(json.loads(proc.stdout))
            except ValueError:
                all_cases.append(dict(case=kind,verdict="FAIL",exit=proc.returncode,stderr=proc.stderr.decode(errors="replace")))
    passed=sum(row["verdict"]=="PASS" for row in all_cases)
    print(json.dumps(dict(passed=passed,total=len(all_cases),cases=all_cases),indent=2))
    return 0 if passed==len(all_cases) else 1

if __name__=="__main__":
    if len(sys.argv)>1:
        driver(sys.argv[1])
    else:
        raise SystemExit(main())
