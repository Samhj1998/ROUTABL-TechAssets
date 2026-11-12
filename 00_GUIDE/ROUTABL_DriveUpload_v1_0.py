#!/usr/bin/env python3
"""ROUTABL encrypted Drive delivery: fail-closed daily staging, optional File Provider copy.
Never sync, delete, rename or decrypt source archives. No credential use."""
import fcntl, hashlib, json, os, shutil, subprocess, sys, tempfile, unicodedata, zipfile
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

HOME=Path("/Users/yongho")
SSD=Path("/Volumes/SSD2TB")
NAS=Path("/Volumes/Dev_Assets")
STATE=HOME/"Library/Logs/ROUTABL-AssetBackup"
SOURCE_STATUS=STATE/"last_nas_result.json"
STATUS=STATE/"last_drive_result.json"
LOCK=STATE/"drive_upload.lock"
OUTBOX=SSD/"ROUTABL-TechAssets-Backup/DriveUploadOutbox"
MOUNT=HOME/"Library/CloudStorage/GoogleDrive-pyh1772@gmail.com"
TARGET_FOLDER="ROUTABL-TechAssets-Backup"
def now(): return datetime.now(ZoneInfo("Asia/Seoul"))
def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def report(row):
 row["checked_at_kst"]=now().isoformat()
 fd,tmp=tempfile.mkstemp(dir=STATE,prefix=".drive-result-")
 try:
  with os.fdopen(fd,"w",encoding="utf-8") as f:json.dump(row,f,ensure_ascii=False,indent=2)
  os.chmod(tmp,0o600);os.replace(tmp,STATUS)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
 print(json.dumps(row,ensure_ascii=False),flush=True)
