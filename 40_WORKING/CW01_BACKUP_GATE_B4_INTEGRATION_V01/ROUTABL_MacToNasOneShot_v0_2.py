"""Fixture-only process adapter. Never accepts an executable or arbitrary argv."""
from datetime import datetime
import os
import signal
import subprocess
import sys
import time

from backup_runner_candidate import KST, Step, Stop, run_stages
import ROUTABL_BackupEvidenceAdapter_v0_1 as evidence

def live_group(pgid):
    result = subprocess.run(["/bin/ps", "-axo", "pid=,pgid=,stat="], capture_output=True,
                            check=True, text=True, timeout=2)
    return [int(pid) for pid, group, status in (row.split() for row in result.stdout.splitlines())
            if int(group) == pgid and not status.startswith("Z")]

def stop_group(pgid, sig):
    try:
        os.killpg(pgid, sig)
    except ProcessLookupError:
        pass

def cleanup(process):
    stop_group(process.pid, signal.SIGTERM)
    time.sleep(0.12)
    stop_group(process.pid, signal.SIGKILL)
    process.communicate(timeout=2)
    until = time.monotonic() + 2
    while (remaining := live_group(process.pid)) and time.monotonic() < until:
        time.sleep(0.02)
    if remaining:
        raise Stop("FAILED_SAFE", "LIVE_FIXTURE_DESCENDANTS")

class Port:
    def __init__(self, base, timeout=1.5):
        self.base = evidence.safe(base)
        self.timeout = timeout
        self.processes = []

    def now(self):
        return datetime.now(KST)

    def inventory(self):
        return evidence.inventory(self.base)

    def previous_local(self):
        return evidence.local(self.base)

    def previous_nas(self):
        return evidence.nas(self.base)

    def child(self, stage):
        if stage not in ("gate", "nas"):
            raise ValueError("Invalid fixture stage")
        process = subprocess.Popen(
            [sys.executable, "-I", "-B", str(evidence.ROOT / "fixture_worker.py"), self.base.name, stage],
            cwd=evidence.ROOT, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, start_new_session=True, close_fds=True,
            env={"PATH": "/usr/bin:/bin", "TMPDIR": str(self.base), "HOME": str(self.base)})
        try:
            stdout, _ = process.communicate(timeout=self.timeout)
        except subprocess.TimeoutExpired:
            cleanup(process)
            self.processes.append(dict(stage=stage, pid=process.pid, exit_code=process.returncode,
                                       live_descendants=live_group(process.pid), timed_out=True))
            raise TimeoutError()
        except BaseException:
            cleanup(process)
            raise
        if live_group(process.pid):
            cleanup(process)
            raise Stop("FAILED_SAFE", "UNEXPECTED_FIXTURE_DESCENDANT")
        self.processes.append(dict(stage=stage, pid=process.pid, exit_code=process.returncode,
                                   live_descendants=[], timed_out=False))
        return stdout, process.returncode

    def local(self, current):
        return evidence.gate_result(*self.child("gate"), current,
                                    lambda: evidence.local(self.base))

    def nas(self, local, created):
        return evidence.nas_result(*self.child("nas"), lambda: evidence.nas(self.base))

    def final(self, current, local, nas):
        verified = evidence.final_chain(self.base, current, local, nas)
        return Step("CHAIN_VERIFIED" if verified else "FAILED", 0, True, verified)

    def run(self, start, record):
        return run_stages(self, start, record)
