from core import *
from contextlib import ExitStack
import argparse, subprocess
orders=['ABC','ACB','BAC','BCA','CAB','CBA']
fields=('scale','layer','mode','id','type','selectivity','fts_eligible','rep','order','engine','status','latency_ms','serialization_ms','outer_ms','connection_ms','verify_ms','verify_performed','fts_ms','recheck_fetch_ms','manual_ms','sqlite_ms','post_ms','candidates','confirmed','accelerated','fallback','reconnect','rss_peak_bytes')
def rank(a,p):
 a=sorted(a)
 return a[max(0,math.ceil(p*len(a))-1)] if a else None
def outfile(name):
 f=(P/name).open('x',newline='',encoding='utf-8');w=csv.DictWriter(f,fieldnames=fields);w.writeheader();return f,w
def sample(run,q,k,scope,mode,i,order,w,extra=0):
 t=time.perf_counter_ns()
 try:
  z,m=run(args(q));t1=time.perf_counter_ns()
  json.dumps(z,ensure_ascii=False,separators=(',',':'));t2=time.perf_counter_ns()
  status='OK';dl=(t1-t)/1e6+extra;sz=(t2-t1)/1e6
 except Exception as e:
  m={};status=type(e).__name__;dl=(time.perf_counter_ns()-t)/1e6;sz=None
 verify=m.get('verify_ms',m.get('generation_validation_ms'))
 if k=='B' and mode=='reuse':verify=0.0
 conn=m.get('t_connect_ms',m.get('connection_ms'))
 if k=='B' and mode=='reuse':conn=0.0
 w.writerow(dict(scale=scope,layer=q.get('layer','mixed'),mode=mode,id=q['id'],type=q.get('type',''),selectivity=q.get('cohort',''),fts_eligible=q.get('eligible',''),rep=i,order=order,engine=k,status=status,latency_ms=round(dl,6),serialization_ms=sz,outer_ms=dl+(sz or 0),connection_ms=conn,verify_ms=verify,verify_performed=m.get('verify_performed', k=='B' and mode!='reuse'),fts_ms=m.get('t_fts_ms'),recheck_fetch_ms=m.get('t_docs_ms'),manual_ms=m.get('t_manual_ms'),sqlite_ms=m.get('t_sql_total_ms',m.get('sqlite_fetch_ms')),post_ms=m.get('t_post_ms',m.get('postprocess_ms')),candidates=m.get('fts_candidates',m.get('candidate_count')),confirmed=m.get('confirmed_rows',m.get('matched_before_scope')),accelerated=m.get('accelerated'),fallback=(m.get('fallback_reason') or '').split(':')[0],reconnect=m.get('reconnect_reason')))
def freeze_plan():
 targets={}
 for q in aux['cases']:
  p=D/'scale1.sqlite'
  if q['id'] in ('FAULT-FT-MISSING','FAULT-FT-DDL'):
   p=P/'tests'/f"{q['id']}.sqlite";shutil.copyfile(D/'scale1.sqlite',p)
   with sqlite3.connect(p) as db:
    if q['id']=='FAULT-FT-MISSING':
     cur=db.execute("DELETE FROM ft WHERE rowid=(SELECT rowid FROM docs WHERE path='00_SYNTHETIC/SIM-001.md')")
     assert cur.rowcount==1
    else:
     db.execute('DROP TABLE ft');db.execute("CREATE VIRTUAL TABLE ft USING fts5(path,tags,content,tokenize='trigram',detail=none)")
     db.execute("INSERT INTO ft(rowid,path,tags,content) SELECT rowid,path||' '||title,tags,content FROM docs")
  targets[q['id']]=dict(path=str(p.relative_to(P)),sha=sha(p),definition=q)
 s=j(D/'scale.json')
 plan=dict(orders=orders,repeat_each_query=30,bench_primary='each mode compared separately',casefile_sha=sha(D/'EVALUATION_BOUNDARY_AUXILIARY.json'),aux=targets,scales=s['scales'],process_first_policy='fixed first selective query, 30 independent processes per engine and scale; other cold queries not tested',generation_first_policy='same fixed selective query x30 distinct contexts per scale, B includes context entry',mixed_policy='50 equal weights, no auxiliary samples',aux_connection_modes=['reuse','fresh'],fault_match_policy='one MATCH denial per trial; this trial invokes MATCH once')
 save('private/measurement_plan.json',plan)
 print('PLAN',sha(D/'measurement_plan.json'),flush=True)
