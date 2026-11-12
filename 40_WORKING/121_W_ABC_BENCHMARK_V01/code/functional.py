from core import *
seed=12104
def setup_data():
 base=D/'SYNTHETIC_DEV_FIXTURE_V01.sqlite'
 assert sha(base)=='d1b5045dd3a7669a076fe790bb038c4461e27a0062c16f0492afc2e78bd6b158'
 s=[]
 for scale in (1,5,10):
  p=D/f'scale{scale}.sqlite'
  shutil.copyfile(base,p)
  with sqlite3.connect(p) as db:
   if scale>1:
    rng=random.Random(seed)
    rows=[]
    for i in range(1230*(scale-1)):
     path=f'99_AUX_SCALE/{i:05d}.md'; txt='무관자료 '+''.join(rng.choice('pqvxzy') for _ in range(384))
     rows.append((path,'synthetic','.md',len(txt.encode()),1,hashlib.sha256(path.encode()).hexdigest(),'OK','통제표본','noise',txt,1))
    db.executemany('INSERT INTO docs(path,carrier,kind,sz,mtime_ns,sha,status,title,tags,content,scan) VALUES(?,?,?,?,?,?,?,?,?,?,?)',rows)
    db.execute("INSERT INTO ft(rowid,path,tags,content) SELECT rowid,path||' '||title,tags,content FROM docs WHERE path GLOB '99_AUX_SCALE/*'")
   n=db.execute('SELECT count(*) FROM docs').fetchone()[0]
   assert n==1230*scale
   assert db.execute('SELECT count(*) FROM ft').fetchone()[0]==n
   got=[]
   for q in cohort['synthetic']:
    rr=rowids(db,q['term'],cor['aliases']);assert len(rr)==q['a_docs_hits'],q['id']
    z=len(rr);band='zero' if not z else 'selective' if z*100<=n else 'dense' if z*5>=n else 'medium'
    got.append(dict(id=q['id'],type=q['type'],split=q['split'],hits=z,cohort=band,eligible=all(len(t)>=3 and '\0' not in t for t in terms_for(q['term'],cor['aliases']))))
  s.append(dict(scale=scale,docs=n,sha=sha(p),bytes=p.stat().st_size,classifications=got))
 save('private/scale.json',dict(seed=seed,generator='12104-v1',fixture_sha=sha(base),qrels={f:sha(D/f) for f in ('SYNTHETIC_DEV_V01.json','SYNTHETIC_HOLDOUT_V01.json')},alias_count=len(cor['aliases']),scales=s,python=sys.version,sqlite=sqlite3.sqlite_version))
