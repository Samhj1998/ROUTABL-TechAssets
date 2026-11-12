from core import *
from contextlib import closing
import statistics
orders=['ABC','ACB','BAC','BCA','CAB','CBA']
docs_sql='INSERT INTO docs(rowid,path,carrier,kind,sz,mtime_ns,sha,status,title,tags,content,scan) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)'
fts_sql="INSERT INTO ft(rowid,path,tags,content) SELECT rowid,path||' '||title,tags,content FROM docs"
def timed(m,k,f):
 t=time.perf_counter_ns()
 try:return f()
 finally:m[k]=m.get(k,0)+(time.perf_counter_ns()-t)/1e6
def native_sizes(db):
 return {k:v for k,v in db.execute('SELECT name,sum(pgsize) FROM dbstat GROUP BY name')}
def validate(k,p,m):
 with closing(ro(p)) as db:
  check=timed(m,'common_quick_check_ms',lambda:db.execute('PRAGMA quick_check').fetchone())
  assert check==('ok',)
 if k=='A':
  q=bind_a(p,cor['aliases'],cor['crosswalk'])
  timed(m,'first_query_after_open_ms',lambda:q('SIM-001',scope='all'))
  return
 if k=='B':
  original=B.sqlite3
  class Probe:
   def __init__(self,db):object.__setattr__(self,'db',db)
   def __setattr__(self,k,v):setattr(self.db,k,v)
   def __getattr__(self,k):return getattr(self.db,k)
   def backup(self,target,*a,**kw):return timed(m,'b_memory_backup_ms',lambda:self.db.backup(target.db,*a,**kw))
   def execute(self,sql,*a):
    if 'integrity-check' in sql:return timed(m,'b_native_fts_ms',lambda:self.db.execute(sql,*a))
    return self.db.execute(sql,*a)
  B.sqlite3=SimpleNamespace(connect=lambda *a,**kw:Probe(sqlite3.connect(*a,**kw)),Row=sqlite3.Row,Error=sqlite3.Error)
  try:
   with B.SearchSnapshot(p) as x:
    assert x.fallback_reason is None
    m['candidate_connect_ms']=x.connection_ms
    m['candidate_verify_ms']=x.validation_ms
    timed(m,'first_query_after_open_ms',lambda:x.query('SIM-001',scope='all'))
    m['b_crosscheck_and_other_ms']=max(0,x.validation_ms-m.get('b_memory_backup_ms',0)-m.get('b_native_fts_ms',0))
  finally:B.sqlite3=original
 else:
  x=C.SearchEngine(p,cor['aliases'],cor['crosswalk'])
  try:
   out,c=x.query_with_metrics('SIM-001',scope='all')
   assert c['generation_verified']
   m['candidate_connect_ms']=c['t_connect_ms'];m['candidate_verify_ms']=c['verify_ms']
   m['c_validation_trigger_query_ms']=c['t_total_ms']
   m['first_query_after_open_ms']=max(0,c['t_total_ms']-c['verify_ms']-c['t_connect_ms'])
  finally:x.close()
def index_trial(n,kind,k,i):
 base=D/f'scale{n}.sqlite';new=P/'tests/index_work.sqlite';installed=P/'tests/index_installed.sqlite'
 assert not new.exists() and not installed.exists()
 m=dict(scale=n,scenario=kind,engine=k,rep=i,source_read_ms=0,copy_ms=0,sql_ms=0,fts_ms=0,commit_ms=0,common_quick_check_ms=0,candidate_verify_ms=0,candidate_connect_ms=0)
 allstart=time.perf_counter_ns()
 with closing(ro(base)) as r,closing(sqlite3.connect(new)) as w:
  if kind=='full':
   ddl,rs,manual=timed(m,'source_read_ms',lambda:(
    [r.execute('SELECT sql FROM sqlite_schema WHERE name=?',(x,)).fetchone()[0] for x in ('docs','manual','ft')],
    r.execute('SELECT rowid,path,carrier,kind,sz,mtime_ns,sha,status,title,tags,content,scan FROM docs ORDER BY rowid').fetchall(),
    r.execute('SELECT * FROM manual').fetchall()))
   def write():
    for z in ddl:w.execute(z)
    w.executemany(docs_sql,rs)
    w.executemany('INSERT INTO manual VALUES(?,?,?,?,?,?,?)',manual)
   timed(m,'sql_ms',write)
   timed(m,'fts_ms',lambda:w.execute(fts_sql))
  else:
   timed(m,'copy_ms',lambda:r.backup(w))
   ids=timed(m,'source_read_ms',lambda:[x[0] for x in r.execute('SELECT rowid FROM docs ORDER BY rowid LIMIT ?',(25 if kind=='batch' else 1,))])
   if kind in ('one','batch','rename','delete'):
    param=','.join('?' for _ in ids)
    clause=' WHERE rowid IN ('+param+')'
    if kind=='delete':
     timed(m,'fts_ms',lambda:w.execute('DELETE FROM ft'+clause,ids))
     timed(m,'sql_ms',lambda:w.execute('DELETE FROM docs'+clause,ids))
    else:
     stmt=("UPDATE docs SET path=path||'.rename',title=title||' ren'" if kind=='rename' else "UPDATE docs SET content=content||' update',mtime_ns=mtime_ns+1")
     timed(m,'sql_ms',lambda:w.execute(stmt+clause,ids))
     timed(m,'fts_ms',lambda:w.execute('DELETE FROM ft'+clause,ids))
     timed(m,'fts_ms',lambda:w.execute(fts_sql+clause,ids))
  m['sidecar_sample_bytes']=sum(p.stat().st_size for p in (pathlib.Path(str(new)+s) for s in ('-wal','-shm','-journal')) if p.exists())
  timed(m,'commit_ms',w.commit)
 timed(m,'verify_total_ms',lambda:validate(k,new,m))
 timed(m,'replace_ms',lambda:os.replace(new,installed))
 m['total_ms']=(time.perf_counter_ns()-allstart)/1e6
 m['db_bytes']=installed.stat().st_size
 with closing(ro(installed)) as db:
  sizes=native_sizes(db)
  m['fts_shadow_bytes']=sum(v for name,v in sizes.items() if name.startswith('ft_'))
  m['other_index_bytes']=sum(v for name,v in sizes.items() if name.startswith('sqlite_autoindex_'))
 installed.unlink()
 return m
if __name__=='__main__':
 for n in (1,5,10):
  rows=[]
  for knd in ('full','one','batch','unchanged','delete','rename'):
   for i in range(6 if knd=='full' else 30):
    for k in orders[i%6]:rows.append(index_trial(n,knd,k,i))
   writecsv(f'private/index_{n}x.csv',rows)
   print('INDEX',n,knd,len(rows),flush=True)
