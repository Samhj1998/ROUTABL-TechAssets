import ast, hashlib, json, math, os, pathlib as p, platform, socket, sqlite3, statistics, time, unicodedata, sys
from urllib.parse import quote
os.umask(0o077)
w=p.Path('/Users/yongho/ROUTABL-TechAssets/40_WORKING')
out=w/'121_W_ABC_EVALUATION_V01'
base=w/'121_W_BASELINE_V01'
app=p.Path('/Users/yongho/Library/Application Support/ROUTABL-AssetSearch')
src=app/'assets_v1_5.sqlite'
old=app/'routabl_assetsearch_v1_1.py'
sha=lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
pin='c5a800f36aaaeddd1b5aad086403df115fa8f99fb8f616271421e89dff71cba4'
assert socket.gethostname().lower()=='macstudioui-macstudio.local'
assert not out.is_symlink() and out.is_dir() and sha(src)==pin
def sides(f):
 return {s:p.Path(str(f)+s).exists() for s in ('-journal','-wal','-shm')}
assert not any(sides(src).values())
def ro(f):
 c=sqlite3.connect('file:'+quote(str(f))+'?mode=ro',uri=True,timeout=2)
 c.execute('PRAGMA query_only=ON')
 return c
def make(f):
 f.touch(exist_ok=False)
 return sqlite3.connect(f,timeout=2)
def integrity(c):
 c.execute('BEGIN')
 try: c.execute("INSERT INTO ft(ft) VALUES('integrity-check')")
 finally: c.rollback()
def count(c,sql):
 return c.execute(sql).fetchone()[0]
def concordance(c):
 items={
 'docs':'SELECT count(*) FROM docs','ft':'SELECT count(*) FROM ft',
 'missing_ft':'SELECT count(*) FROM docs d LEFT JOIN ft f ON f.rowid=d.rowid WHERE f.rowid IS NULL',
 'orphan_ft':'SELECT count(*) FROM ft f LEFT JOIN docs d ON d.rowid=f.rowid WHERE d.rowid IS NULL',
 'path_exact':'SELECT count(*) FROM docs d JOIN ft f ON f.rowid=d.rowid WHERE f.path=d.path',
 'path_plus_title':'SELECT count(*) FROM docs d JOIN ft f ON f.rowid=d.rowid WHERE f.path=d.path||char(32)||d.title',
 'path_other':'SELECT count(*) FROM docs d JOIN ft f ON f.rowid=d.rowid WHERE f.path IS NOT d.path AND f.path IS NOT d.path||char(32)||d.title',
 'path_join_misses':'SELECT count(*) FROM docs d WHERE d.rowid IN (SELECT f.rowid FROM ft f) AND d.path NOT IN (SELECT f.path FROM ft f WHERE f.path IS NOT NULL)',
 'tags_or_content_mismatch':'SELECT count(*) FROM docs d JOIN ft f ON f.rowid=d.rowid WHERE d.tags IS NOT f.tags OR d.content IS NOT f.content',
 'manual':'SELECT count(*) FROM manual'}
 return {k:count(c,v) for k,v in items.items()}
