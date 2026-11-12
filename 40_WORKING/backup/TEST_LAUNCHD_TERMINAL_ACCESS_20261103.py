from pathlib import Path
import os,unicodedata,json,datetime
out=Path("/Users/yongho/ROUTABL-TechAssets/40_WORKING/TEST_LAUNCHD_TERMINAL_ACCESS_RESULT.json")
root=Path("/Volumes/SSD2TB/ROUTABL-TechAssets-Backup/ROUTABL-SecureBackup.sparsebundle/Info.plist")
drive=Path("/Users/yongho/Library/CloudStorage/GoogleDrive-pyh1772@gmail.com")
result={"time_utc":datetime.datetime.now(datetime.timezone.utc).isoformat()}
try:
 result["ssd_readable"]=len(root.read_bytes())>0
except Exception as e:result["ssd_error"]=type(e).__name__+":"+str(getattr(e,"errno",None))
try:
 my=next(drive/x for x in os.listdir(drive) if unicodedata.normalize("NFC",x)=="내 드라이브")
 result["drive_list_ok"]="ROUTABL-TechAssets-Backup" in [unicodedata.normalize("NFC",x) for x in os.listdir(my)]
except Exception as e:result["drive_error"]=type(e).__name__+":"+str(getattr(e,"errno",None))
with out.open("x",encoding="utf-8") as f:json.dump(result,f,ensure_ascii=False,indent=2)
os.chmod(out,0o600)
print(json.dumps(result))
