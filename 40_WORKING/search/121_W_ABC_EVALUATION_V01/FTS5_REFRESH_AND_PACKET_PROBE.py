import ast, collections, hashlib, json, math, os, pathlib as p, re, shutil, sqlite3, tempfile, threading, time, types
from pathlib import Path
os.umask(0o077)
home=p.Path('/Users/yongho')
app=home/'Library/Application Support/ROUTABL-AssetSearch'
work=home/'ROUTABL-TechAssets/40_WORKING'
out=work/'121_W_ABC_EVALUATION_V01'
base=work/'121_W_BASELINE_V01'
hashfile=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def read(name,sha):
 f=app/name
 assert hashfile(f)==sha
 return f.read_text()
def subset(src, funcs, env):
 tree=ast.parse(src)
 b=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in funcs]
 assert len(b)==len(funcs)
 exec(compile(ast.Module(body=b,type_ignores=[]),'<pinned-source-extract>','exec'),env)
 return env
leg=read('routabl_assetsearch_v1_1.py','bdea926cabe2157bdec2f8d0c69173e1a50dfa35ec5cae40563f16711588cc83')
legacy=subset(leg,{'setup','add'}, {})
scanner_text=read('routabl_assetsearch_v1_3.py','9faeb3e8711f3f2c1dcd0c63e4848fd9cabd87ae8ea4e15d89f23d5ce2fb5de3')
worker_text=read('routabl_search_v1_4_service.py','972bc93b820c8b7446931ec2a4403d6be7846c21f787d3328b38dd264e17a068')
a=read('routabl_search_v1_5_service.py','55b8747b145463c62366deba13904e3136893b8a611bb4ae94bbc2d7a642347d')
probes={}
with tempfile.TemporaryDirectory(prefix='synthetic_refresh_',dir=out) as path:
 stage=p.Path(path)
 root=stage/'projects'
 project=root/'TestProject'
 project.mkdir(parents=True)
 control=stage/'fixed_baseline.sqlite'
 active=stage/'active.sqlite'
 prev=stage/'rollback.sqlite'
 legacy_mod=types.SimpleNamespace(add=legacy['add'],tag_of=lambda path:'synthetic')
 def digest_file(f):return hashfile(f)
 protect={f'MAC::StudioProjects/TestProject/verified{i}.md':f'verifiedsynthetic{i}' for i in range(2)}
 with sqlite3.connect(control) as db:
  legacy['setup'](db)
  for key,content in protect.items():
   (project/key.rsplit('/',1)[1]).write_text(content)
   legacy['add'](db,key,'MAC_STUDIOPROJECTS_EXPLICIT_ALLOWLIST','.md',len(content),1,hashlib.sha256(content.encode()).hexdigest(),'OK','Synthetic','',''+content,0)
  for i in range(2270):
   legacy['add'](db,f'dummy/{i:04}.txt','SYNTHETIC','.txt',4,1,'','OK','neutral','','seed',0)
 shutil.copyfile(control,active)
 control_sha=hashfile(control)
 no_match=re.compile(r'(?!)')
 def load_engine():
  env={'PREVIOUS':control,'LEGACY_ENGINE':out/'FTS5_FEASIBILITY_PROBE.py','PROJECTS':('TestProject',),'ROOT':root,'os':os,'sqlite3':sqlite3,'collections':collections,'Path':Path,'SKIP_DIRS':set(),'PRIVATE_PATH':no_match,'ALLOWED_EXT':{'.md'},'MAX_INDEX_BYTES':10000,'protect_or_redact':lambda f,e,s:('OK',f.read_text(),'P3'),'digest':digest_file,'PROTECTED_BASELINE':set(protect),'engine':lambda:legacy_mod,'EMAIL':no_match,'PHONE':no_match,'PERSONAL':no_match,'SECRET_CONTENT':no_match,'json':json}
  subset(scanner_text,{'build'},env)
  class Scanner:
   def __setattr__(self,name,value):env[name]=value
   def build(self):env['build']()
  return Scanner()
 env={'ACTIVE':active,'PREVIOUS':prev,'STORE':stage,'LAST_ACTIVITY':0,'tempfile':tempfile,'Path':Path,'os':os,'sqlite3':sqlite3,'STATE_LOCK':threading.Lock(),'STATE':{},'time':time,'load_engine':load_engine}
 subset(worker_text,{'refresh_worker','check_db'},env)
 def state():
  with sqlite3.connect(active) as db:
   keys={x[0] for x in db.execute("SELECT path FROM docs WHERE carrier='MAC_PROJECTS_ALLOWLIST_V1_3'")}
   matches={t:db.execute('SELECT count(*) FROM ft WHERE ft MATCH ?',(t,)).fetchone()[0] for t in ('oldmarker','newmarker','deletemarker')}
   mismatches=db.execute("""SELECT count(*) FROM docs d LEFT JOIN ft f ON d.rowid=f.rowid WHERE f.rowid IS NULL OR f.path IS NOT d.path||' '||d.title OR f.tags IS NOT d.tags OR f.content IS NOT d.content""").fetchone()[0]
   extra=db.execute("SELECT count(*) FROM ft f LEFT JOIN docs d ON d.rowid=f.rowid WHERE d.rowid IS NULL").fetchone()[0]
   db.execute("INSERT INTO ft(ft) VALUES('integrity-check')")
   db.rollback()
  return {'generation_keys':sorted(k.rsplit('/',1)[-1] for k in keys),'matches':matches,'misalignment':mismatches,'orphan_ft':extra,'worker':env['STATE']['state']}
 def refresh(label):
  before=hashfile(active)
  env['refresh_worker']()
  row=state()
  assert row['worker']=='complete',env['STATE']
  assert row['misalignment']==row['orphan_ft']==0
  row['rollback_matches_prior_active']=hashfile(prev)==before
  # Backup may change the database header even if rows match.
  with sqlite3.connect(prev) as db:row['rollback_rows']=db.execute('SELECT count(*) FROM docs').fetchone()[0]
  probes[label]=row
 x=project/'old.md'; y=project/'delete.md'; z=project/'renamed.md'
 x.write_text('oldmarker');y.write_text('deletemarker')
 refresh('initial')
 st=x.stat();x.write_text('newmarker');os.utime(x,ns=(st.st_atime_ns,st.st_mtime_ns))
 refresh('same_size_and_mtime_source_update')
 x.rename(z);refresh('rename')
 y.unlink();refresh('delete')
 assert hashfile(control)==control_sha
 assert probes['initial']['matches']=={'oldmarker':1,'newmarker':0,'deletemarker':1}
 assert probes['same_size_and_mtime_source_update']['matches']=={'oldmarker':0,'newmarker':1,'deletemarker':1}
 assert probes['rename']['generation_keys']==['delete.md','renamed.md']
 assert probes['delete']['generation_keys']==['renamed.md'] and probes['delete']['matches']['deletemarker']==0