r={'environment':{'python':platform.python_version(),'sqlite':sqlite3.sqlite_version,'macOS':platform.mac_ver()[0],'arch':platform.machine(),'host':socket.gethostname(),'time_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}}
snapshot=out/'OPERATING_DB_EVALUATOR_ONLY.sqlite'
source=ro(src)
r['source_journal_mode']=count(source,'PRAGMA journal_mode')
assert r['source_journal_mode']=='delete'
op=make(snapshot)
t=time.monotonic()
def progress(status,remaining,total):
 if time.monotonic()-t>15: raise TimeoutError('backup time bound')
source.backup(op,pages=256,progress=progress,sleep=.05)
source.close()
r['backup_ms']=round((time.monotonic()-t)*1000,2)
r['schema']=list(op.execute("SELECT type,name,sql FROM sqlite_schema WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"))
r['schema_columns_ft']=list(op.execute('PRAGMA table_xinfo(ft)'))
r['operating_counts']=concordance(op)
r['operating_quick_check']=count(op,'PRAGMA quick_check')
integrity(op)
r['operating_native_fts_check']='ok'
r['operating_bytes_objects']=dict(op.execute("SELECT name,sum(pgsize) FROM dbstat GROUP BY name"))
op.close()
snapshot.chmod(0o400)
r['snapshot']={'bytes':snapshot.stat().st_size,'sha':sha(snapshot),'sidecars':sides(snapshot)}
assert sha(src)==pin and not any(sides(src).values())
for n,h in {'SYNTHETIC_CORPUS_V01.json':'840ecf1ea98a59fa20d499e559205ceae130c513aa68531e295cb129e01a7b8b','SYNTHETIC_DEV_V01.json':'db2fca0951c1c43d30da560d7ecafd6c967e7ff9389c21c773b347714a93f3a1'}.items():
 assert sha(base/n)==h
assert sha(old)=='bdea926cabe2157bdec2f8d0c69173e1a50dfa35ec5cae40563f16711588cc83'
legacy=ast.parse(old.read_text())
ns={}
exec(compile(ast.Module(body=[x for x in legacy.body if isinstance(x,ast.FunctionDef) and x.name in {'setup','add'}],type_ignores=[]),str(old),'exec'),ns)
setup,add=ns['setup'],ns['add']
build=next(x for x in legacy.body if isinstance(x,ast.FunctionDef) and x.name=='build')
purge=[x.value for x in ast.walk(build) if isinstance(x,ast.Constant) and isinstance(x.value,str) and x.value.startswith(('DELETE FROM docs WHERE scan','DELETE FROM ft WHERE rowid IN'))]
assert len(purge)==2 and purge[0].startswith('DELETE FROM ft')
def put(c,d,mt=100,epoch=1):
 content=d['content']
 return add(c,d['path'],d['path'],'.md',len(content.encode()),mt,d.get('sha') or hashlib.sha256(content.encode()).hexdigest(),d.get('status','OK'),d.get('title','Neutral'),d.get('tags',''),content,epoch)
def dbmem():
 c=sqlite3.connect(':memory:')
 setup(c)
 return c
def like(t): return '%'+t.replace('!','!!').replace('%','!%').replace('_','!_')+'%'
def literal(t): return '"'+t.replace('"','""')+'"'
def query(cols,terms):
 return ' OR '.join(f"{col} LIKE ? ESCAPE '!'" for t in terms for col in cols),[like(t) for t in terms for col in cols]
def ids(c,sql,params=()):
 return {row[0] for row in c.execute(sql,params)}
def candidate(c,terms):
 pr,b=query(('path','title','tags','content'),terms)
 want=ids(c,'SELECT rowid FROM docs WHERE '+pr,b)
 tr,tb=query(('title',),terms)
 title=ids(c,'SELECT rowid FROM docs WHERE '+tr,tb)
 match=' OR '.join(map(literal,terms))
 ft=ids(c,'SELECT rowid FROM ft WHERE ft MATCH ?',(match,))
 bypath=ids(c,'SELECT d.rowid FROM docs d WHERE d.path IN (SELECT path FROM ft WHERE ft MATCH ?)',(match,))
 return {'like':len(want),'match':len(ft),'title':len(title),'miss_match':len(want-ft),'miss_rowid_union':len(want-(ft|title)),'miss_path_union':len(want-(bypath|title)),'extra_rowid_union':len((ft|title)-want),'fallback_short':any(len(t)<3 for t in terms)}
edge=dbmem()
examples=[
 ('T01','generic','tag','가나다라마바사'),
 ('T02','한글제목만','tag','placeholder'),
 ('T03-경로식별','generic','tag','unrelated'),
 ('T04','generic','태그식별','unrelated'),
 ('T05','generic','tag','Prefix AlphaBETA 100%_! "double quote" unit-test'),
 ('T06','generic','tag','prefix æther 100XY "different quote" unit test'),
 ('T07','generic','tag','prefix Æther'),
 ('T08','generic','tag',unicodedata.normalize('NFD','한글음절')),
 ('T09','generic','tag','한글음절'),
 ('T10','generic','tag','0ab\x00needleTail'),
 ('T11','generic','tag','xyz\x00tail'),
 ('T12','generic','tag','100%_! extra OR (AND)'),
 ('T13','generic','tag','before 😀가나 after'),
 ('T14','generic','tag','ㄱㅈㄱㅊ')]
for path,title,tags,content in examples: put(edge,dict(path=path,title=title,tags=tags,content=content))
edge.commit()
r['edge']={k:candidate(edge,terms) for k,terms in [
 ('ko2',['가나']),('ko3',['가나다']),('ko4',['나다라마']),('title_only',['제목만']),('path',['경로식별']),('tag',['태그식별']),
 ('short_alias_or',['no-result-for-long-key','가나']),('ascii_case',['alphabeta']),('unicode_case',['æther']),('percent_underscore_escape',['%_!']),('double_quote',['"double quote"']),('space',['unit test']),('hyphen',['unit-test']),('boolean_literal',['OR (AND)']),('nfc',['한글음절']),('nfd',[unicodedata.normalize('NFD','한글음절')]),('jamo_literal',['ㄱㅈㄱㅊ']),('emoji',['😀가나']),('only_spaces',['   '])]}
for term in ('\x00abc','ab\x00tail'):
 try: r['edge']['query_nul_'+str(len(term))]=candidate(edge,[term])
 except sqlite3.Error as e: r['edge']['query_nul_'+str(len(term))]={'error':str(e)}
r['variants']={}
for spec,extra in [('full',''),('column',',detail=column'),('none',',detail=none'),('sensitive',',tokenize placeholder')]:
 c=sqlite3.connect(':memory:')
 c.execute("CREATE VIRTUAL TABLE probe USING fts5(body,tokenize='trigram"+(' case_sensitive 1' if spec=='sensitive' else '')+"'"+('' if spec=='sensitive' else extra)+")")
 c.execute("INSERT INTO probe VALUES('가나다라마 Alpha æther')")
 data={}
 for key,term in [('ko2','가나'),('ko3','가나다'),('ko4','가나다라'),('ascii_case','alpha')]:
  try: data[key]=len(ids(c,'SELECT rowid FROM probe WHERE probe MATCH ?',(literal(term),)))
  except sqlite3.Error as e: data[key]=str(e)
 data['like_eq']=len(ids(c,"SELECT rowid FROM probe WHERE body LIKE ? ESCAPE '!'",('%alpha%',)))
 data['like_plan']=list(c.execute('EXPLAIN QUERY PLAN SELECT rowid FROM probe WHERE body LIKE ?',('%alpha%',)))
 data['like_escaped_plan']=list(c.execute("EXPLAIN QUERY PLAN SELECT rowid FROM probe WHERE body LIKE ? ESCAPE '!'",('%alpha%',)))
 r['variants'][spec]=data
 c.close()
edge.close()
fix=out/'SYNTHETIC_DEV_FIXTURE_V01.sqlite'
c=make(fix)
setup(c)
corpus=json.loads((base/'SYNTHETIC_CORPUS_V01.json').read_bytes())
dev=json.loads((base/'SYNTHETIC_DEV_V01.json').read_bytes())
assert len(corpus['docs'])==1230 and len(dev)==30 and len({q['id'] for q in dev})==30
assert {q['split'] for q in dev}=={'dev'}
for d in corpus['docs']: put(c,d)
c.commit()
r['fixture_counts']=concordance(c)
r['fixture_qrels_paths_present']=all(set([q['top_path'],*q['duplicate_paths']]).issubset({d['path'] for d in corpus['docs']}) for q in dev)
r['dev']={}
for q in dev:
 term=q['term']; terms=[term]+[a for a in corpus['aliases'].get(term,()) if a.casefold()!=term.casefold()]
 r['dev'][q['id']]={'kind':q['kind'],**candidate(c,terms)}
r['timing']={}
for label,terms in [('selective',[next(q['term'] for q in dev if q['kind']=='body_only')]) ,('broad',['SIM'])] if any(q['kind']=='body_only' for q in dev) else [('selective',[next(q['term'] for q in dev if q['kind'] in ('body','body_infix','exact_id'))]),('broad',['SIM'])]:
 pr,b=query(('path','title','tags','content'),terms)
 tr,tb=query(('title',),terms)
 m=' OR '.join(map(literal,terms))
 ids_sql='SELECT rowid FROM ft WHERE ft MATCH ?'
 raw_ids=sorted(ids(c,ids_sql,(m,)))
 key_constraint='rowid IN ('+','.join('?' for _ in raw_ids)+')' if raw_ids else '0'
 shapes={'a_like':('SELECT rowid FROM docs WHERE '+pr,b),'title_scan':('SELECT rowid FROM docs WHERE '+tr,tb),'fts_match':(ids_sql,(m,)),'recheck_only':('SELECT rowid FROM docs WHERE '+key_constraint+' AND ('+pr+')',(*raw_ids,*b))}
 sample={k:[] for k in shapes}
 for k,(sql,bv) in shapes.items(): list(c.execute(sql,bv))
 order=list(shapes)
 for i in range(30):
  for k in order[i%len(order):]+order[:i%len(order)]:
   sql,bv=shapes[k]
   t=time.perf_counter_ns(); fetched=list(c.execute(sql,bv)); ms=(time.perf_counter_ns()-t)/1e6
   sample[k].append(ms)
 r['timing'][label]={k:{'rows':len(list(c.execute(sql,bv))),'plan':[z[-1] for z in c.execute('EXPLAIN QUERY PLAN '+sql,bv)],'avg_ms':round(statistics.mean(sample[k]),4),'p50_ms':round(sorted(sample[k])[14],4),'p95_ms':round(sorted(sample[k])[28],4),'max_ms':round(max(sample[k]),4)} for k,(sql,bv) in shapes.items()}
integrity(c)
c.close()
fix.chmod(0o400)
r['fixture']={'bytes':fix.stat().st_size,'sha':sha(fix)}
l=dbmem()
def doc(path,content):return dict(path=path,content=content)
def has(s):return bool(ids(l,'SELECT rowid FROM ft WHERE ft MATCH ?',(literal(s),)))
def checked():
 v=concordance(l)
 return not any(v[k] for k in ('missing_ft','orphan_ft','path_other','tags_or_content_mismatch'))
lc={}
put(l,doc('initial.md','oldtoken')); l.commit()
lc['insert_and_read']=has('oldtoken') and checked()
unchanged=put(l,doc('initial.md','newtoken'),100,2); l.commit()
lc['same_size_mtime_leaves_old']=unchanged=='unchanged' and has('oldtoken') and not has('newtoken') and checked()
put(l,doc('initial.md','newtoken'),101,3); l.commit()
lc['update_changed_mtime']=has('newtoken') and not has('oldtoken') and checked()
put(l,doc('renamed.md','newtoken'),101,4); l.commit()
lc['add_only_rename_leaves_old']=count(l,'SELECT count(*) FROM docs')==2 and checked()
for s in purge:l.execute(s,(4,))
l.commit()
lc['rename_with_legacy_purge']=count(l,"SELECT count(*) FROM docs WHERE path='renamed.md'")==1 and count(l,'SELECT count(*) FROM docs')==1 and checked()
l.execute('DELETE FROM ft'); l.commit(); integrity(l)
lc['native_check_misses_missing_docs_row']=not checked()
put(l,doc('renamed.md','newtoken'),102,5); l.commit(); integrity(l)
lc['repair_both_checks']=checked() and has('newtoken')
put(l,doc('renamed.md','badtoken'),103,5); l.rollback()
lc['transaction_rollback']=checked() and has('newtoken') and not has('badtoken')
for s in purge:l.execute(s,(6,))
l.commit()
lc['delete_with_legacy_purge']=count(l,'SELECT count(*) FROM docs')==0 and not has('newtoken') and checked()
r['lifecycle']=lc
l.close()
assert sha(src)==pin and not any(sides(src).values())
r['source_post_sha']=sha(src)
with (out/'FTS5_MEASURED_EVIDENCE.json').open('x') as f: json.dump(r,f,ensure_ascii=False,indent=2,sort_keys=True)
print(json.dumps({**r,'dev':{'total':len(r['dev']),'kind':sorted(set(x['kind'] for x in r['dev'].values())),'miss_match':sum(x['miss_match'] for x in r['dev'].values()),'miss_rowid_union':sum(x['miss_rowid_union'] for x in r['dev'].values()),'miss_path_union':sum(x['miss_path_union'] for x in r['dev'].values()),'short':sum(x['fallback_short'] for x in r['dev'].values())}},ensure_ascii=False,sort_keys=True))
