"""B6 supervisor candidate. No operational launcher or credential access."""
import fcntl
import hashlib
import json
import os
import re
import stat
import tempfile
from datetime import datetime
from pathlib import Path

from ROUTABL_MacToNasOneShot_v0_2 import collect

ROOT = Path(__file__).resolve().parent
LABEL = "com.routabl.assetbackup.native.v043"
FILES = ("ROUTABL_BackupHeadlessSupervisor_v0_3.py","ROUTABL_MacToNasOneShot_v0_2.py",
         "ROUTABL_BackupEvidenceAdapter_v0_1.py","ROUTABL_BackupEvidenceNormalizer_v0_1.py")
EXITS = {"CANDIDATE_NEW_EVIDENCE":0, "CANDIDATE_SAME_DAY_RECHECK":10, "SKIPPED_LOCK_HELD":20}
SHA = re.compile(r"[0-9a-f]{64}")
TEAM = re.compile(r"[A-Z0-9]{10}")

def workspace(path):
    path = Path(path)
    if not path.is_absolute() or not path.is_dir() or ROOT not in path.parents or path.resolve() != path:
        raise ValueError("FIXTURE_ROOT_REQUIRED")
    info = path.stat()
    if info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o700:
        raise ValueError("PRIVATE_FIXTURE_ROOT_REQUIRED")
    return path

def pins():
    result = {}
    for name in FILES:
        fd = os.open(ROOT/name, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd,"rb") as source:
            if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
                raise ValueError("PIN_FILE_NOT_REGULAR")
            result[name] = hashlib.sha256(source.read()).hexdigest()
    return result

def identity(info):
    return info.st_dev,info.st_ino

def fixture_policy(policy, signature, before, entry):
    if (policy.get("schema") != "b6.1" or policy.get("scope") != "ISOLATED_FIXTURE"
            or policy.get("deployment_enabled") is not False
            or policy.get("label") != LABEL or policy.get("schedule_kst") != "04:30"
            or policy.get("entries") != ["scheduled","manual"] or entry not in policy["entries"]):
        return "BLOCKED_POLICY"
    signer = policy["fixture_signer"]
    if (not isinstance(signer.get("team_id"),str) or not TEAM.fullmatch(signer["team_id"])
            or not isinstance(signer.get("requirement"),str) or not signer["requirement"]
            or not isinstance(signer.get("binary_sha256"),str) or not SHA.fullmatch(signer["binary_sha256"])
            or signer != signature):
        return "BLOCKED_SIGNATURE"
    if policy.get("pins") != before:
        return "BLOCKED_PROGRAM_PIN"
    return None

def emit(path, data):
    with tempfile.NamedTemporaryFile(dir=path, prefix=".result-", delete=False) as handle:
        stage = Path(handle.name)
        try:
            handle.write((json.dumps(data,ensure_ascii=False,sort_keys=True)+"\n").encode())
            handle.flush()
            os.fsync(handle.fileno())
            os.replace(stage,path/"result.json")
        finally:
            stage.unlink(missing_ok=True)
    directory = os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)

def run(path, policy, signature, entries, entry, dedicated_write_granted, engine, clock):
    status, details = "BLOCKED_POLICY", {}
    lock = None
    owns_current_lock = False
    path = workspace(path)
    try:
        if entries != [LABEL]:
            status = "BLOCKED_MULTIPLE_ENTRYPOINTS"
        else:
            lockpath = path/"run.lock"
            lock = os.open(lockpath,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
            info = os.fstat(lock)
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid()
                    or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1):
                raise ValueError("INVALID_LOCK")
            try:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:
                status = "SKIPPED_LOCK_HELD"
            else:
                if identity(info) != identity(lockpath.lstat()):
                    status = "BLOCKED_LOCK_REPLACED"
                else:
                    owns_current_lock = True
                    before = pins()
                    denied = fixture_policy(policy,signature,before,entry)
                    if denied:
                        status = denied
                    elif dedicated_write_granted is not True:
                        status = "BLOCKED_WRITE_CAPABILITY"
                    else:
                        status,details = collect(engine,clock(),clock)
                        if identity(info) != identity(lockpath.lstat()):
                            owns_current_lock = False
                            status,details = "BLOCKED_LOCK_REPLACED", {}
                        elif before != pins():
                            status,details = "BLOCKED_PROGRAM_PIN_CHANGED", {}
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        status,details = "BLOCKED_PREFLIGHT", {}
    report = dict(schema="b6.1", scope="ISOLATED_FIXTURE", status=status,
                  exit_code=EXITS.get(status,30), actual_backup_success=False,
                  production_deployment=False, details=details)
    try:
        # A contender must never overwrite the active owner's eventual receipt.
        if owns_current_lock and identity(os.fstat(lock)) == identity(lockpath.lstat()):
            emit(path,report)
    except OSError:
        report.update(status="FAILED_RESULT_PUBLICATION",exit_code=30,details={})
    finally:
        if lock is not None:
            os.close(lock)
    return report

if __name__ == "__main__":
    print(json.dumps(dict(schema="b6.1",scope="DISABLED",status="BLOCKED_NO_PRODUCTION_ADAPTER",
                          exit_code=30,actual_backup_success=False,production_deployment=False)))
    raise SystemExit(30)
