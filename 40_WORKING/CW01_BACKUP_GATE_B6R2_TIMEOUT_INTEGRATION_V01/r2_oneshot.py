"""OneShot bridge from the verified B4 stage contract to R1 process cleanup."""
from datetime import datetime
from hashlib import sha256
import json

import b4_evidence as legacy
import b6_evidence
import r2_lifecycle as life
from backup_runner_candidate import KST, Step, Stop, run_stages

class Port:
    def __init__(self, base, lifecycle, policy, timeout, cleanup, media_clear, send_signal):
        self.base=base
        self.lifecycle=lifecycle
        self.policy=policy
        self.timeout=timeout
        self.cleanup=cleanup
        self.media_clear=media_clear
        self.send_signal=send_signal
        self.proofs=[]
        self.last_failure=None

    def now(self):
        return datetime.now(KST)

    def inventory(self):
        return legacy.inventory(self.base)

    def previous_local(self):
        return legacy.local(self.base)

    def previous_nas(self):
        return legacy.nas(self.base)

    def child(self,stage):
        report=life.run(self.lifecycle,stage,self.policy,case=self.base.name,work_timeout=self.timeout,
                        cleanup_timeout=self.cleanup,media_clear=self.media_clear,send_signal=self.send_signal)
        self.proofs.append({"stage":stage,**report})
        if report["status"] not in ("FIXTURE_COMPLETED","FIXTURE_COMPLETED_DELAYED"):
            self.last_failure=report["status"]
            raise TimeoutError(report["status"])
        done=report["fixture_payload"]
        rows=done["rows"]
        raw=b"invalid synthetic wire" if rows is None else b"".join(
            (json.dumps(row)+"\n").encode() for row in rows)
        return raw,done["wire_exit"]

    def local(self,current):
        return legacy.gate_result(*self.child("gate"),current,lambda:self.previous_local())

    def nas(self,local,created):
        return legacy.nas_result(*self.child("nas"),lambda:self.previous_nas())

    def final(self,current,local,nas):
        good=legacy.final_chain(self.base,current,local,nas)
        return Step("CHAIN_VERIFIED" if good else "FAILED",0,True,good)

    def inputs(self):
        current=self.inventory()
        manifest=legacy.read(self.base/"registry"/current.manifest_name)
        selected=[(row["target"],row["category"],legacy.read(self.base/"assets"/row["name"]))
                  for row in legacy.decode(legacy.read(self.base/"selection.json"))["files"]]
        return current.manifest_name,manifest,selected

    def capture(self,record):
        start=self.now()
        previous=self.previous_local()
        cas_path=self.base/"nas_receipt.json"
        prior_cas=sha256(legacy.read(cas_path)).hexdigest() if cas_path.is_file() else None
        name,manifest,selected=self.inputs()
        status,local,_=run_stages(self,start,record)
        created=status=="NEW_BACKUP_VERIFIED"
        after_name,after_manifest,after_selected=self.inputs()
        def component(row):
            if row["relative_path"]!="band":
                raise ValueError("UNAPPROVED_FIXTURE_COMPONENT")
            return [legacy.read(self.base/"cas_blob.bin")]
        bundle=dict(local=legacy.read(self.base/"local_status.json"),oneshot=legacy.read(self.base/"oneshot.json"),
                    cas=legacy.read(cas_path),receipt_raw=legacy.read(self.base/"local_receipt.json"),
                    registry_name=name,registry_bytes=manifest,selected_bytes=selected,
                    registry_name_after=after_name,registry_bytes_after=after_manifest,selected_bytes_after=after_selected,
                    cas_name="CAS_"+local.snapshot_id+".json",prior_snapshot_id=previous.snapshot_id if previous else None,
                    prior_receipt_sha256=previous.receipt_sha256 if previous else None,prior_cas_sha256=prior_cas,
                    read_component=component)
        observed=dict(outcome="CREATED" if created else "REUSED",performed_work=created,exit_code=0,
                      image_residual=self.media_clear() is not True,descendants_remaining=False)
        decision,proof=b6_evidence.evaluate(bundle,observed,start,self.now())
        return decision,proof
