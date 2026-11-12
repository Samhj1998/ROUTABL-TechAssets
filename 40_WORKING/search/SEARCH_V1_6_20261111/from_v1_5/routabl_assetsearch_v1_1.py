#!/usr/bin/env python3
# ROUTABL AssetSearch v1.1 - private, read-only source catalog; stdlib only.
import argparse, collections, hashlib, html, json, os, re, sqlite3, time, unicodedata, zipfile
from html.parser import HTMLParser
from pathlib import Path
ROOT=Path('/Volumes/Dev_Assets/Routabl')
STORE=Path.home()/'Library/Application Support/ROUTABL-AssetSearch'
DB=STORE/'assets.sqlite'
TEXT={'.md','.txt','.html','.htm','.rst'}
META={'.kt','.java','.js','.ts','.json','.tsv','.csv','.pdf','.docx','.xml','.sh','.py','.cjs','.png','.zip'}
BAD=re.compile(r'(?:^\.env(?:\.|$)|adminsdk|credential|private.?key|password|secret|token|service.?account|\.pem$|\.p12$|\.key$)',re.I)
KEY=re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----|"private_key"\s*:|AIza[0-9A-Za-z_-]{25,}|ya29\.[0-9A-Za-z_-]{20,}|sk-[A-Za-z0-9_-]{20,}')
EMAIL=re.compile(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}')
PHONE=re.compile(r'(?<!\d)01[0-9]-?\d{3,4}-?\d{4}(?!\d)')
LIMIT=3_000_000
def n(s):return unicodedata.normalize('NFC',str(s))
class Strip(HTMLParser):
 def __init__(self):super().__init__();self.s=[];self.skip=0
 def handle_starttag(self,t,a):
  if t in ('script','style'):self.skip+=1
  elif t in ('p','h1','h2','h3','br','tr','li'):self.s.append(' ')
 def handle_endtag(self,t):
  if t in ('script','style'):self.skip=max(0,self.skip-1)
 def handle_data(self,x):
  if not self.skip:self.s.append(x)
def tag_of(name):
 m={'SEARCH-01':'초성검색 검색순위','DATA-01':'고객정보 고객등록 중복방지','AUTH-01':'인증 권한 승인','BACKUP-01':'백업 복원','PERF-01':'성능 입력','E04':'통합점검 관제','F1':'취소상태 위험'}
 labels=[]
 for k,v in m.items():
  if k.casefold() in name.casefold():labels.extend([k]+v.split())
 for k,v in {'인계':'인계','검증':'검증','원고':'기술원고','원본':'원본','관제':'관제','백서':'백서','검색':'검색','고객':'고객정보'}.items():
  if k in name:labels.append(v)
 return ' '.join(dict.fromkeys(labels))
def text_of(path):
 try:
  if path.stat().st_size>LIMIT:return 'TOO_LARGE',''
  t=path.read_bytes().decode('utf-8-sig',errors='replace')
  if KEY.search(t):return 'SENSITIVE_CONTENT',''
  if path.suffix.lower() in ('.html','.htm'):
   p=Strip();p.feed(t);t=' '.join(p.s)
  t=EMAIL.sub('[EMAIL]',PHONE.sub('[PHONE]',t))
  return ('OK' if t.strip() else 'EMPTY'),t
 except Exception:return 'READ_ERROR',''
def setup(db):
 db.executescript("""CREATE TABLE IF NOT EXISTS docs(
  path TEXT PRIMARY KEY, carrier TEXT NOT NULL, kind TEXT NOT NULL, sz INTEGER NOT NULL,
  mtime_ns INTEGER NOT NULL, sha TEXT NOT NULL, status TEXT NOT NULL, title TEXT NOT NULL,
  tags TEXT NOT NULL, content TEXT NOT NULL, scan INTEGER NOT NULL);
 CREATE TABLE IF NOT EXISTS manual(
  id TEXT PRIMARY KEY,title TEXT,tags TEXT,path TEXT,source_grade TEXT,validation_grade TEXT,details TEXT);
 CREATE VIRTUAL TABLE IF NOT EXISTS ft USING fts5(path,tags,content,tokenize='trigram');
 """)
