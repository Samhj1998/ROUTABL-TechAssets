#!/usr/bin/env python3
"""ROUTABL Drive delivery v1.1: use locked local AES-256 image after verified NAS success.
Uploads only when macOS File Provider is available; never claims cloud success without API proof."""
import fcntl, hashlib, json, os, shutil, subprocess, sys, tempfile, unicodedata, zipfile
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
HOME=Path("/Users/yongho")
SSD=Path("/Volumes/SSD2TB")
IMAGE=SSD/"ROUTABL-TechAssets-Backup/ROUTABL-SecureBackup.sparsebundle"
OUTBOX=SSD/"ROUTABL-TechAssets-Backup/DriveUploadOutbox"
STATE=HOME/"Library/Logs/ROUTABL-AssetBackup"
SOURCE_STATUS=STATE/"last_nas_result.json"
STATUS=STATE/"last_drive_result.json"
LOCK=STATE/"drive_upload.lock"
MOUNT=HOME/"Library/CloudStorage/GoogleDrive-pyh1772@gmail.com"
DEST_NAME="ROUTABL-TechAssets-Backup"
MAX_BYTES=2_000_000_000
def now():return datetime.now(ZoneInfo("Asia/Seoul"))
def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def report(v):
 v["checked_at_kst"]=now().isoformat()
 fd,tmp=tempfile.mkstemp(dir=str(STATE),prefix=".drive-result-")
 try:
  with os.fdopen(fd,"w",encoding="utf-8") as f:json.dump(v,f,ensure_ascii=False,indent=2)
  os.chmod(tmp,0o600);os.replace(tmp,STATUS)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
 print(json.dumps(v,ensure_ascii=False),flush=True)