def lifecycle():
 from contextlib import ExitStack
 p=P/'tests/lifecycle_v2.sqlite'
 from contextlib import closing
 # Recreate the same physical search schema and build rows and FTS from the pinned synthetic source.
 base=D/'scale1.sqlite'
 with closing(ro(base)) as source, closing(sqlite3.connect(p)) as db, db:
  for name in ('docs','manual','ft'):
   db.execute(source.execute('SELECT sql FROM sqlite_schema WHERE name=?',(name,)).fetchone()[0])
  db.executemany('INSERT INTO docs(rowid,path,carrier,kind,sz,mtime_ns,sha,status,title,tags,content,scan) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',source.execute('SELECT rowid,path,carrier,kind,sz,mtime_ns,sha,status,title,tags,content,scan FROM docs'))
  db.execute("INSERT INTO ft(rowid,path,tags,content) SELECT rowid,path||' '||title,tags,content FROM docs")
 keeper=sqlite3.connect(p)
 assert keeper.execute('PRAGMA journal_mode=WAL').fetchone()[0]=='wal'
 keeper.execute('BEGIN IMMEDIATE');keeper.execute('UPDATE docs SET scan=scan WHERE rowid=1');keeper.commit()
 al=cor['aliases'];cw=cor['crosswalk']; rows=[]
 q=dict(id='life',term='evalmarker',scope='all')
 c=C.SearchEngine(p,al,cw); bind_b(al,cw); a=bind_a(p,al,cw)
 def check(name,query=q,fault=None,old_b=None):
  az=a(*args(query))
  for k in 'BC':
   start=time.perf_counter_ns()
   if k=='C' and fault is None:z,m=c.query_with_metrics(*args(query),debug=True)
   else:
    with engine(k,p,al,cw,fault=fault) as run:z,m=run(args(query),True)
   with ro(p) as conn:
    target=rowids(conn,query['term'],al)
   missed=len(target-set(m.get('candidate_rowids',[]))) if m['accelerated'] else None
   expected=name in {'fts_row_missing','docs_ft_mismatch','ddl','match'}
   rows.append(dict(case=name,engine=k,equal=az==z,missed=missed,accelerated=m['accelerated'],reason=(m.get('fallback_reason') or '').split(':')[0],safe=(not m['accelerated'] if expected else True),external_ms=(time.perf_counter_ns()-start)/1e6,verify_ms=m.get('verify_ms',m.get('generation_validation_ms')),reconnect=m.get('reconnect_reason')))
 def reindex(db,where,args=()):
  ids=[x[0] for x in db.execute('SELECT rowid FROM docs WHERE '+where,args)]
  db.executemany('DELETE FROM ft WHERE rowid=?',[(i,) for i in ids])
  db.execute("INSERT INTO ft(rowid,path,tags,content) SELECT rowid,path||' '||title,tags,content FROM docs WHERE "+where,args)
 def write(f):
  with closing(sqlite3.connect(p)) as db, db:f(db)
 check('initial_full');check('unchanged')
 def put(db,i):
  path=f'99_EVAL/{i}.md'; txt='evalmarker'
  db.execute('INSERT INTO docs(path,carrier,kind,sz,mtime_ns,sha,status,title,tags,content,scan) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(path,'synthetic','.md',len(txt),1,hashlib.sha256(path.encode()).hexdigest(),'OK','test title','tag',txt,1))
  reindex(db,'path=?',(path,))
 write(lambda db:put(db,1));check('insert')
 def update(db,sql,values,where):
  db.execute(sql,values);reindex(db,where)
 write(lambda db:update(db,"UPDATE docs SET content='evalmarker changed' WHERE path='99_EVAL/1.md'",(),"path='99_EVAL/1.md'"));check('content_change')
 write(lambda db:[put(db,i) for i in range(2,5)]);check('batch')
 write(lambda db:update(db,"UPDATE docs SET path='99_EVAL/renamed.md',title='evalmarker' WHERE path='99_EVAL/1.md'",(),"path='99_EVAL/renamed.md'"));check('rename_title_path')
 write(lambda db:db.execute("UPDATE docs SET status='PDF_TEXT_NOT_EXTRACTED' WHERE path='99_EVAL/renamed.md'"));check('status_only')
 with B.SearchSnapshot(p) as pin:
  before=pin.query(*args(q))
  write(lambda db:db.execute("UPDATE docs SET status='OK' WHERE path='99_EVAL/renamed.md'"))
  after=pin.query(*args(q))
  rows.append(dict(case='B_pinned_snapshot',engine='B',equal=before==after,safe=True,missed=None))
 check('new_snapshot_after_write')
 write(lambda db:(db.execute("DELETE FROM ft WHERE rowid IN (SELECT rowid FROM docs WHERE path='99_EVAL/2.md')"),db.execute("DELETE FROM docs WHERE path='99_EVAL/2.md'")));check('delete')
 write(lambda db:db.execute("DELETE FROM ft WHERE rowid IN (SELECT rowid FROM docs WHERE path='99_EVAL/3.md')"));check('fts_row_missing')
 write(lambda db:reindex(db,"path='99_EVAL/3.md'"))
 write(lambda db:db.execute("UPDATE docs SET content='mismatch evalmarker' WHERE path='99_EVAL/4.md'"));check('docs_ft_mismatch')
 write(lambda db:reindex(db,"path='99_EVAL/4.md'"));check('match',fault='match')
 with closing(sqlite3.connect(p)) as db:
  db.execute("UPDATE docs SET content='lost' WHERE path='99_EVAL/3.md'");db.rollback()
 check('rollback')
 c.close()
 keeper.execute('PRAGMA wal_checkpoint(TRUNCATE)');keeper.close()
 with closing(sqlite3.connect(p)) as db:assert db.execute('PRAGMA journal_mode=DELETE').fetchone()[0]=='delete'
 backup=P/'tests/recovery.sqlite'
 with closing(ro(p)) as x,closing(sqlite3.connect(backup)) as y:
  x.backup(y);assert y.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
  assert y.execute("SELECT count(*) FROM docs d LEFT JOIN ft f ON f.rowid=d.rowid WHERE f.rowid IS NULL OR f.path IS NOT d.path||' '||d.title OR f.tags IS NOT d.tags OR f.content IS NOT d.content").fetchone()[0]==0
  assert y.execute("SELECT count(*) FROM ft f LEFT JOIN docs d ON d.rowid=f.rowid WHERE d.rowid IS NULL").fetchone()[0]==0
  y.execute("INSERT INTO ft(ft) VALUES('integrity-check')");y.rollback()
 recovery,_=perform(backup,[q],al,cw,'recovery')
 for r in recovery:rows.append(dict(case='recovery_backup',engine=r['engine'],equal=r['equal'],safe=True,missed=r['missed']))
 with sqlite3.connect(p) as db:db.execute('PRAGMA wal_checkpoint(TRUNCATE)')
 c=C.SearchEngine(p,al,cw);check('before_replace')
 swap=P/'tests/replacement.sqlite'
 with closing(ro(backup)) as x,closing(sqlite3.connect(swap)) as y,y:
  x.backup(y);y.execute("UPDATE docs SET status='NEW_GENERATION' WHERE path='99_EVAL/renamed.md'")
 # Delete clean checkpoint sidecars only after all writable connections have closed.
 # No live WAL writer or committed content remains in sidecars.
 for suffix in ('-wal','-shm'):
  assert not pathlib.Path(str(p)+suffix).exists() or pathlib.Path(str(p)+suffix).stat().st_size==0 or suffix=='-shm'
 os.replace(swap,p);check('replace_generation');c.close()
 with sqlite3.connect(p) as db:
  db.execute('DROP TABLE ft');db.execute("CREATE VIRTUAL TABLE ft USING fts5(path,tags,content,tokenize='trigram',detail=none)")
  db.execute("INSERT INTO ft(rowid,path,tags,content) SELECT rowid,path||' '||title,tags,content FROM docs")
 c=C.SearchEngine(p,al,cw);check('ddl');c.close()
 return rows
def edge():
 p=P/'tests/edge.sqlite';shutil.copyfile(D/'scale1.sqlite',p)
 texts=['가나다라마바사','AbCdEf','100%_! "quoted"','한글음절','한글','a\u0301bc','before 😀가나','a\0needle']
 with sqlite3.connect(p) as db:
  for i,t in enumerate(texts):
   path=f'99_EVAL/edge{i}.md'; title='제목표본' if i==1 else 'edge'; tags='태그표본' if i==2 else 'edge'
   rid=db.execute('INSERT INTO docs(path,carrier,kind,sz,mtime_ns,sha,status,title,tags,content,scan) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(path,'synthetic','.md',len(t.encode()),1,hashlib.sha256(path.encode()).hexdigest(),'OK',title,tags,t,1)).lastrowid
   db.execute('INSERT INTO ft(rowid,path,tags,content) VALUES(?,?,?,?)',(rid,path+' '+title,tags,t))
 al={**cor['aliases'],'short-eval':['가나']}
 ts=['가나','가나다','나다라마','abcdef','%_!','"quoted"','한글음절','한글','a\u0301bc','😀가나','a\0needle','edge1.md','제목표본','태그표본','short-eval','before 😀','needle']
 return perform(p,[dict(id=f'X{i:02}',term=t,scope='all') for i,t in enumerate(ts)],al,cor['crosswalk'],'edge')[0]
if __name__=='__main__':
 setup_data()
 source=pathlib.Path('/Users/yongho/ROUTABL-TechAssets/40_WORKING/CW01_MVL01_FIRST_IGNITION_CLOSEOUT_R01_V01/SEARCH_REGRESSION.json')
 assert sha(source)=='6c2f0486b4ecc33aecde4156edbc2fe8f9b06cb717b937e60bdee3b9ea1a8cbf'
 assert [(x['term'],x['scope']) for x in j(source)['cases']]==[(x['term'],x['scope']) for x in cohort['operating_layer']]
 op,_=perform(D/'operating.sqlite',cohort['operating_layer'],OA,OX,'operating')
 aa=bind_a(D/'operating.sqlite',OA,OX)
 hist=[]
 for q,past in zip(cohort['operating_layer'],j(source)['cases']):
  z=aa(*args(q)); hist.append(dict(id=q['id'],match=z['match_count'],group=z['group_count'],manual=len(z['manual']),historical=past.get('match_group_manual_counts')))
 save('private/operating_historical_counts.json',hist)
 rr=list(op); acc=[]
 for n in (1,5,10):
  x,y=perform(D/f'scale{n}.sqlite',cohort['synthetic'],cor['aliases'],cor['crosswalk'],f'{n}x',True);rr+=x;acc+=y
 rr+=edge()
 save('private/functional.json',rr);writecsv('ACCURACY_COMPARISON.csv',acc)
 print('FUNCTION',dict(Counter((r['layer'],r['engine'],r['equal'],bool(r['missed'])) for r in rr)),flush=True)
 life=lifecycle();save('private/lifecycle.json',life)
 print('LIFE',len(life),[r for r in life if not r['equal'] or not r['safe'] or r['missed']],flush=True)