def main():
 os.umask(0o077)
 if os.geteuid()==0 or not os.path.ismount(SSD) or not os.path.ismount(NAS):
  raise RuntimeError("SSD_or_NAS_offline")
 if Path("/Volumes/ROUTABL-Secure").exists():
  raise RuntimeError("encrypted_image_is_mounted")
 if not STATE.is_dir() or STATE.is_symlink():raise RuntimeError("unsafe_log_directory")
 with LOCK.open("a+") as lock:
  os.chmod(LOCK,0o600)
  try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:
   print('{"status":"SKIPPED_ALREADY_RUNNING"}');return 0
  today=now().date().isoformat()
  nas_status=json.loads(SOURCE_STATUS.read_text(encoding="utf-8"))
  if nas_status.get("status")!="SUCCESS" or nas_status.get("day_kst")!=today:
   raise RuntimeError("today_NAS_backup_not_success")
  nas_path=Path(nas_status.get("nas_snapshot",""))
  if not str(nas_path).startswith(str(NAS/"ROUTABL-TechAssets-Backup/snapshots/NAS_AUTO_")) or not nas_path.is_dir():
   raise RuntimeError("unexpected_NAS_snapshot_path")
  receipt_path=nas_path/"NAS_ENCRYPTED_BACKUP_RECEIPT.json"
  receipt=json.loads(receipt_path.read_text(encoding="utf-8"))
  image=nas_path/"ROUTABL-SecureBackup.sparsebundle"
  files=sorted(p for p in image.rglob("*") if p.is_file())
  expected={item["path"]:item["sha256"] for item in receipt["files"]}
  if not files or len(files)!=len(expected) or any(p.is_symlink() for p in image.rglob("*")):
   raise RuntimeError("NAS_snapshot_filecount_or_symlinks")
  if sum(p.stat().st_size for p in files)>2_000_000_000:
   raise RuntimeError("NAS_source_exceeds_2GB")
  for source in files:
   rel=source.relative_to(image).as_posix()
   if expected.get(rel)!=sha(source):raise RuntimeError("NAS_source_hash_changed_"+rel)
  metadata=subprocess.run(["/usr/sbin/diskutil","image","info",str(image)],
                         capture_output=True,text=True,timeout=40)
  if metadata.returncode or "Is Encrypted: 1" not in metadata.stdout or "Key Size: 256" not in metadata.stdout:
   raise RuntimeError("NAS_image_AES256_not_verified")
  OUTBOX.mkdir(parents=True,exist_ok=True,mode=0o700)
  target=OUTBOX/("ROUTABL-SecureBackup_"+nas_path.name+".zip")
  if not target.is_file():
   with zipfile.ZipFile(target,mode="x",compression=zipfile.ZIP_STORED,allowZip64=True) as z:
    for source in files:
     z.write(source,arcname="ROUTABL-SecureBackup.sparsebundle/"+source.relative_to(image).as_posix())
   os.chmod(target,0o600)
  with zipfile.ZipFile(target) as z:
   if len(z.infolist())!=len(expected) or z.testzip() is not None:raise RuntimeError("ZIP_integrity_failure")
   for entry in z.infolist():
    if not entry.filename.startswith("ROUTABL-SecureBackup.sparsebundle/"):raise RuntimeError("ZIP_member_invalid")
    name=entry.filename.split("/",1)[1]
    hh=hashlib.sha256()
    with z.open(entry) as f:
     for chunk in iter(lambda:f.read(1048576),b""):hh.update(chunk)
    if expected.get(name)!=hh.hexdigest():raise RuntimeError("ZIP_member_hash_mismatch_"+name)
  checksum=sha(target)
  result={"status":"STAGED_NOT_UPLOADED","day_kst":today,"source_nas_snapshot":str(nas_path),
          "staged_zip":str(target),"size":target.stat().st_size,"sha256":checksum,
          "zip_members_verified":len(expected),"google_drive_server_verified":False}
  if not MOUNT.is_dir():
   result["reason"]="google_drive_fileprovider_not_mounted";report(result);return 3
  drive_root=next((MOUNT/name for name in os.listdir(MOUNT)
                   if unicodedata.normalize("NFC",name)=="내 드라이브"),None)
  if drive_root is None:
   result["reason"]="my_drive_not_found";report(result);return 3
  try:
   names=os.listdir(drive_root)
  except OSError as e:
   result["reason"]="mac_fileprovider_unavailable_errno_"+str(e.errno)
   report(result);return 3
  folders=[name for name in names if unicodedata.normalize("NFC",name)==TARGET_FOLDER]
  if len(folders)!=1:
   result["reason"]="destination_folder_not_exactly_found";report(result);return 3
  destination=drive_root/folders[0]/target.name
  if destination.exists():
   try:
    if destination.is_file() and destination.stat().st_size==target.stat().st_size and sha(destination)==checksum:
     result["status"]="ALREADY_COPIED_TO_PROVIDER_PENDING_SERVER_VERIFICATION"
     result["reason"]="verify_Google_Drive_API_before_cloud_success"
     report(result);return 0
   except OSError:
    pass
   result["reason"]="destination_name_exists_but_unverified";report(result);return 3
  try:
   with target.open("rb") as inp,destination.open("xb") as out:
    shutil.copyfileobj(inp,out,1048576)
   if sha(destination)!=checksum:raise RuntimeError("fileprovider_local_copy_hash_failed")
  except Exception as e:
   result["reason"]="fileprovider_write_failed_"+type(e).__name__
   report(result);return 3
  result["status"]="COPIED_TO_DRIVE_PROVIDER_PENDING_SERVER_VERIFICATION"
  result["reason"]="wait_for_remote_Drive_API_confirmation"
  result["google_drive_local_path"]=str(destination)
  report(result);return 0
if __name__=="__main__":
 try:sys.exit(main())
 except Exception as e:
  try:report({"status":"FAILED","reason":str(e)[:200],"day_kst":now().date().isoformat()})
  except Exception:print("BACKUP_ERROR "+type(e).__name__,file=sys.stderr)
  sys.exit(1)
