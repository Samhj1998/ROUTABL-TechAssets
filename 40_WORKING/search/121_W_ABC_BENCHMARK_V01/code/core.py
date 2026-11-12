import ast, csv, hashlib, importlib.util, itertools, json, math, os, pathlib, random, shutil, sqlite3, sys, time
from collections import Counter, defaultdict
from contextlib import contextmanager
from types import SimpleNamespace
P=pathlib.Path(__file__).resolve().parents[1]
D=P/'private'
os.umask(0o077)
def sha(p):
 with p.open('rb') as f:
  h=hashlib.sha256()
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
  return h.hexdigest()
def j(p):return json.loads(p.read_bytes())
def save(name,obj):
 (P/name).write_text(json.dumps(obj,indent=2,ensure_ascii=False,sort_keys=True)+'\n',encoding='utf-8')
def load(p,n):
 sp=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
src=P/'code/A.py'
A0=ast.parse(src.read_text())
funcs={'resolve_crosswalk','kind','safe_like','basename','relevant','query'}
assign={'ALIASES','SCOPE','MAIN_PROJECTS'}
nodes=[n for n in A0.body if isinstance(n,ast.FunctionDef) and n.name in funcs or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in assign for t in n.targets)]
assert {x.name for x in nodes if isinstance(x,ast.FunctionDef)}==funcs
ac=compile(ast.Module(body=nodes,type_ignores=[]),str(src),'exec')
def abase():
 h=pathlib.Path('/Users/yongho')
 a=dict(Path=pathlib.Path,json=json,math=math,sqlite3=sqlite3,MANIFEST=h/'ROUTABL-TechAssets/30_REGISTRY/asset_manifest_v0.6.json',PROJECT_ROOT=h/'StudioProjects')
 exec(ac,a);return a
A=abase()
OA=A['ALIASES']; OX=A['resolve_crosswalk']()
B=load(P/'tests/B/src/search_b.py','candidate_b')
C=load(P/'tests/C/src/asset_search_fts.py','candidate_c')
cor=j(D/'SYNTHETIC_CORPUS_V01.json')
cohort=j(D/'EVALUATION_COHORT_PRIVATE.json')
aux=j(D/'EVALUATION_BOUNDARY_AUXILIARY.json')
qrels={q['id']:q for f in ('SYNTHETIC_DEV_V01.json','SYNTHETIC_HOLDOUT_V01.json') for q in j(D/f)}
def ro(p):return sqlite3.connect(p.as_uri()+'?mode=ro',uri=True,timeout=8)
def terms_for(t,al):
 t=str(t).strip()
 return [t]+[a for a in al.get(t,()) if a.casefold()!=t.casefold()]
def rowids(conn,t,al):
 ts=terms_for(t,al)
 return {r[0] for r in conn.execute("SELECT rowid FROM docs WHERE "+" OR ".join([c+" LIKE ? ESCAPE '!'" for c in ('path','title','tags','content')]*len(ts)),[A['safe_like'](a) for a in ts for _ in range(4)])}
def bind_a(path,al,cw,adapter=sqlite3):
 a=abase();a.update(INDEX=path,ALIASES=al,CROSSWALK=cw,sqlite3=adapter);return a['query']
def bind_b(al,cw):
 B.ALIASES=al;B.CROSSWALK=cw
 B.relevant.__globals__['CROSSWALK']=cw
 B.relevant.__globals__['MAIN_PROJECTS']=A['MAIN_PROJECTS']
 assert B.SCOPE==A['SCOPE']
class TimedConn:
 def __init__(self,db,m):
  self.db=db;self.m=m
 def __setattr__(self,k,v):
  if k=='row_factory':self.db.row_factory=v
  else:object.__setattr__(self,k,v)
 def __enter__(self):self.db.__enter__();return self
 def __exit__(self,*a):return self.db.__exit__(*a)
 def execute(self,*a):
  t=time.perf_counter_ns(); rows=self.db.execute(*a).fetchall()
  self.m['sqlite_fetch_ms']+=(time.perf_counter_ns()-t)/1e6
  return rows
class AContext:
 def __init__(self,path,al,cw,mode):
  self.path=path;self.mode=mode;self.db=ro(path) if mode=='reuse' else None;self.used=[]
  self.query=bind_a(path,al,cw,SimpleNamespace(connect=self.connect,Row=sqlite3.Row))
 def connect(self,*args,**kw):
  t=time.perf_counter_ns()
  db=self.db
  if db is None:db=sqlite3.connect(*args,**kw);self.used.append(db)
  self.m['connection_ms']+=(time.perf_counter_ns()-t)/1e6
  return TimedConn(db,self.m)
 def run(self,q):
  self.m=dict(connection_ms=0,sqlite_fetch_ms=0)
  t=time.perf_counter_ns()
  try:r=self.query(*q)
  finally:
   for db in self.used:db.close()
   self.used.clear()
  ms=(time.perf_counter_ns()-t)/1e6
  self.m['postprocess_ms']=max(0,ms-self.m['sqlite_fetch_ms']-self.m['connection_ms'])
  self.m['accelerated']=False;self.m['fallback_reason']='baseline';return r,self.m
 def close(self):
  if self.db:self.db.close()
