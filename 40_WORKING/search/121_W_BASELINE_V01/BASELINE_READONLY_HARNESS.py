import ast, csv, hashlib, json, math, os, pathlib, re, sqlite3, statistics, sys, time, types
from urllib.parse import quote
h=pathlib.Path('/Users/yongho')
s=h/'Library/Application Support/ROUTABL-AssetSearch'
w=h/'ROUTABL-TechAssets/40_WORKING'
f=s/'routabl_search_v1_5_service.py'
p=s/'assets_v1_5.sqlite'
e=w/'CW01_MVL01_FIRST_IGNITION_CLOSEOUT_R01_V01/SEARCH_REGRESSION.json'
def emit(label,obj):
    print(label,json.dumps(obj,ensure_ascii=False,separators=(',',':')),flush=True)
def snapshot():
    q=p.stat()
    return [q.st_dev,q.st_ino,q.st_size,q.st_mtime_ns,q.st_ctime_ns]
def check_db():
    sidecars=[p.with_name(p.name+x) for x in ('-wal','-shm','-journal')]
    with p.open('rb') as fh:
        header=fh.read(100)
    if p.is_symlink() or header[18:20]!=b'\x01\x01' or any(x.exists() for x in sidecars):
        raise RuntimeError('DB guard')
def digest(path):
    hh=hashlib.sha256()
    with path.open('rb') as fh:
        for block in iter(lambda:fh.read(1048576),b''):
            hh.update(block)
    return hh.hexdigest()
check_db()
initial=snapshot()
expected='55b8747b145463c62366deba13904e3136893b8a611bb4ae94bbc2d7a642347d'
if digest(f)!=expected: raise RuntimeError('service hash guard')
t=ast.parse(f.read_text())
assigns={'STORE','PROJECT_ROOT','MANIFEST','INDEX','MAIN_PROJECTS','PROJECTS','SCOPE','ALIASES','CROSSWALK'}
funcs={'resolve_crosswalk','kind','safe_like','basename','relevant','query'}
nodes=[x for x in t.body if (isinstance(x,ast.FunctionDef) and x.name in funcs) or (isinstance(x,ast.Assign) and isinstance(x.targets[0],ast.Name) and x.targets[0].id in assigns)]
for node in nodes:
    if isinstance(node,ast.FunctionDef):
        node.returns=None
        for arg in node.args.args: arg.annotation=None
env={'Path':pathlib.Path,'json':json,'math':math,'Any':object}
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(f),'exec'),env)
if pathlib.Path(env['INDEX'])!=p: raise RuntimeError('INDEX guard')
emit('source_runtime',{'aliases':len(env['ALIASES']),'crosswalk_count':len(env['CROSSWALK']),'scopes':sorted(env['SCOPE'])})
uri='file:'+quote(str(p))+'?mode=ro'
timer=time.perf_counter_ns
plans={}
stats={}
run_start=time.monotonic()
def cap():
    deadline=time.monotonic()+0.55
    return lambda:int(time.monotonic()>deadline)
class MeterCursor:
    def __init__(self,cur,key): self.cur,self.key=cur,key
    def __iter__(self): return self
    def __next__(self):
        a=timer()
        try: return next(self.cur)
        finally: stats[self.key]+=timer()-a
class MeterDB:
    def __init__(self,requested,*,uri,timeout):
        if not uri or requested!='file:'+str(p)+'?mode=ro': raise RuntimeError('unexpected SQLite target')
        a=timer()
        self.db=sqlite3.connect('file:'+quote(str(p))+'?mode=ro',uri=True,timeout=0.05)
        self.db.execute('PRAGMA query_only=ON')
        self.db.execute('PRAGMA temp_store=MEMORY')
        self.db.set_progress_handler(cap(),1000)
        stats['connect']+=timer()-a
    def __enter__(self): return self
    def __exit__(self,*args): self.db.close()
    @property
    def row_factory(self): return self.db.row_factory
    @row_factory.setter
    def row_factory(self,val): self.db.row_factory=val
    def execute(self,sql,params=()):
        key='docs' if ' FROM docs WHERE ' in sql else 'manual' if ' FROM manual' in sql else None
        if key is None or not sql.startswith('SELECT '): raise RuntimeError('SQL guard')
        if (key,len(params)) not in plans:
            plans[key,len(params)]=[r[3] for r in self.db.execute('EXPLAIN QUERY PLAN '+sql,params)]
        self.db.set_progress_handler(cap(),1000)
        a=timer()
        try: return MeterCursor(self.db.execute(sql,params),key)
        finally: stats[key]+=timer()-a