def add(db,path,carrier,kind,sz,mtime,sha,status,title,tags,content,epoch):
 prior=db.execute('SELECT rowid,sz,mtime_ns FROM docs WHERE path=?',(path,)).fetchone()
 if prior and prior[1]==sz and prior[2]==mtime:
  db.execute('UPDATE docs SET scan=? WHERE path=?',(epoch,path));return 'unchanged'
 db.execute("""INSERT INTO docs(path,carrier,kind,sz,mtime_ns,sha,status,title,tags,content,scan)
 VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(path) DO UPDATE SET
 carrier=excluded.carrier,kind=excluded.kind,sz=excluded.sz,mtime_ns=excluded.mtime_ns,
 sha=excluded.sha,status=excluded.status,title=excluded.title,tags=excluded.tags,
 content=excluded.content,scan=excluded.scan""",
 (path,carrier,kind,sz,mtime,sha,status,title,tags,content,epoch))
 row=db.execute('SELECT rowid FROM docs WHERE path=?',(path,)).fetchone()[0]
 db.execute('DELETE FROM ft WHERE rowid=?',(row,))
 db.execute('INSERT INTO ft(rowid,path,tags,content) VALUES(?,?,?,?)',(row,path+' '+title,tags,content))
 return 'new'
def build():
 if not ROOT.is_dir():print('ROOT_OFFLINE',ROOT);return 2
 STORE.mkdir(parents=True,exist_ok=True);os.chmod(STORE,0o700)
 db=sqlite3.connect(DB);setup(db);epoch=int(time.time()*1000);count=collections.Counter()
 for folder,dirs,names in os.walk(ROOT,followlinks=False):
  dirs[:]=[x for x in dirs if not x.startswith('.') and x not in ('.git','node_modules','__pycache__') and not (Path(folder)/x).is_symlink()]
  for name in names:
   p=Path(folder)/name
   if p.is_symlink() or BAD.search(name):count['excluded_sensitive_name']+=1;continue
   ext=p.suffix.lower()
   if ext not in TEXT|META:count['excluded_extension']+=1;continue
   try:
    rel=n(p.relative_to(ROOT).as_posix());st=p.stat()
    prior=db.execute('SELECT sz,mtime_ns FROM docs WHERE path=?',(rel,)).fetchone()
    if prior and prior[0]==st.st_size and prior[1]==st.st_mtime_ns:
     db.execute('UPDATE docs SET scan=? WHERE path=?',(epoch,rel))
     if ext=='.zip':
      db.execute("UPDATE docs SET scan=? WHERE carrier=? AND kind='ZIP_MEMBER_NAME'",(epoch,rel))
     count['unchanged']+=1
     continue
    if ext in TEXT:
     status,content=text_of(p)
    else:status,content=('METADATA_ONLY' if ext!='.pdf' else 'PDF_TEXT_NOT_EXTRACTED'),''
    title=next((line.strip('# ').strip()[:150] for line in content.splitlines()[:14] if line.startswith('# ')),p.stem[:150])
    digest=hashlib.sha256(p.read_bytes()).hexdigest() if st.st_size<=40_000_000 else ''
    result=add(db,rel,rel,ext,st.st_size,st.st_mtime_ns,digest,status,title,tag_of(rel),content,epoch)
    count[result]+=1;count['type:'+ext]+=1
    if ext=='.zip':
     try:
      with zipfile.ZipFile(p) as z:
       for i,m in enumerate(z.infolist()):
        if i>=10000:count['zip_member_limit']+=1;break
        v=n(m.filename)
        if m.is_dir() or '..' in Path(v).parts or v.startswith('/') or BAD.search(v):continue
        vv=rel+'::'+v
        add(db,vv,rel,'ZIP_MEMBER_NAME',m.file_size,st.st_mtime_ns,'','ZIP_MEMBER_METADATA_ONLY',Path(v).name,tag_of(vv),'',epoch)
        count['zip_member_names']+=1
     except (OSError,zipfile.BadZipFile,RuntimeError):count['zip_errors']+=1
   except (OSError,PermissionError):count['read_errors']+=1
 db.execute('DELETE FROM ft WHERE rowid IN (SELECT rowid FROM docs WHERE scan != ?)',(epoch,))
 db.execute('DELETE FROM docs WHERE scan != ?',(epoch,))
 manual=[
 ('TA-CASE-20261102-01','Firebase 주소록 등록 성공·실패 경로 분석','Firebase 주소록 고객등록 성공사례 cloud_access.py',
  'ROUTIVEL-Firebase-Migration/tools/firebase-migration/cloud_access.py','HISTORICAL_REPORT','HISTORICAL_LOG_REPORT',
  '2026-11-02 첨부 PDF 보고. 모듈 위치 실제 확인. 원문 재조회·현 운영 테스트는 아님.'),
 ('INTEGRATION-F1','취소 배차 재활성화 F1 정적 위험','F1 취소상태 완료 위험 TransportStatusPolicy',
  'DISPATCH-One-Android/app/src/main/java/com/routivel/driver/TransportStatusPolicy.kt','GITHUB_FIXED_COMMIT','STATIC_REVIEW',
  'GitHub main b9c40c2 기준 정적 위험. 현 APK·배포 Rules 미검증.'),
 ('INTEGRATION-E04','2026-10-19 앱·관제 통합점검 원본','E04 F1 F2 F3 F4 관제 통합점검',
  'ROUTABL-integration-audit-20261019.html','LIBRARY_ORIGINAL','HISTORICAL_TEST_REPORT',
  'ChatGPT Library 원본 확인. NAS에 별도 파일 원본 있다고 단정하지 않음.')]
 for x in manual:db.execute('INSERT OR REPLACE INTO manual VALUES(?,?,?,?,?,?,?)',x)
 db.commit()
 summary=dict(count)
 summary.update({'physical_count':db.execute("SELECT count(*) FROM docs WHERE kind!='ZIP_MEMBER_NAME'").fetchone()[0],
 'zip_member_count':db.execute("SELECT count(*) FROM docs WHERE kind='ZIP_MEMBER_NAME'").fetchone()[0],
 'indexed_text_count':db.execute("SELECT count(*) FROM docs WHERE status='OK'").fetchone()[0],
 'metadata_only_count':db.execute("SELECT count(*) FROM docs WHERE status LIKE '%METADATA_ONLY' OR status='PDF_TEXT_NOT_EXTRACTED'").fetchone()[0],
 'db_bytes':DB.stat().st_size,'root':str(ROOT),'db':str(DB)})
 db.close();os.chmod(DB,0o600)
 print(json.dumps(summary,ensure_ascii=False))
 return 0