tree=ast.parse(a)
def get_source(node):
 return '\n'.join(a.splitlines()[node.lineno-1:node.end_lineno])
pieces=[get_source(n) for n in tree.body if
 (isinstance(n,ast.FunctionDef) and n.name in {'kind','safe_like','basename','relevant','query'})
 or (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in {'MAIN_PROJECTS','SCOPE'} for t in n.targets))]
assert len(pieces)==7
prolog='''"""ASSET-SEARCH-01 v1.5 local query reference. Runtime bindings use synthetic inputs.
Original functions and the two classification constants below are verbatim.
"""
import json
import math
import sqlite3
from pathlib import Path

HERE = Path(__file__).resolve().parent
INDEX = HERE / "SYNTHETIC_DEV_FIXTURE_V01.sqlite"
with (HERE / "SYNTHETIC_CORPUS_V01.json").open(encoding="utf-8") as source:
    fixture = json.load(source)
ALIASES = fixture["aliases"]
CROSSWALK = fixture["crosswalk"]
del fixture
'''
local_source=prolog+'\n\n'+'\n\n\n'.join(pieces)+'\n'
patterns={
 'private_key':r'-----BEGIN (?:[A-Z]+ )*PRIVATE KEY-----',
 'token_like':r'\b(?:sk-ant-[\w-]{12,}|AIza[\w-]{20,}|ya29\.[\w-]{12,}|gh[pousr]_[\w]{20,}|github_pat_[\w-]{15,}|AKIA[A-Z0-9]{16}|xox[baprs]-[\w-]{12,})\b',
 'credential_assignment':r'(?im)\b(?:client_secret|private_key|api[_-]?key|auth[_-]?token|access[_-]?token|password)\s*[:=]\s*["\x27][^"\x27\n]{8,}',
 'email':r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}',
 'korean_identity':r'\b\d{6}-[1-8]\d{6}\b',
 'korean_mobile':r'(?<!\d)01[016789][ .-]\d{3,4}[ .-]\d{4}(?!\d)'}
