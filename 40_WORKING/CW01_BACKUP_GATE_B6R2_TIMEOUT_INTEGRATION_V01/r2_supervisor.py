"""R2 isolated coordinator. The shared lock spans Gate, NAS and evidence publication."""
import argparse
import json
import os
from uuid import uuid4

import b4_evidence as legacy
import r2_lifecycle as life
from backup_runner_candidate import Stop
from r2_oneshot import Port

ROOT=life.ROOT
LABEL="com.routabl.assetbackup.native.v043"
STATE=ROOT/"state"

def initialize():
    STATE.mkdir(mode=0o700)
    life.prepare(STATE)
    (STATE/"stage").mkdir(mode=0o700)
    life.prepare(STATE/"stage")

def fixture_policy():
    return {"scope":"ISOLATED_FIXTURE_ONLY","pins":life.fingerprint(),"production_enabled":False}

def pending(path):
    return os.path.lexists(path/"pending.json")

def run(case,entry,active,policy,*,media_clear=lambda:True,timeout=1.1,cleanup=.85,send_signal=None,after_capture=None):
    result=dict(scope="ISOLATED_FIXTURE_ONLY",status="FAILED_SAFE",reason="PREFLIGHT",stages=[],events=[],
                actual_backup_success=False,production_deployment=False)
    if entry not in ("manual","scheduled") or active!=[LABEL]:
        return dict(result,reason="SCHEDULE_NOT_SINGLE_AUTHORIZED_ENTRY")
    journal=STATE/"active.json"
    stage=STATE/"stage"
    try:
        with life.locked(life.workspace(STATE)) as fd:
            if fd is None:
                return dict(result,status="SKIPPED_LOCK_HELD",reason="SHARED_LOCK_HELD")
            if os.path.lexists(journal) or pending(stage):
                return dict(result,status="BLOCKED_UNRESOLVED_RUN",reason="PERSISTENT_FENCE")
            if media_clear() is not True:
                return dict(result,status="BLOCKED_MEDIA_STATE",reason="MEDIA_UNKNOWN")
            before=life.fingerprint()
            if policy!={"scope":"ISOLATED_FIXTURE_ONLY","pins":before,"production_enabled":False}:
                return dict(result,reason="PROGRAM_PIN_MISMATCH")
            policy_before=json.dumps(policy,sort_keys=True)
            run_id=uuid4().hex
            state=dict(run_id=run_id,state="ACTIVE",case=case,entry=entry)
            try:
                base=legacy.fixture(case)
            except Stop as error:
                return dict(result,status=error.status,reason=error.reason)
            life.atom(journal,state)
            result.update(run_id=run_id)
            port=Port(base,stage,policy,timeout,cleanup,media_clear,send_signal)
            def record(phase,code,exit_code=None,executed=None,evidence=None):
                result["events"].append(dict(phase=phase,code=code,exit_code=exit_code,executed=executed))
            try:
                result["status"],result["evidence"]=port.capture(record)
                result["reason"]="ISOLATED_EVIDENCE_CONTRACT"
                if after_capture is not None:
                    after_capture()
            except Stop as error:
                result.update(status=error.status,reason=port.last_failure or error.reason)
            except (OSError,ValueError,KeyError,TypeError):
                result.update(status="FAILED_SAFE",reason="EVIDENCE_OR_ADAPTER_ERROR")
            result["stages"]=port.proofs
            try:
                lock_valid=life.lock_ok(STATE,fd)
            except (OSError,ValueError):
                lock_valid=False
            stable=before==life.fingerprint() and policy_before==json.dumps(policy,sort_keys=True)
            media_ok=media_clear() is True
            pending_stage=pending(stage)
            if not lock_valid or not stable or not media_ok or pending_stage:
                if not lock_valid:
                    result.update(status="BLOCKED_LOCK_REPLACED",reason="LOCK_INODE_CHANGED")
                elif not stable:
                    result.update(status="BLOCKED_PIN_CHANGED",reason="PIN_OR_APPROVAL_CHANGED")
                elif not media_ok:
                    result.update(status="BLOCKED_MEDIA_STATE",reason="MEDIA_UNKNOWN")
                else:
                    result.update(status="BLOCKED_UNRESOLVED_RUN",reason=port.last_failure or "STAGE_PENDING")
                result.pop("evidence",None)
                if lock_valid:
                    stage_id=life.read(stage/"pending.json").get("run_id") if pending_stage else None
                    life.atom(journal,dict(state,state="UNRESOLVED",stage_pending=pending_stage,
                                          stage_run_id=stage_id,reason=result["reason"]))
            if lock_valid:
                life.atom(STATE/("result-"+run_id+".json"),result)
                if stable and media_ok and not pending_stage:
                    life.atom(journal,dict(state,state="RESOLVED"))
                    journal.unlink()
                    sync_dir(STATE)
            return result
    except (OSError,ValueError,KeyError,TypeError):
        return dict(result,status="BLOCKED_LOCK_OR_STATE",reason="LOCK_OR_STATE_INVALID")

def sync_dir(path):
    fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)

def reconcile(run_id,*,review_approved=False,media_clear=lambda:False):
    try:
        with life.locked(life.workspace(STATE)) as fd:
            if fd is None:
                return "SKIPPED_LOCK_HELD"
            journal=STATE/"active.json"
            data=life.read(journal)
            if (data.get("run_id")!=run_id or data.get("state")!="UNRESOLVED"
                    or review_approved is not True or media_clear() is not True
                    or not life.lock_ok(STATE,fd)):
                return "BLOCKED_RECONCILIATION"
            stage=STATE/"stage"
            if pending(stage):
                prior=life.read(stage/"pending.json")
                if prior.get("run_id")!=data.get("stage_run_id"):
                    return "BLOCKED_RECONCILIATION"
                if life.reconcile(stage,prior["run_id"],media_clear=media_clear,
                                  review_approved=True)!="RECONCILED":
                    return "BLOCKED_RECONCILIATION"
            else:
                stage_id=data.get("stage_run_id")
                if data.get("stage_pending") is not True or not isinstance(stage_id,str) or not stage_id.isalnum():
                    return "BLOCKED_RECONCILIATION"
                if life.read(stage/("reconciled-"+stage_id+".json")).get("run_id")!=stage_id:
                    return "BLOCKED_RECONCILIATION"
            if not life.lock_ok(STATE,fd) or media_clear() is not True:
                return "BLOCKED_RECONCILIATION"
            life.atom(STATE/("review-"+run_id+".json"),dict(run_id=run_id,status="RECONCILED"))
            journal.unlink()
            sync_dir(STATE)
            return "RECONCILED"
    except (OSError,ValueError,KeyError,TypeError):
        return "BLOCKED_RECONCILIATION"

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("case")
    parser.add_argument("entry",choices=("scheduled","manual"))
    parser.add_argument("--label",action="append",required=True)
    args=parser.parse_args()
    # This CLI accepts only an explicitly staged isolated fixture approval.
    policy=life.read(ROOT/"fixture_approval.json")
    result=run(args.case,args.entry,args.label,policy)
    print(json.dumps(result))
    return {"CANDIDATE_NEW_EVIDENCE":0,"CANDIDATE_SAME_DAY_RECHECK":10,
            "SKIPPED_LOCK_HELD":20}.get(result["status"],30)

if __name__=="__main__":
    raise SystemExit(main())
