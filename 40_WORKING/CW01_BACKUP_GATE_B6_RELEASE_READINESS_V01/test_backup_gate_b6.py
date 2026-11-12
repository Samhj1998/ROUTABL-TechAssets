"""Integration tests for B6 only. No operational program or storage path is used."""
import copy
import fcntl
import json
import os
import sys
import tempfile
from datetime import timedelta
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch

import ROUTABL_BackupHeadlessSupervisor_v0_3 as supervisor
from ROUTABL_MacToNasOneShot_v0_2 import FixtureEngine
from ROUTABL_BackupEvidenceAdapter_v0_1 import selection

sys.path.insert(0,str(Path(__file__).resolve().parent/"_regression"/"b5"))
from test_backup_gate_b5 import (fixture, encode, NOW, MANIFEST_BYTES, M, CAS_NAME,
                                escaped_group_probe, pin_probe, lock_inode_probe)

ROOT = Path(__file__).resolve().parent
LABEL = supervisor.LABEL

def base(reuse=False):
    local,one,cas,receipt=fixture()
    items=[("projects/\ud55c\uae00.txt","project",b"synthetic contents"),
           ("registered_assets/one","registry",b"separate input")]
    sh,count,size=selection(items)
    for row, item in zip(receipt["records"],items):
        row.update(sha256=sha256(item[2]).hexdigest(),size=len(item[2]))
    for data in (local,one,cas,receipt,receipt["summary"]):
        data["selection_sha256"]=sh
    local.update(file_count=count,source_bytes=size)
    receipt["summary"].update(total_files=count,total_source_bytes=size)
    receipt_raw=encode(receipt)
    local["receipt_sha256"]=one["local_receipt_sha256"]=cas["local_receipt_sha256"]=sha256(receipt_raw).hexdigest()
    components={"bands/1":b"encrypted first","token":b"encrypted second"}
    for row in cas["files"]:
        chunk=components[row["relative_path"]]
        row.update(size=len(chunk),sha256=sha256(chunk).hexdigest())
    cas["total_ciphertext_bytes"]=sum(map(len,components.values()))
    cas_raw=encode(cas)
    bundle=dict(local=encode(local),oneshot=encode(one),cas=cas_raw,registry_name=M,
                registry_bytes=MANIFEST_BYTES,registry_name_after=M,registry_bytes_after=MANIFEST_BYTES,
                cas_name=CAS_NAME,receipt_raw=receipt_raw,selected_bytes=items,
                selected_bytes_after=list(items),read_component=lambda row:[components[row["relative_path"]]])
    if reuse:
        bundle.update(prior_snapshot_id=local["snapshot_name"],prior_receipt_sha256=local["receipt_sha256"],
                      prior_cas_sha256=sha256(cas_raw).hexdigest())
    child=dict(outcome="REUSED" if reuse else "CREATED",performed_work=not reuse,exit_code=0,
               image_residual=False,descendants_remaining=False)
    return bundle,child

def change(data,key,**updates):
    value=json.loads(data[key])
    value.update(updates)
    data[key]=encode(value)

