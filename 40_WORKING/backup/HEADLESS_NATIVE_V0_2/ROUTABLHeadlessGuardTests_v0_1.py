#!/usr/bin/env python3
"""Offline real guard-path unit tests. Never invokes backup or launchd."""
import importlib.util
import json
import os
import stat
import tempfile
from pathlib import Path
from unittest.mock import patch

SOURCE=Path("/Users/yongho/ROUTABL-TechAssets/00_GUIDE/ROUTABL_BackupHeadlessSupervisor_v0_1.py")
spec=importlib.util.spec_from_file_location("routabl_guard_test",str(SOURCE))
p=importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)

tests=[]
def record(name,passed):
    assert passed,name
    tests.append(name)
    print("PASS",name,flush=True)

with tempfile.TemporaryDirectory(prefix="ROUTABL_HEADLESS_GUARD_ISOLATED_") as scratch:
    base=Path(scratch)
    p.HOME=base
    p.ROOT=base/"assets"
    p.LOG=base/"logs"
    p.LOG.mkdir()
    p.SSD=base/"SSD"
    p.NAS=base/"NAS"
    p.SSD.mkdir()
    p.NAS.mkdir()
    p.MOUNT=base/"ROUTABL-Secure"
    p.IMAGE=p.SSD/"ROUTABL-SecureBackup.sparsebundle"
    p.IMAGE.mkdir()
    p.MANIFESTS=p.NAS/"CAS/manifests"
    p.MANIFESTS.mkdir(parents=True)
    (p.MANIFESTS/"CAS_ASSET_V21_FAKE.json").write_text("{}",encoding="utf8")
    p.RUNNER=base/"runner.py"
    p.CAS=base/"cas.py"
    p.GATE=base/"gate.py"
    for x in (p.RUNNER,p.CAS,p.GATE):
        x.write_text("print('offline fixture')\n",encoding="utf8")
    p.APPROVAL=base/"approval_v01.json"
    p.LOCK=p.LOG/"offline.lock"
    p.STATUS=p.LOG/"status.json"
    p.LAST=p.LOG/"last.json"
    p.LOCAL=p.LOG/"local.json"
    expected_uid=os.getuid()
    record("SANDBOX_USER_MATCHES_501",expected_uid==501)
    p.EXPECTED_UID=expected_uid
    mounts={str(p.SSD),str(p.NAS)}
    with patch.object(p.os.path,"ismount",side_effect=lambda v:str(v) in mounts):
        stages=p.checks()
        record("TEN_REAL_PRECONDITION_STAGES_PASS",len(stages)==10 and
               all(r["state"]=="PASS" for r in stages))
        record("MISSING_APPROVAL_IS_DISARMED",p.approval_check()=="DISARMED_NO_APPROVAL")
        p.MOUNT.mkdir()
        record("OPEN_IMAGE_BLOCKS_BACKUP",
               any(r["stage"]=="source_encrypted_image_closed" and r["state"]=="BLOCKED"
                   for r in p.checks()))
        p.MOUNT.rmdir()
        mounts.remove(str(p.SSD))
        record("SSD_MISSING_BLOCKS_BACKUP",
               any(r["stage"]=="ssd_mounted" and r["state"]=="BLOCKED" for r in p.checks()))
        mounts.add(str(p.SSD))
        mounts.remove(str(p.NAS))
        record("NAS_MISSING_BLOCKS_BACKUP",
               any(r["stage"]=="nas_mounted" and r["state"]=="BLOCKED" for r in p.checks()))
        mounts.add(str(p.NAS))
        valid={
            "approval_version":1,
            "owner_uid":expected_uid,
            "enabled":True,
            "scope":"MAC_SSD_AES256_TO_NAS_CAS_ONLY",
            "scheduled_hour_kst":4,
            "scheduled_minute_kst":30,
            "drive_upload":False,
            "allow_pruning":False,
            "runner_sha256":p.sha(p.RUNNER),
            "nas_engine_sha256":p.sha(p.CAS),
            "local_gate_sha256":p.sha(p.GATE)
        }
        def write_policy(conf,mode=0o600):
            p.APPROVAL.write_text(json.dumps(conf),encoding="utf8")
            p.APPROVAL.chmod(mode)
        write_policy(valid)
        record("APPROVED_FAKE_POLICY_REACHABLE",p.approval_check()=="APPROVED")
        p.RUNNER.write_text("changed source\n",encoding="utf8")
        record("SCRIPT_HASH_CHANGE_DISARMS",
               p.approval_check()=="DISARMED_PROGRAM_INTEGRITY_CHANGED")
        p.RUNNER.write_text("print('offline fixture')\n",encoding="utf8")
        too_permissive=dict(valid)
        write_policy(too_permissive,0o644)
        record("UNSAFE_APPROVAL_PERMISSIONS_DISARM",
               p.approval_check()=="DISARMED_APPROVAL_PERMISSIONS")
        mutated=dict(valid)
        mutated["drive_upload"]=True
        write_policy(mutated)
        record("DRIVE_TRANSFER_POLICY_DISARM",
               p.approval_check()=="DISARMED_APPROVAL_POLICY")
        mutated=dict(valid)
        mutated["allow_pruning"]=True
        write_policy(mutated)
        record("PRUNING_POLICY_DISARM",p.approval_check()=="DISARMED_APPROVAL_POLICY")
        mutated=dict(valid)
        mutated["owner_uid"]=999
        write_policy(mutated)
        record("UID_MISMATCH_DISARM",p.approval_check()=="DISARMED_APPROVAL_POLICY")
        p.APPROVAL.write_text("{invalid",encoding="utf8")
        record("INVALID_JSON_DISARM",p.approval_check()=="DISARMED_INVALID_APPROVAL")
        record("NO_LIVE_BACKUP_OR_NAS_COPY_CALLED",not p.STATUS.exists() and not p.LAST.exists())
print("ROUTABL_HEADLESS_GUARD_REAL_BRANCH_TESTS_PASS",len(tests),flush=True)