def query(term):
 if not DB.exists():raise SystemExit('INDEX_MISSING')
 db=sqlite3.connect(DB);db.row_factory=sqlite3.Row
 allterms=[term]
 expansions={'주소등록':['고객등록','cloud_access.py','주소록'],'고객등록':['주소록','DATA-01'],'초성검색':['SEARCH-01'],'취소상태':['F1','TransportStatusPolicy'],'관제':['E04','통합점검'],'백업':['BACKUP-01','NAS']}
 allterms+=expansions.get(term,[])
 hits={}
 for t in allterms:
  if len(t)>=3:
   for row in db.execute("""SELECT docs.* FROM docs JOIN ft ON docs.rowid=ft.rowid
      WHERE ft.path LIKE ? OR ft.tags LIKE ? OR ft.content LIKE ? LIMIT 500""",('%'+t+'%',)*3):
    score=20 if t.casefold() in row['title'].casefold() else 15 if t.casefold() in row['tags'].casefold() else 10 if t.casefold() in row['path'].casefold() else 1
    if row['status']=='OK':score+=7
    elif row['kind']=='ZIP_MEMBER_NAME':score-=5
    elif row['kind']=='.pdf':score+=1
    key=row['path'];hits[key]=(max(hits.get(key,(0,))[0],score),dict(row))
 manual=[]
 for row in db.execute('SELECT * FROM manual'):
  r=dict(row)
  if any(t.casefold() in ' '.join([r['id'],r['title'],r['tags'],r['path'],r['details']]).casefold() for t in allterms):manual.append(r)
 ranked=sorted(hits.values(),key=lambda x:(-x[0],x[1]['path']))
 unique={}
 for score,row in ranked:
  k=('sha',row['sha']) if row['sha'] else ('title_size',n(row['title']).casefold(),row['sz'])
  if k not in unique:unique[k]=(score,row)
 out=list(unique.values())[:10]
 print(json.dumps({'term':term,'match_count':len(hits),'manual':manual,
 'top':[{'score':s,'title':r['title'],'path':r['path'],'status':r['status'],'tags':r['tags'],'archive_member':r['kind']=='ZIP_MEMBER_NAME'} for s,r in out]},ensure_ascii=False))
 db.close()
def stats():
 if not DB.exists():raise SystemExit('INDEX_MISSING')
 db=sqlite3.connect(DB)
 print(json.dumps({'total':db.execute('SELECT count(*) FROM docs').fetchone()[0],
 'types':db.execute('SELECT kind,count(*) FROM docs GROUP BY kind ORDER BY count(*) DESC').fetchall()[:18],
 'statuses':db.execute('SELECT status,count(*) FROM docs GROUP BY status').fetchall(),
 'manual':db.execute('SELECT count(*) FROM manual').fetchone()[0],
 'size_bytes':DB.stat().st_size,'source_online':ROOT.is_dir()},ensure_ascii=False))
if __name__=='__main__':
 ap=argparse.ArgumentParser();sp=ap.add_subparsers(dest='cmd',required=True)
 sp.add_parser('build');q=sp.add_parser('query');q.add_argument('term');sp.add_parser('stats')
 a=ap.parse_args()
 if a.cmd=='build':raise SystemExit(build())
 elif a.cmd=='query':query(a.term)
 else:stats()