env['sqlite3']=types.SimpleNamespace(connect=MeterDB,Row=sqlite3.Row)
cases=json.loads(e.read_text())['cases']
if len(cases)!=9: raise RuntimeError('case count')
def feature(case):
    term=case['term']
    if term in env['ALIASES']: return 'configured_alias'
    if re.search('[ㄱ-ㅎㅏ-ㅣ]',term): return 'hangul_jamo'
    if re.search('[가-힣]',term): return 'hangul_or_mixed'
    if re.fullmatch('[A-Z0-9]+(?:-[A-Z0-9.]+)+',term): return 'asset_id_like'
    return 'latin_or_other'
def once(case):
    stats.clear()
    stats.update(connect=0,docs=0,manual=0)
    a=timer()
    q=env['query'](case['term'],scope=case['scope'])
    full=timer()-a
    sql=stats['docs']+stats['manual']
    return [full,sql,stats['docs'],stats['manual'],stats['connect'],max(0,full-sql-stats['connect'])],q
def ptl(ordered,p):
    return ordered[math.ceil(len(ordered)*p)-1]
def summary(vals):
    result=[]
    for xs in zip(*vals):
        v=sorted(xs)
        result.append([round(x/1e6,4) for x in (statistics.mean(v),ptl(v,.5),ptl(v,.95),v[-1])])
    return result
cold=[]
for i,c in enumerate(cases):
    # This first request has a new connection and may incur a first EXPLAIN per SQL shape.
    v,q=once(c)
    cold.append(v)
    counts=[q['match_count'],q['group_count'],len(q['manual'])]
    page_group_ok=all(g['duplicate_count']>=len(g['locations']) and len(g['locations'])==min(25,g['duplicate_count']) for g in q['results'])
    emit('regression',[f'R{i+1:02}',feature(c),c['scope'],counts,counts==c['match_group_manual_counts'],page_group_ok])
emit('first_ms',[[round(y/1e6,4) for y in x] for x in cold])
repeat=[[] for c in cases]
for round_id in range(30):
    for j in range(9):
        if time.monotonic()-run_start>55: raise RuntimeError('batch time guard')
        i=(j+round_id)%9
        repeat[i].append(once(cases[i])[0])
for i,row in enumerate(repeat):
    emit('timings',[f'R{i+1:02}',len(row),summary(row)])
emit('aggregate',summary([a for row in repeat for a in row]))
emit('plans',[[k[0],k[1],v] for k,v in plans.items()])
with sqlite3.connect(uri,uri=True,timeout=0.05) as db:
    db.execute('PRAGMA query_only=ON')
    db.execute('PRAGMA temp_store=MEMORY')
    for key,sql,args in [
        ('path_exact','EXPLAIN QUERY PLAN SELECT path FROM docs WHERE path=?',('__121_probe__',)),
        ('manual_id_exact','EXPLAIN QUERY PLAN SELECT id FROM manual WHERE id=?',('__121_probe__',)),
        ('fts_match','EXPLAIN QUERY PLAN SELECT rowid FROM ft WHERE ft MATCH ?',('__121_probe__',)),
    ]:
        emit('control_plan',[key,[r[3] for r in db.execute(sql,args)]])
    db.set_progress_handler(cap(),1000)
    try: emit('dbstat',list(db.execute('SELECT name, sum(pgsize), count(*) FROM dbstat GROUP BY name ORDER BY name')))
    except sqlite3.OperationalError: emit('dbstat','NOT_TESTED')
check_db()
if initial!=snapshot(): raise RuntimeError('DB identity/metadata changed during run')
emit('db_sha256',digest(p))
check_db()
if initial!=snapshot(): raise RuntimeError('DB identity/metadata changed after hash')
emit('stable_db_stat',initial)
emit('elapsed_s',round(time.monotonic()-run_start,3))