refs={'COMMON_ANALYSIS_PACKET_V01.md':'d88a5a12e4a814105991fce95391079e7cdd22cddee0296d5ad33d3812c69bba','SYNTHETIC_CORPUS_V01.json':'840ecf1ea98a59fa20d499e559205ceae130c513aa68531e295cb129e01a7b8b','SYNTHETIC_DEV_V01.json':'db2fca0951c1c43d30da560d7ecafd6c967e7ff9389c21c773b347714a93f3a1','COMMON_TEST_SPEC.md':'552bb8111f703048e657a26922954f2739156362efa37f54f5f7e5cf1e254f6d'}
security={}
for name,value in {'A_V15_QUERY_REFERENCE.py':local_source, **{n:(base/n).read_text() for n in refs}}.items():
 security[name]={k:len(re.findall(pattern,value)) for k,pattern in patterns.items()}
 assert not any(security[name].values()),(name,security[name])
target=out/'IMPLEMENTATION_COMMON_DRAFT'
target.mkdir(mode=0o700)
for n,h in refs.items():
 assert hashfile(base/n)==h
for n in (*refs,'SYNTHETIC_DEV_FIXTURE_V01.sqlite'):
 src=(base if n in refs else out)/n
 dst=target/n
 with dst.open('xb') as f: f.write(src.read_bytes())
 assert hashfile(dst)==hashfile(src)
 dst.chmod(0o400)
f=target/'A_V15_QUERY_REFERENCE.py'
with f.open('x') as t: t.write(local_source)
f.chmod(0o400)
a_env={'__file__':str(f)}
exec(compile(local_source,str(f),'exec'),a_env)
dev=json.loads((target/'SYNTHETIC_DEV_V01.json').read_bytes())
corpus=json.loads((target/'SYNTHETIC_CORPUS_V01.json').read_bytes())
baseline_memory=sqlite3.connect(':memory:')
legacy['setup'](baseline_memory)
for d in corpus['docs']:
 legacy['add'](baseline_memory,d['path'],'SYNTHETIC','FILE',len(d['content'].encode()),1,d['sha'],d['status'],d['title'],d['tags'],d['content'],1)
baseline_memory.commit()
frozen=subset(a,{'kind','safe_like','basename','relevant','query'}, {'INDEX':'synthetic','ALIASES':corpus['aliases'],'CROSSWALK':corpus['crosswalk'],'MAIN_PROJECTS':a_env['MAIN_PROJECTS'],'SCOPE':a_env['SCOPE'],'math':math,'sqlite3':types.SimpleNamespace(connect=lambda *x,**y:baseline_memory,Row=sqlite3.Row)})
checks=0
for q in dev:
 for pg,sz in ((1,12),(2,1),(999,1)):
  args=(q['term'],pg,q['scope'],sz)
  assert a_env['query'](*args)==frozen['query'](*args),(q['id'],pg,sz)
  checks+=1
baseline_memory.close()
records={f.name:{'bytes':f.stat().st_size,'sha':hashfile(f)} for f in sorted(target.iterdir())}
evidence={'refresh_with_original_function_bodies':probes,'package':records,'screen_hits_count':security,'dev_reference_full_object_checks':checks,'dev_queries':len(dev),'synthetic_metadata_diff':{'fixture_carrier':'path','fixture_kind':'.md','fixture_mtime_ns':100,'historical_carrier':'SYNTHETIC','historical_kind':'FILE','historical_mtime_ns':1},'mocked_dependencies':['v1.3 synthetic root and paths','read-only text classifier for synthetic Markdown','synthetic tag helper','impossible PII regex for fixed literals','injected local load_engine','fixed 2272 synthetic baseline, including two synthetic protected rows']}
with (out/'FTS5_REFRESH_AND_PACKET_EVIDENCE.json').open('x') as f:json.dump(evidence,f,ensure_ascii=False,indent=2,sort_keys=True)
print(json.dumps(evidence,ensure_ascii=False,sort_keys=True))
