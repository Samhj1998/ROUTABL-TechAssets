#!/usr/bin/env python3
from pathlib import Path
from hashlib import sha256
import zipfile,shutil,json,sys
source=Path.home()/"Downloads"/"ROUTABL_97-1_내부완결기준판_v4.1_20261102.zip"
root=Path("/Volumes/Dev_Assets/Routabl")
target=root/"97-1_최종내부기준판_v4.1_20261102"
expected="4f56d30d346c075347f890aca0e91b3c58a00672b0d85edb37a73cc1d84dea89"
def digest(p):return sha256(p.read_bytes()).hexdigest()
if not source.exists():sys.exit("SOURCE_NOT_DOWNLOADED: "+str(source))
if not root.is_dir():sys.exit("NAS_NOT_MOUNTED")
if digest(source)!=expected:sys.exit("SOURCE_SHA_MISMATCH")
with zipfile.ZipFile(source) as z:
 if z.testzip() or len(z.infolist())!=19:sys.exit("ZIP_CRC_OR_COUNT_FAILED")
 pdf=next((x for x in z.namelist() if x.endswith("01_라우터블개발백서_최종내부기준판_v4.1.pdf")),None)
 if pdf is None:sys.exit("PDF_MISSING")
 data=z.read(pdf)
target.mkdir(exist_ok=True)
destination=target/source.name
if destination.exists() and digest(destination)!=expected:sys.exit("DESTINATION_CONFLICT")
if not destination.exists():shutil.copy2(source,destination)
if digest(destination)!=expected:sys.exit("NAS_READBACK_MISMATCH")
pdfout=target/"01_라우터블개발백서_최종내부기준판_v4.1.pdf"
if pdfout.exists() and sha256(pdfout.read_bytes()).digest()!=sha256(data).digest():sys.exit("PDF_DESTINATION_CONFLICT")
if not pdfout.exists():pdfout.write_bytes(data)
if digest(pdfout)!=sha256(data).hexdigest():sys.exit("PDF_READBACK_MISMATCH")
receipt=dict(status="VERIFIED",sha256=expected,pdf_sha256=digest(pdfout),source=str(source),dest=str(target),files=19)
(target/"NAS_보존영수증_v4.1.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2))
print("NAS_BACKUP_VERIFIED",target)
