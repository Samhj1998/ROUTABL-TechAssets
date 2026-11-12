"""Fixed worker for R2 fixtures. No operational program, mount or network access."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import select
import signal
import sys
import time

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import b4_evidence as evidence

KST=timezone(timedelta(hours=9))

def write(base,name,data):
    with evidence.safe(base/name).open("xb") as file:
        file.write((json.dumps(data,sort_keys=True)+"\n").encode())

def local_receipt(base, stamp, current):
    snapshot=stamp.strftime("ASSET_V21_%Y%m%d_%H%M%S_KST_")+str(os.getpid())
    fields=dict(snapshot_name=snapshot,created_at_kst=stamp.isoformat(),manifest_name=current.manifest_name,
                manifest_sha256=current.manifest_sha256,selection_sha256=current.selection_sha256,
                file_count=current.file_count,source_bytes=current.total_bytes)
    records=[]
    for row in evidence.decode(evidence.read(base/"selection.json"))["files"]:
        raw=evidence.read(base/"assets"/row["name"])
        records.append(dict(relative_path=row["target"],category=row["category"],size=len(raw),
                            sha256=sha256(raw).hexdigest()))
    receipt=dict(**fields,type="ROUTABL_ASSET_V21_AES256_SELECTIVE_SNAPSHOT",
                 source_manifest=current.manifest_name,source_manifest_sha256=current.manifest_sha256,
                 all_snapshot_sha256_verified=True,records=records,
                 summary=dict(manifest_name=current.manifest_name,manifest_sha256=current.manifest_sha256,
                    selection_sha256=current.selection_sha256,total_files=current.file_count,
                    total_source_bytes=current.total_bytes))
    write(base,"local_receipt.json",receipt)
    write(base,"local_status.json",dict(**fields,receipt_sha256=sha256(evidence.read(base/"local_receipt.json")).hexdigest(),
          status="SUCCESS",locked_after_backup=True,sha256_verified=True))

def cas_receipt(base,stamp,mode):
    local=evidence.decode(evidence.read(base/"local_status.json"))
    blob=evidence.read(base/"cas_blob.bin")
    snapshot=local["snapshot_name"]
    link=dict(local_receipt_sha256=local["receipt_sha256"],manifest_sha256=local["manifest_sha256"],
              selection_sha256=local["selection_sha256"])
    component=sha256(blob).hexdigest()
    cas=dict(**link,type="ROUTABL_CIPHERTEXT_CAS_V01",cas_id="CAS-"+snapshot,local_snapshot_name=snapshot,
        completed=mode!="incomplete",components=1,ciphertext_sha256=component,ciphertext_bytes=len(blob),
        total_ciphertext_bytes=len(blob),created_kst=stamp.isoformat(),
        files=[dict(relative_path="band",size=len(blob),sha256=component,reference={"type":"blob"})])
    if mode=="mismatch":
        cas["local_receipt_sha256"]="0"*64
    write(base,"nas_receipt.json",cas)
    write(base,"oneshot.json",dict(**link,status="SUCCESS_LOCAL_TO_NAS_ENCRYPTED_CAS",aes_image_detached=True,
          local_snapshot=snapshot,nas_cas_manifest="CAS_"+snapshot+".json",manifest_name=local["manifest_name"],
          local_file_count=local["file_count"],cas_components=1,verified_at_kst=stamp.isoformat()))

def event(name,token,**fields):
    payload=dict(event=name,token=token,pid=os.getpid(),pgid=os.getpgrp(),sid=os.getsid(0),uid=os.geteuid(),**fields)
    os.write(1,(json.dumps(payload)+"\n").encode())

def stage(base,phase,mode):
    if phase=="gate":
        current=evidence.inventory(base)
        fields=dict(job="local",mode="check" if mode=="no_work" else "run",manifest=current.manifest_name,
                    files=current.file_count,manifest_sha256=current.manifest_sha256,
                    selection_sha256=current.selection_sha256)
        if mode=="child_lock":
            return [dict(job="local",state="ALREADY_RUNNING",executed=False)],0
        if mode=="exit7":
            return [],7
        if mode=="malformed":
            return None,0
        if mode in ("reuse","no_work"):
            return [dict(**fields,no_work_executed=True,gate="SKIPPED_CURRENT_SNAPSHOT_VERIFIED" if mode=="reuse"
                          else "READY_FOR_LOCAL_ONCE")],0
        local_receipt(base,datetime.now(KST),current)
        return [dict(**fields,no_work_executed=False,gate="READY_FOR_LOCAL_ONCE"),
                dict(job="local",result="SUCCESS",receipt_chain_verified=True,manifest_sha256=current.manifest_sha256,
                     selection_sha256=current.selection_sha256)],0
    if mode=="reindex":
        return [dict(result="SNAPSHOT_ALREADY_INDEXED")],0
    if mode=="change":
        with evidence.safe(base/"assets/asset").open("ab") as file:
            file.write(b" changed")
    if mode!="missing":
        cas_receipt(base,datetime.now(KST),mode)
    return [dict(result="INCREMENTAL_SNAPSHOT_VERIFIED")],0

def main(phase,token,case):
    base=evidence.fixture(case)
    mode=evidence.decode(evidence.read(base/"config.json"))[phase]
    if mode=="resistant":
        signal.signal(signal.SIGTERM,signal.SIG_IGN)
    started=time.monotonic()
    event("READY",token)
    if mode=="hold":
        write(base,"ready.json",{"pid":os.getpid()})
        time.sleep(.8)
    if mode=="hang":
        if select.select([0],[],[],4)[0]:
            os.read(0,1)
        return 3
    if mode=="resistant":
        time.sleep(2)
        return 3
    if mode=="escape":
        if os.fork()==0:
            os.setsid()
            event("DESCENDANT",token)
            time.sleep(2)
            os._exit(0)
        if select.select([0],[],[],4)[0]:
            os.read(0,1)
        return 3
    rows,code=stage(base,phase,mode)
    event("DONE",token,elapsed_seconds=time.monotonic()-started,rows=rows,wire_exit=code)
    return 0

if __name__=="__main__":
    raise SystemExit(main(*sys.argv[1:]))