def main():
 os.umask(0o077)
 if os.geteuid()==0 or not os.path.ismount(SSD) or not IMAGE.is_dir() or IMAGE.is_symlink():
  raise RuntimeError("SSD_or_encrypted_image_unavailable")
 if Path("/Volumes/ROUTABL-Secure").exists():raise RuntimeError("encrypted_image_is_mounted")
 if not STATE.is_dir() or STATE.is_symlink():raise RuntimeError("log_directory_unavailable")
 with LOCK.open("a+") as lock:
  os.chmod(LOCK,0o600)
  try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  except BlockingIOError:
   print('{"status":"SKIPPED_ALREADY_RUNNING"}');return 0
  today=now().date().isoformat()
  data=json.loads(SOURCE_STATUS.read_text(encoding="utf-8"))
  if data.get("day_kst")!=today or data.get("status")!="SUCCESS" or data.get("image_mounted") is not False:
   raise RuntimeError("NAS_verification_not_successful_today")
  nas_name=Path(str(data.get("nas_snapshot",""))).name
  if not nas_name.startswith("NAS_AUTO_"+today.replace("-","")):
   raise RuntimeError("NAS_receipt_snapshot_name_invalid")
  check=subprocess.run(["/usr/sbin/diskutil","image","info",str(IMAGE)],
                       capture_output=True,text=True,timeout=40)
  if check.returncode==0:
   if "Is Encrypted: 1" not in check.stdout or "Key Size: 256" not in check.stdout:
    raise RuntimeError("SSD_image_AES256_unverified")
   crypt_basis="current_diskutil_AES256"
  else:
   if "Operation not permitted" not in check.stderr:
    raise RuntimeError("unexpected_diskutil_failure")
   import plistlib
   meta=plistlib.loads((IMAGE/"Info.plist").read_bytes())
   if meta.get("diskimage-bundle-type")!="com.apple.diskimage.sparsebundle" or meta.get("size")!=21474836480 or not (IMAGE/"token").is_file():
    raise RuntimeError("known_AES256_image_structure_mismatch")
   crypt_basis="today_NAS_verified_AES256_and_locked_local_image_structure"
  attached=subprocess.run(["/usr/bin/hdiutil","info"],capture_output=True,text=True,timeout=20)
  if attached.returncode==0 and str(IMAGE) in attached.stdout:raise RuntimeError("SSD_image_attached")
  files=sorted(p for p in IMAGE.rglob("*") if p.is_file())
  if (not files or len(files)!=data.get("file_count") or
      any(p.is_symlink() for p in IMAGE.rglob("*"))):
   raise RuntimeError("SSD_image_file_count_mismatch")
  if sum(p.stat().st_size for p in files)>MAX_BYTES:raise RuntimeError("SSD_image_too_large")
  original={p.relative_to(IMAGE).as_posix():{"sha256":sha(p),"bytes":p.stat().st_size,
                 "mtime_ns":p.stat().st_mtime_ns} for p in files}
  OUTBOX.mkdir(parents=True,exist_ok=True,mode=0o700)
  package=OUTBOX/("ROUTABL-SecureBackup_"+nas_name+".zip")
  if not package.exists():
   with zipfile.ZipFile(package,"x",compression=zipfile.ZIP_STORED,allowZip64=True) as z:
    for p in files:z.write(p,arcname="ROUTABL-SecureBackup.sparsebundle/"+p.relative_to(IMAGE).as_posix())
   os.chmod(package,0o600)
  if not package.is_file() or package.is_symlink():raise RuntimeError("invalid_outbox_package")
  with zipfile.ZipFile(package) as z:
   if len(z.infolist())!=len(files) or z.testzip() is not None:raise RuntimeError("ZIP_integrity_failed")
   for member in z.infolist():
    if not member.filename.startswith("ROUTABL-SecureBackup.sparsebundle/"):
     raise RuntimeError("ZIP_member_name_invalid")
    key=member.filename.split("/",1)[1]
    if key not in original:raise RuntimeError("unexpected_member")
    h=hashlib.sha256()
    with z.open(member) as f:
     for b in iter(lambda:f.read(1048576),b""):h.update(b)
    if h.hexdigest()!=original[key]["sha256"]:raise RuntimeError("ZIP_member_SHA_mismatch")
  if Path("/Volumes/ROUTABL-Secure").exists():raise RuntimeError("image_mounted_during_package")
  for p in files:
   name=p.relative_to(IMAGE).as_posix()
   s=p.stat()
   if s.st_size!=original[name]["bytes"] or s.st_mtime_ns!=original[name]["mtime_ns"] or sha(p)!=original[name]["sha256"]:
    raise RuntimeError("SSD_image_changed_during_package")
  checksum=sha(package)
  row={"status":"STAGED_NOT_UPLOADED","day_kst":today,"source":"SSD_AES256_LOCKED",
       "nas_success_snapshot":nas_name,"zip_path":str(package),
       "zip_bytes":package.stat().st_size,"zip_sha256":checksum,
       "all_member_hashes_verified":True,"encryption_check_basis":crypt_basis,"cloud_confirmed":False}
  try:
   root=next((MOUNT/x for x in os.listdir(MOUNT) if unicodedata.normalize("NFC",x)=="내 드라이브"),None)
   names=os.listdir(root) if root is not None else []
  except OSError as e:
   row["reason"]="fileprovider_access_errno_"+str(e.errno);report(row);return 3
  matches=[n for n in names if unicodedata.normalize("NFC",n)==DEST_NAME]
  if len(matches)!=1:
   row["reason"]="drive_target_folder_unavailable";report(row);return 3
  destination=root/matches[0]/package.name
  try:
   if destination.exists():
    if destination.is_file() and destination.stat().st_size==package.stat().st_size and sha(destination)==checksum:
     row["status"]="PROVIDER_COPY_EXISTS_CLOUD_UNVERIFIED";report(row);return 0
    row["reason"]="different_destination_file_exists";report(row);return 3
   with package.open("rb") as src,destination.open("xb") as dst:shutil.copyfileobj(src,dst,1048576)
   if sha(destination)!=checksum:raise RuntimeError("provider_hash_diff")
  except (OSError,RuntimeError) as e:
   row["reason"]="provider_copy_error_"+type(e).__name__;report(row);return 3
  row["status"]="COPIED_TO_PROVIDER_CLOUD_UNVERIFIED"
  row["destination"]=str(destination)
  report(row);return 0
if __name__=="__main__":
 try:sys.exit(main())
 except Exception as e:
  try:report({"status":"FAILED","reason":str(e)[:180],"day_kst":now().date().isoformat()})
  except Exception:print("FAILED "+type(e).__name__,file=sys.stderr)
  sys.exit(1)
