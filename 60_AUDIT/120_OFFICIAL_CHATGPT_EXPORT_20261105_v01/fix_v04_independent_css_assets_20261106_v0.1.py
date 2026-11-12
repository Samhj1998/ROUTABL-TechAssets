#!/usr/bin/env python3
"""Repair v0.4 lost v0.3 layout and remove v0.1-v0.3 hard/soft file dependencies.
- Only v0.4 directory files modified, no deletion of older GUI versions or originals.
- APFS copy-on-write clone assets (separate inode, no old-path dependency).
- Immutable original v0.4 HTML/JS and registered checksums unchanged.
"""
from pathlib import Path
import os,stat,subprocess,hashlib,json,time,shutil,datetime,re,sys

BASE=Path('/Users/yongho/ROUTABL-ChatGPT-Archive/2026-11-05')
V1=BASE/'10_GUI_VIEWER'
V3=BASE/'12_GUI_PROJECT_IDS_V03'
V4=BASE/'13_GUI_MARKDOWN_V04'
AUD=BASE/'20_AUDIT'
SRC_ASSETS=V1/'assets'
STAGING=V4/'.assets.v04.independent.staging'
DEST=V4/'assets'
LAYOUT_SRC=V3/'v03-style.css'
LAYOUT_DEST=V4/'v03-style.css'
PRECHECK=AUD/'v04_independence_repair_20261106_v0.1.json'
EXPECTED_ASSETS=1925

def sha(p):
 d=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):d.update(b)
 return d.hexdigest()
def clone(src,dst):
 assert src.is_file() and not dst.exists()
 result=subprocess.run(['/bin/cp','-c',str(src),str(dst)],capture_output=True,text=True,timeout=25)
 if result.returncode!=0:raise RuntimeError('APFS_COPY_ON_WRITE_CLONE_FAILED '+str(dst)+' '+result.stderr[:140])
 assert dst.is_file() and sha(src)==sha(dst),'CLONE_HASH_MISMATCH '+str(src)
 assert src.stat().st_ino!=dst.stat().st_ino,'HARDLINK_NOT_INDEPENDENT'