def mixed(mode,n):
 p=D/f'scale{n}.sqlite'
 plan=j(D/'measurement_plan.json')
 classified={r['id']:r for z in plan['scales'] if z['scale']==n for r in z['classifications']}
 qs=[{**q,**classified[q['id']]} for q in cohort['synthetic']]
 f,w=outfile(f'private/raw_{mode}_{n}x.csv')
 try:
  with ExitStack() as st:
   runs={k:st.enter_context(engine(k,p,cor['aliases'],cor['crosswalk'],mode)) for k in 'ABC'}
   if mode=='reuse':
    for k in 'ABC':runs[k](args(next(q for q in qs if q['cohort']=='selective')))
   for i in range(30):
    for qi,q in enumerate(qs):
     order=orders[(i+qi)%6]
     for k in order:sample(runs[k],q,k,n,mode,i,order,w)
    f.flush()
    if i%5==4:print('PROGRESS',mode,n,i+1,flush=True)
 finally:f.close()
def auxbench():
 plan=j(D/'measurement_plan.json');f,w=outfile('private/raw_aux.csv')
 try:
  for id,s in plan['aux'].items():
   q={**s['definition'],'layer':'aux','type':id,'cohort':'dense' if id=='PERF-DENSE-1X' else '', 'eligible':id=='PERF-DENSE-1X'}
   p=P/s['path'];assert sha(p)==s['sha']
   al={**cor['aliases'],**q.get('extra_aliases',{})}
   for mode in ('reuse','fresh'):
    with ExitStack() as st:
     # An authorization error is injected in a temporary connection; it has its own matched fresh condition.
     if id=='FAULT-MATCH' and mode=='fresh':continue
     runs={k:st.enter_context(engine(k,p,al,cor['crosswalk'],mode,'match' if id=='FAULT-MATCH' else None)) for k in 'ABC'}
     for k in 'ABC':runs[k](args(q))
     for i in range(30):
      order=orders[i%6]
      for k in order:sample(runs[k],q,k,1,mode,i,order,w)
   f.flush()
 finally:f.close()
def firsts():
 f,w=outfile('private/raw_first.csv')
 try:
  q0=next(q for q in cohort['synthetic'] if q['cohort']=='selective')
  q={**q0,'layer':'first_diagnostic','eligible':True}
  for n in (1,5,10):
   for i in range(30):
    order=orders[i%6]
    for k in order:
     p=D/f'scale{n}.sqlite';t=time.perf_counter_ns()
     with engine(k,p,cor['aliases'],cor['crosswalk'],'reuse') as run:
      extra=(time.perf_counter_ns()-t)/1e6
      sample(run,q,k,n,'first_generation',i,order,w,extra)
     start=time.perf_counter_ns()
     res=subprocess.run([sys.executable,'-B',str(P/'code/bench.py'),'child',k,str(n),q['id']],capture_output=True,text=True,timeout=45,check=True)
     item=json.loads(res.stdout)
     w.writerow(dict(scale=n,layer='first_diagnostic',mode='first_process',id=q['id'],type=q['type'],selectivity=q['cohort'],fts_eligible=True,rep=i,order=order,engine=k,status='OK',latency_ms=item['query_ms'],outer_ms=(time.perf_counter_ns()-start)/1e6,connection_ms=item.get('connection'),verify_ms=item.get('verify'),rss_peak_bytes=item.get('rss')))
   f.flush()
   print('FIRSTS',n,flush=True)
 finally:f.close()
def child(k,n,id):
 import resource
 p=D/f'scale{n}.sqlite';q=next(q for q in cohort['synthetic'] if q['id']==id)
 t=time.perf_counter_ns()
 with engine(k,p,cor['aliases'],cor['crosswalk'],'fresh') as run:z,m=run(args(q))
 print(json.dumps(dict(query_ms=(time.perf_counter_ns()-t)/1e6,connection=m.get('connection_ms',m.get('t_connect_ms')),verify=m.get('generation_validation_ms',m.get('verify_ms')),rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)))
if __name__=='__main__':
 a=sys.argv[1:]
 if a[0]=='child':child(a[1],int(a[2]),a[3])
 elif a[0]=='plan':freeze_plan()
 elif a[0]=='aux':auxbench()
 elif a[0]=='first':firsts()
 else:mixed(a[0],int(a[1]))