def main():
    cases=[]
    identity=dict(team_id="FIXTURE123",requirement="fixture-only",binary_sha256="a"*64)
    original_pins=supervisor.pins()
    policy=dict(schema="b6.1",scope="ISOLATED_FIXTURE",deployment_enabled=False,label=LABEL,
                entries=["scheduled","manual"],schedule_kst="04:30",pins=original_pins,
                fixture_signer=identity)
    def record(name,expected,actual,details=None):
        cases.append(dict(case=name,expected=expected,actual=actual,
                          verdict="PASS" if expected==actual else "FAIL",details=details))
    with tempfile.TemporaryDirectory(prefix="b6-case-",dir=ROOT) as tmp:
        path=Path(tmp)
        def run(name,expected,tweak=None,reuse=False,configure=None):
            bundle,child=base(reuse)
            if tweak:
                tweak(bundle,child)
            times=iter([NOW+timedelta(minutes=1) if reuse else NOW-timedelta(minutes=10),
                        NOW+timedelta(minutes=2)])
            opts=dict(policy=copy.deepcopy(policy),signature=identity.copy(),entries=[LABEL],
                      entry="manual",dedicated_write_granted=True,engine=FixtureEngine(lambda:(bundle,child)),
                      clock=lambda:next(times))
            if configure:
                configure(opts)
            result=supervisor.run(path,**opts)
            expected_exit={"CANDIDATE_NEW_EVIDENCE":0,"CANDIDATE_SAME_DAY_RECHECK":10,
                           "SKIPPED_LOCK_HELD":20}.get(expected,30)
            acceptable=result["actual_backup_success"] is False and result["production_deployment"] is False \
                       and result["exit_code"] == expected_exit
            record(name,expected,result["status"] if acceptable else "CONTRACT_VIOLATION",result)
            return result

        run("fresh_fixture_verified","CANDIDATE_NEW_EVIDENCE")
        receipt=json.loads((path/"result.json").read_bytes())
        record("atomic_result_readback",True,receipt["status"]=="CANDIDATE_NEW_EVIDENCE"
               and not list(path.glob(".result-*")))
        run("same_day_preexisting_recheck","CANDIDATE_SAME_DAY_RECHECK",reuse=True)
        run("unbound_reuse","REUSE_NOT_PREEXISTING",lambda b,c:b.update(prior_cas_sha256="f"*64),reuse=True)
        run("child_lock_skip","SKIPPED_LOCK_HELD",lambda b,c:c.update(outcome="LOCK_HELD",performed_work=False))
        run("zero_exit_without_work","NO_NEW_BACKUP_EVIDENCE",lambda b,c:c.update(outcome="READY",performed_work=False))
        run("duplicate_agent_registration","BLOCKED_MULTIPLE_ENTRYPOINTS",
            configure=lambda a:a.update(entries=[LABEL,"com.routabl.assetbackup.native.v042"]))
        before=(path/"result.json").read_bytes()
        with (path/"run.lock").open("rb") as active:
            fcntl.flock(active,fcntl.LOCK_EX|fcntl.LOCK_NB)
            run("same_lock_contention","SKIPPED_LOCK_HELD")
        record("contender_does_not_replace_result",True,before==(path/"result.json").read_bytes())
        (path/"writable-by-same-uid").write_bytes(b"direct write without supervisor")
        record("same_uid_path_still_writable","BYPASS_NOT_BLOCKED",
               "BYPASS_NOT_BLOCKED" if (path/"writable-by-same-uid").is_file() else "UNEXPECTED")
        def must_not_run():
            raise AssertionError("engine executed with denied capability")
        run("modeled_dedicated_write_denied","BLOCKED_WRITE_CAPABILITY",configure=lambda a:a.update(
            dedicated_write_granted=False,engine=FixtureEngine(must_not_run)))
        run("program_pin_mismatch","BLOCKED_PROGRAM_PIN",configure=lambda a:a["policy"]["pins"].update(
            {supervisor.FILES[0]:"0"*64}))
        run("signature_team_mismatch","BLOCKED_SIGNATURE",configure=lambda a:a["signature"].update(team_id="BADTEAM123"))
        run("approval_activation_rejected","BLOCKED_POLICY",configure=lambda a:a["policy"].update(deployment_enabled=True))
        run("production_engine_is_not_callable","BLOCKED_ENGINE_UNAPPROVED",configure=lambda a:a.update(engine=object()))
        run("old_v019_metadata_cannot_be_current","STALE_REGISTRY_BACKUP",lambda b,c:(
            change(b,"local",manifest_name="asset_manifest_v0.19.json"),
            change(b,"oneshot",manifest_name="asset_manifest_v0.19.json"),
            replace_receipt_registry(b,"asset_manifest_v0.19.json")))
        run("independent_selection_differs","SELECTION_CHANGED",lambda b,c:b.update(
            selected_bytes=[("other","project",b"changed")]))
        run("selection_mutates_mid_run","SELECTION_OR_REGISTRY_CHANGED_DURING_RUN",
            lambda b,c:b.update(selected_bytes_after=[("other","project",b"changed")]))
        run("registry_mutates_mid_run","SELECTION_OR_REGISTRY_CHANGED_DURING_RUN",
            lambda b,c:b.update(registry_bytes_after=b"other registry"))
        run("missing_local_original","LOCAL_ORIGINAL_MISSING",lambda b,c:b.pop("receipt_raw"))
        run("cas_verifier_missing","CAS_COMPONENTS_NOT_VERIFIED",lambda b,c:b.pop("read_component"))
        run("cas_component_wrong_bytes","CAS_COMPONENTS_NOT_VERIFIED",lambda b,c:b.update(
            read_component=lambda row:[b"wrong"]))
        run("nas_lineage_mismatch","EVIDENCE_INVALID",lambda b,c:change(b,"cas",local_receipt_sha256="0"*64))
        def timeout():
            raise TimeoutError()
        run("child_timeout","FAILED_CHILD",configure=lambda a:a.update(engine=FixtureEngine(timeout)))
        run("child_nonzero","FAILED_CHILD",lambda b,c:c.update(exit_code=9))
        run("escaped_child_report","FAILED_CHILD",lambda b,c:c.update(outcome="ESCAPED"))
        run("descendant_still_running","BLOCKED_RESIDUAL",lambda b,c:c.update(descendants_remaining=True))
        run("mounted_image_remains","BLOCKED_RESIDUAL",lambda b,c:c.update(image_residual=True))
        with tempfile.TemporaryDirectory(dir=path) as probe:
            area=Path(probe)
            ok,details=pin_probe(area)
            record("os_post_pin_code_replacement",True,ok,details)
            ok,details=lock_inode_probe(area)
            record("os_lock_inode_replacement",True,ok,details)
        def pin_changes():
            return {**original_pins,supervisor.FILES[0]:"0"*64}
        with patch.object(supervisor,"pins",side_effect=[original_pins,pin_changes()]):
            run("supervisor_detects_post_run_pin_change","BLOCKED_PROGRAM_PIN_CHANGED")
        def swap_lock():
            old=path/"old-run.lock"
            (path/"run.lock").rename(old)
            fd=os.open(path/"run.lock",os.O_CREAT|os.O_EXCL|os.O_RDWR,0o600)
            os.close(fd)
            return base()
        run("supervisor_detects_lock_identity_replacement","BLOCKED_LOCK_REPLACED",
            configure=lambda a:a.update(engine=FixtureEngine(swap_lock)))
        ok,details=escaped_group_probe()
        record("os_detached_process_escape_and_cleanup",True,ok,details)
    count=sum(row["verdict"]=="PASS" for row in cases)
    print(json.dumps(dict(scope="ISOLATED_FIXTURE",passed=count,total=len(cases),cases=cases),indent=2))
    return 0 if count==len(cases) else 1

def replace_receipt_registry(bundle,name):
    receipt=json.loads(bundle["receipt_raw"])
    receipt["manifest_name"]=receipt["source_manifest"]=name
    receipt["summary"]["manifest_name"]=name
    bundle["receipt_raw"]=encode(receipt)
    digest=sha256(bundle["receipt_raw"]).hexdigest()
    change(bundle,"local",receipt_sha256=digest)
    change(bundle,"oneshot",local_receipt_sha256=digest)
    change(bundle,"cas",local_receipt_sha256=digest)

if __name__=="__main__":
    raise SystemExit(main())
