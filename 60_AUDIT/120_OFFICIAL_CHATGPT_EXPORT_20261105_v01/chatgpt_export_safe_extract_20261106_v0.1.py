#!/usr/bin/env python3
"""Safely extract the 2026-11-05 ChatGPT official ZIP to a private local GUI workspace.
No network, no original mutations, no external disk plaintext.
"""
from pathlib import Path, PurePosixPath
import os, zipfile, hashlib, json, datetime, time, stat, shutil, sys

SOURCE_DIR=Path('/Users/yongho/ROUTABL-TechAssets/20_ORIGINALS/ChatGPT-Account-Exports/2026-11-05/00_ORIGINAL')
ROOT=Path('/Users/yongho/ROUTABL-ChatGPT-Archive/2026-11-05')
FINAL=ROOT/'00_EXTRACTED_ORIGINAL'
STAGING=ROOT/'00_EXTRACTED_ORIGINAL.staging'
RECEIPT=ROOT/'20_AUDIT'/'original_extract_validation_v0.1.json'
EXPECTED_SHA='06efc5c5c787d59b7d1bd62566974563416b29792bb17ac318335475884c5553'

def log(message, **kw):
 print(json.dumps({'step':message,**kw},ensure_ascii=False),flush=True)
def sha256(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for chunk in iter(lambda:f.read(4*1024*1024),b''):
   h.update(chunk)
 return h.hexdigest()
def mkdir_private(p):
 if p.is_symlink():raise ValueError('SYMLINK_DENIED_'+str(p))
 p.mkdir(parents=True,exist_ok=True,mode=0o700)
 os.chmod(p,0o700)
def main():
 os.umask(0o077)
 found=list(SOURCE_DIR.glob('*.zip'))
 assert len(found)==1 and found[0].is_file(),'SOURCE_ZIP_NOT_UNIQUE'
 source=found[0]
 assert not FINAL.exists() and not STAGING.exists(),'ALREADY_EXTRACTED_REFUSING_OVERWRITE'
 assert sha256(source)==EXPECTED_SHA,'SOURCE_ZIP_SHA_MISMATCH'
 log('SOURCE_ORIGINAL_SHA_VERIFIED',bytes=source.stat().st_size)
 mkdir_private(ROOT);mkdir_private(ROOT/'20_AUDIT');mkdir_private(ROOT/'10_GUI_VIEWER')
 mkdir_private(STAGING)
 with zipfile.ZipFile(source) as z:
  members=z.infolist()
  assert len(members)==2780,'UNEXPECTED_MEMBER_COUNT'
  expected_size=sum(m.file_size for m in members if not m.is_dir())
  assert expected_size<5*1024**3
  all_paths=set();count=0;size=0
  for m in members:
   parts=PurePosixPath(m.filename)
   assert not parts.is_absolute() and all(a not in ('..','.') for a in parts.parts),'UNSAFE_PATH'
   assert m.filename and not m.filename.startswith('/') and '\\' not in m.filename
   assert ((m.external_attr>>16)&0o170000)!=0o120000,'SYMLINK_IN_ARCHIVE'
   assert m.filename not in all_paths,'DUPLICATE_MEMBER_PATH'
   all_paths.add(m.filename)
  log('ZIP_MEMBER_PATHS_VALID',count=len(members),uncompressed_bytes=expected_size)
  for m in members:
   pp=PurePosixPath(m.filename)
   target=STAGING.joinpath(*pp.parts)
   assert STAGING.resolve() in target.resolve().parents,'PATH_ESCAPES_STAGING'
   if m.is_dir():
    mkdir_private(target)
    continue
   mkdir_private(target.parent)
   with z.open(m,'r') as fin, open(target,'xb') as fout:
    while True:
     chunk=fin.read(4*1024*1024)
     if not chunk:break
     fout.write(chunk)
   assert target.stat().st_size==m.file_size
   count+=1;size+=m.file_size
   if count%400==0:log('EXTRACT_PROGRESS',files=count,total=len(members))
  assert size==expected_size
  assert (STAGING/'chat.html').is_file()
  assert all((STAGING/p).is_file() for p in ['conversations-000.json','conversations-001.json','conversations-002.json','conversations-003.json'])
 os.replace(STAGING,FINAL)
 receipt={
  'status':'ORIGINAL_EXTRACTED_AND_CRC_CHECKED_ON_STREAMING_READ',
  'source_zip_path':str(source),'source_zip_sha256':EXPECTED_SHA,
  'source_zip_bytes':source.stat().st_size,'files_extracted':count,
  'total_uncompressed_bytes':size,'location':str(FINAL),
  'private_local_only':True,'original_archive_unchanged':True,
  'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'official_chat_html_present':True,'json_shards':4}
 with RECEIPT.open('x',encoding='utf8') as out:json.dump(receipt,out,ensure_ascii=False,indent=2)
 log('EXTRACTION_SUCCEEDED',file_count=count,location=str(FINAL),chat_html=str(FINAL/'chat.html'))
if __name__=='__main__':main()
