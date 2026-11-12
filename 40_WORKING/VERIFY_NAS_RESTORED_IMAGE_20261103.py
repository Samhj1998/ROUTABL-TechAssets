from pathlib import Path
import json,subprocess,hashlib,unicodedata,os
image=Path("/Users/yongho/ROUTABL-TechAssets/40_WORKING/NAS_INDEPENDENT_RESTORE_20261103_071431_KST/ROUTABL-SecureBackup.sparsebundle")
mount=Path("/Volumes/ROUTABL-RestoreVerify")
if not image.is_dir() or mount.exists():raise SystemExit("INVALID_PRECONDITION")
r=subprocess.run(["/usr/sbin/diskutil","image","info",str(image)],capture_output=True,text=True,timeout=20)
if r.returncode or "Is Encrypted: 1" not in r.stdout or "Key Size: 256" not in r.stdout:raise SystemExit("AES256_NOT_CONFIRMED")
report={"image":str(image),"aes256":True}
attached=False
try:
 try:
  r=subprocess.run(["/usr/sbin/diskutil","image","attach","--readOnly","--nobrowse","--mountPoint",str(mount),str(image)],input=b"",stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=18)
  attached=mount.is_dir()
  report["mount_result"]="PASS" if r.returncode==0 and attached else "FAILED_OR_KEYCHAIN_NOT_AVAILABLE"
  report["mount_returncode"]=r.returncode
 except subprocess.TimeoutExpired:
  attached=mount.is_dir()
  report["mount_result"]="TIMEOUT"
 if attached:
  paths=list(mount.glob("snapshots/*/ROUTABL-TechAssets/30_REGISTRY/asset_manifest_v0.3.json"))
  checks=[]
  for p in paths:
   h=hashlib.sha256(p.read_bytes()).hexdigest()
   ref=Path("/Users/yongho/ROUTABL-TechAssets/30_REGISTRY/asset_manifest_v0.3.json")
   checks.append({"relative_path":str(p.relative_to(mount)),"sha256":h,"matches_original":h==hashlib.sha256(ref.read_bytes()).hexdigest()})
  report["read_files"]=checks
finally:
 if attached:
  e=subprocess.run(["/usr/bin/hdiutil","detach",str(mount)],capture_output=True,text=True,timeout=25)
  report["ejected"]=e.returncode==0 and not mount.exists()
print(json.dumps(report,ensure_ascii=False))