@contextmanager
def engine(k,path,al,cw,mode='reuse',fault=None):
 if k=='A':
  x=AContext(path,al,cw,mode)
  try:yield lambda q,audit=False:x.run(q)
  finally:x.close()
 elif k=='B':
  bind_b(al,cw)
  if mode=='reuse':
   with B.SearchSnapshot(path) as x:
    if fault=='match':x.db.set_authorizer(lambda op,one,two,db,trig:sqlite3.SQLITE_DENY if op==sqlite3.SQLITE_FUNCTION and (two or one or '').lower()=='match' else sqlite3.SQLITE_OK)
    def run(q,audit=False):
     m={};r=x.query(*q,metrics=m,audit=audit);return r,m
    yield run
  else:
   def run(q,audit=False):
    m={};r=B.query(*q,db_path=path,metrics=m,audit=audit);return r,m
   yield run
 else:
  x=C.SearchEngine(path,al,cw)
  if fault=='match':x._fts_expression=lambda _: '"unterminated'
  def run(q,audit=False):
   obj=x if mode=='reuse' else C.SearchEngine(path,al,cw)
   try:return obj.query_with_metrics(*q,debug=audit)
   finally:
    if obj is not x:obj.close()
  try:yield run
  finally:x.close()
def args(q):return (q['term'],q.get('page',1),q['scope'],q.get('page_size',12))
def identities(corpus):
 return {d['path']:d.get('group') for d in corpus['docs']}
def rank_metrics(result,q,groups):
 grades=q['grades'];seen=set();rels=[]
 for item in result['results'][:10]:
  g=groups.get(item['path']);rels.append(grades.get(g,0) if g not in seen else 0);seen.add(g)
 ideal=sorted(grades.values(),reverse=True)[:10]
 dcg=lambda xs:sum((2**v-1)/math.log2(i+2) for i,v in enumerate(xs))
 hit=sum(x>0 for x in rels)
 top=result['results'][0] if result['results'] else {}
 prov=top.get('provenance') or {}
 loc=sorted(x['path'] for x in top.get('locations',[]))
 expected=sorted(q['duplicate_paths'])
 return dict(recall=hit/max(1,sum(x>0 for x in grades.values())),precision=hit/10,mrr=next((1/(i+1) for i,x in enumerate(rels) if x>0),0),ndcg=dcg(rels)/(dcg(ideal) or 1),top=top.get('path')==q['top_path'],sha=top.get('sha256')==q['expected_sha'],status=top.get('status')==q['expected_status'],version=prov.get('version')==q['expected_version'],duplicates=(loc==expected and top.get('duplicate_count')==len(expected)))
def diffs(x,y):
 if not isinstance(y,dict):return ['exception']
 return [k for k in x if x[k]!=y.get(k)]+[k for k in y if k not in x]
def perform(path,qs,al,cw,layer,score=False):
 from contextlib import ExitStack
 rows=[];metrics=[]
 with ExitStack() as st:
  lookup=st.enter_context(ro(path))
  runs={k:st.enter_context(engine(k,path,al,cw)) for k in 'ABC'}
  for q in qs:
   az,_=runs['A'](args(q))
   rid=rowids(lookup,q['term'],al)
   if score:metrics.append(dict(layer=layer,split=q['split'],id=q['id'],engine='A',**rank_metrics(az,qrels[q['id']],identities(cor))))
   for k in 'BC':
    try:z,m=runs[k](args(q),True);err=None
    except Exception as e:z=None;m={};err=type(e).__name__
    missed=len(rid-set(m.get('candidate_rowids',[]))) if m.get('accelerated') else None
    rows.append(dict(layer=layer,split=q.get('split',layer),id=q['id'],engine=k,equal=(az==z),diff=diffs(az,z),missed=missed,eligible=len(rid),accelerated=m.get('accelerated'),reason=(m.get('fallback_reason') or '').split(':')[0],error=err))
    if score and z is not None:metrics.append(dict(layer=layer,split=q['split'],id=q['id'],engine=k,**rank_metrics(z,qrels[q['id']],identities(cor))))
 return rows,metrics
def writecsv(name,rows):
 if not rows:return
 fields=list(dict.fromkeys(k for r in rows for k in r))
 with (P/name).open('w',newline='',encoding='utf-8') as f:
  out=csv.DictWriter(f,fieldnames=fields);out.writeheader();out.writerows(rows)
