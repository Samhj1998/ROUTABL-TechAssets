from core import *
from bench import rank, outfile, orders
from contextlib import closing
from collections import Counter
import statistics
def native():
 f,w=outfile('private/raw_native_A.csv')
 try:
  for n in (1,5,10):
   query=bind_a(D/f'scale{n}.sqlite',cor['aliases'],cor['crosswalk'])
   for i in range(30):
    qs=cohort['synthetic'];qs=qs[i%len(qs):]+qs[:i%len(qs)]
    for q in qs:
     t=time.perf_counter_ns()
     try:r=query(*args(q));dt=(time.perf_counter_ns()-t)/1e6;state='OK'
     except Exception as e:dt=(time.perf_counter_ns()-t)/1e6;state=type(e).__name__
     w.writerow(dict(scale=n,layer='native_A_diagnostic',mode='fresh_native_A',id=q['id'],type=q['type'],selectivity=q['cohort'],rep=i,order='A',engine='A',status=state,latency_ms=dt))
   f.flush();print('NATIVE',n,flush=True)
 finally:f.close()
def stats(rows,fields):
 metrics={}
 for key in fields:
  a=[float(r[key]) for r in rows if r.get(key) not in (None,'') and r.get('status','OK')=='OK']
  metrics[key]=dict(n=len(a),mean=statistics.mean(a) if a else None,p50=rank(a,.5),p95=rank(a,.95),max=max(a) if a else None)
 return metrics
def finish():
 sources=sorted(D.glob('raw*.csv'))
 rows=[r for f in sources for r in csv.DictReader(f.open())]
 writecsv('ABC_BENCHMARK_RAW.csv',rows)
 sample_groups=defaultdict(list)
 for r in rows:
  prefix=(r['scale'],r['layer'],r['mode'],r['engine'])
  sample_groups[(*prefix,'query',r['id'])].append(r)
  sample_groups[(*prefix,'type',r['type'])].append(r)
  sample_groups[(*prefix,'all','all')].append(r)
  if r['layer']=='mixed' and r['selectivity']=='selective' and r['fts_eligible']=='True':sample_groups[(*prefix,'gate','selective_3plus')].append(r)
 fields=('latency_ms','serialization_ms','outer_ms','connection_ms','verify_ms','fts_ms','recheck_fetch_ms','manual_ms','sqlite_ms','post_ms','candidates','confirmed','rss_peak_bytes')
 records=[]
 for (scale,layer,mode,k,bucket,id),samples in sorted(sample_groups.items()):
  m=stats(samples,fields)
  rec=dict(scale=scale,layer=layer,mode=mode,engine=k,bucket=bucket,id=id,n=len(samples),errors=sum(x['status']!='OK' for x in samples),accelerated=sum(x['accelerated']=='True' for x in samples),fallback=dict(Counter(x['fallback'] for x in samples if x['fallback'] not in ('','baseline'))),metrics=m)
  records.append(rec)
 save('private/performance_aggregate.json',records)
 writecsv('private/benchmark_grouped.csv',[{**{k:r[k] for k in ('scale','layer','mode','engine','bucket','id','n','errors','accelerated','fallback')},**{f'{k}_{v}':o[v] for k,o in r['metrics'].items() for v in ('mean','p50','p95','max')}} for r in records])
 ix=[]
 for f in sorted(D.glob('index_*x.csv')):ix+=list(csv.DictReader(f.open()))
 writecsv('private/index_raw.csv',ix)
 ig=defaultdict(list)
 for r in ix:ig[(r['scale'],r['scenario'],r['engine'])].append(r)
 idx=[dict(scale=n,scenario=kind,engine=k,n=len(v),metrics=stats(v,[x for x in v[0] if x not in ('scale','scenario','engine','rep')])) for (n,kind,k),v in sorted(ig.items())]
 save('private/index_aggregate.json',idx)
 acc=list(csv.DictReader((P/'ACCURACY_COMPARISON.csv').open()))
 ac=defaultdict(list)
 for r in acc:ac[(r['layer'],r['split'],r['engine'])].append(r)
 scores=[dict(layer=l,split=s,engine=e,n=len(v),**{f:statistics.mean(float(r[f]) for r in v) for f in ('recall','precision','mrr','ndcg')},**{f:sum(r[f]=='True' for r in v) for f in ('top','sha','status','version','duplicates')}) for (l,s,e),v in sorted(ac.items())]
 save('private/accuracy_summary.json',scores)
 print('SUM',len(rows),len(records),len(ix),len(scores),flush=True)
if __name__=='__main__':
 if sys.argv[-1]=='native':native()
 else:finish()