def main():
 os.umask(0o077)
 assert V4.is_dir() and SRC_ASSETS.is_dir() and LAYOUT_SRC.is_file()
 assert not LAYOUT_DEST.exists()
 assert DEST.is_symlink() and os.readlink(DEST)=='../10_GUI_VIEWER/assets'
 assert not STAGING.exists()
 assert not PRECHECK.exists()
 old_index_sha=sha(V4/'index.html')
 old_app_sha=sha(V4/'app.js')
 old_data_sha=sha(V4/'project-id-data.js')
 old_markdown_sha=sha(V4/'v04-style.css')
 old_v03_index_sha=sha(V3/'index.html')
 old_v01_index_sha=sha(V1/'index.html')
 # HTML has v03 layout stylesheet link but missing file: the cause of stacked columns.
 index=(V4/'index.html').read_text('utf8')
 assert 'href="v03-style.css"' in index
 assert '#v03-layout' in (V3/'v03-style.css').read_text('utf8')
 assert '#v03-layout' not in (V4/'v04-style.css').read_text('utf8')
 print('REPAIR_PREFLIGHT_OK',flush=True)
 clone(LAYOUT_SRC,LAYOUT_DEST)
 print('V03_LAYOUT_CSS_COW_CLONED_TO_V04',flush=True)
 # Hardlinks are stable if the old path gets deleted, but not isolated from later modifications.
 # Replace with independent APFS clones without changing content/checksum.
 for fname in ('style.css','project-style.css','search-data.js'):
  dst=V4/fname
  assert dst.is_file() and not dst.is_symlink()
  old_hash=sha(dst)
  tmp=V4/('.'+fname+'.independent.tmp')
  clone(dst,tmp)
  os.replace(tmp,dst)
  assert sha(dst)==old_hash
  print('INDEPENDENT_SHARED_FILE',fname,flush=True)
 # Make all v0.4 media files independent of v0.1 in their own directory.
 items=sorted(SRC_ASSETS.iterdir(),key=lambda p:p.name)
 assert len(items)==EXPECTED_ASSETS and all(p.is_file() and not p.is_symlink() for p in items)
 names={p.name for p in items}
 source_total=sum(p.stat().st_size for p in items)
 # Prepare entire clone before flipping any live asset symlink.
 STAGING.mkdir(mode=0o700)
 result=subprocess.run(['/bin/cp','-c','-R',str(SRC_ASSETS)+'/.' ,str(STAGING)],
        capture_output=True,text=True,timeout=240)
 if result.returncode!=0:
  raise RuntimeError('RECURSIVE_APFS_COPY_ON_WRITE_CLONE_FAILED '+result.stderr[:250])
 newitems=sorted(STAGING.iterdir(),key=lambda p:p.name)
 assert len(newitems)==EXPECTED_ASSETS and {p.name for p in newitems}==names
 assert sum(p.stat().st_size for p in newitems)==source_total
 assert all(not p.is_symlink() and p.is_file() for p in newitems)
 assert all((SRC_ASSETS/p.name).stat().st_ino!=p.stat().st_ino for p in newitems)
 print('V04_MEDIA_STAGING_CLONE_READY',len(newitems),source_total,flush=True)
 # Confirm every clone hash: streamed, no file is trusted solely by name or size.
 digest_ok=0
 for idx,p in enumerate(newitems,1):
  if sha(p)!=sha(SRC_ASSETS/p.name):
   raise AssertionError('INDEPENDENT_ASSET_HASH_MISMATCH '+p.name)
  digest_ok+=1
  if idx%500==0:print('ASSET_HASH_VERIFICATION',idx,'/',EXPECTED_ASSETS,flush=True)
 assert digest_ok==EXPECTED_ASSETS
 # One symlink replaced with an independent real directory. Previous versions untouched.
 oldlink=V4/'.assets.v01.symlink.bak'
 assert not oldlink.exists() and not oldlink.is_symlink()
 os.rename(DEST,oldlink)
 try:
  os.rename(STAGING,DEST)
 except Exception:
  os.rename(oldlink,DEST)
  raise
 oldlink.unlink()
 assert DEST.is_dir() and not DEST.is_symlink()
 assert (V4/'v03-style.css').is_file()
 # Verify the working GUI's registered files are byte-identical after repair.
 assert sha(V4/'index.html')==old_index_sha
 assert sha(V4/'app.js')==old_app_sha
 assert sha(V4/'project-id-data.js')==old_data_sha
 assert sha(V4/'v04-style.css')==old_markdown_sha
 assert sha(V3/'index.html')==old_v03_index_sha
 assert sha(V1/'index.html')==old_v01_index_sha
 assert len(list((V4/'chats').glob('*.html')))==327
 assert not any(v.is_symlink() for v in V4.iterdir()),'UNEXPECTED_LOCAL_SYMLINK_REMAINS'
 report={
  'result':'INDEPENDENT_V04_GUI_MEDIA_AND_LAYOUT_FIXED',
  'source_snapshot':'2026-11-05',
  'fixed_layout_file':str(LAYOUT_DEST),
  'layout_css_source_sha256':sha(LAYOUT_SRC),
  'layout_css_v04_sha256':sha(LAYOUT_DEST),
  'v04_assets_is_real_directory':DEST.is_dir() and not DEST.is_symlink(),
  'v04_assets_total':EXPECTED_ASSETS,
  'v04_assets_all_sha256_matched':digest_ok,
  'v04_asset_apparent_bytes':source_total,
  'apfs_copy_on_write':True,'separate_file_inodes':True,
  'v04_root_independent_from_v01_v02_v03_for_essential_ui_assets':True,
  'registered_v04_html_app_data_checksums_unchanged':True,
  'previous_v01_v02_v03_unchanged':True,
  'previous_versions_not_deleted':True,
  'external_official_export_zip_untouched':True,
  'optional_prev_version_hyperlinks':'Index contains links to v01-v03; those optional history links will fail if earlier GUIs deleted, but do not affect current v04 functions.',
  'official_raw_chat_html_link':'Index links to ../00_EXTRACTED_ORIGINAL/chat.html, a separate preserved source folder.',
  'created_kst':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(timespec='seconds')
 }
 with PRECHECK.open('x',encoding='utf8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
 print('REPAIR_FINAL',json.dumps(report,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
