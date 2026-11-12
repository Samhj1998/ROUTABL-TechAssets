from core import *
import platform, socket, subprocess, datetime
from collections import Counter,defaultdict
DROOT='/Users/yongho/ROUTABL-TechAssets/40_WORKING/121_W_ABC_BENCHMARK_V01/'
def put(name,s):
 with (P/name).open('x',encoding='utf-8') as f:f.write(s.rstrip()+'\n')
def fmt(x):
 return '—' if x is None else f'{x:,.3f}'
def pct(x):
 return '—' if x is None else f'{x:+.1f}%'
def protection():
 h=pathlib.Path('/Users/yongho')
 working=h/'ROUTABL-TechAssets/40_WORKING'
 old=working/'121_W_ABC_IMPLEMENTATION_V01'
 app=h/'Library/Application Support/ROUTABL-AssetSearch'
 b=h/'121_CHATGPT_B_V01/implementation'
 c=h/'121_CLAUDE_ISOLATED_V01/implementation'
 known=[
 (app/'routabl_search_v1_5_service.py','55b8747b145463c62366deba13904e3136893b8a611bb4ae94bbc2d7a642347d'),
 (app/'assets_v1_5.sqlite','c5a800f36aaaeddd1b5aad086403df115fa8f99fb8f616271421e89dff71cba4'),
 (old/'SHA256SUMS','b2f51c92eb8d163e2dcce122d89c69dbcb32a8fd33d2576e402cc70a921da522'),
 (b/'src/search_b.py','f46f64e2479a331c6bd6822f7b0b41af2fbceeab801bb27ad679dce108d1950d'),
 (c/'src/asset_search_fts.py','0a33cd62f47d530813ba23e30eb0616945469a42ffba105714b02a827b576a3b'),
 (b/'output/SHA256SUMS','70ec00dfe861be12aa075ec0011dd9bab58dafeae1d6f3829f9b441d3f795a28'),
 (c/'output/SHA256SUMS','aa3d4118bbe6ad85ee627230af3d39635bc9a7397995fedfcfc85a0565c9b16e'),
 (old/'EVALUATION_COHORT_PRIVATE.json','a5aa8fac99eaddf410a89fa7a7b0a05bdd9c9e298473557b1dd01efe9ec43efc'),
 (old/'EVALUATION_BOUNDARY_AUXILIARY.json','ddf5a17d75f9693ec2a998f477a0e4e496929a971c668afb7009fd79aef1da52'),
 (working/'121_W_BASELINE_V01/SHA256SUMS','546c4bc1bdd5db3072a108b66aacc5b48ea52ef36461758ca6339ca7b4969642'),
 (working/'121_W_ABC_EVALUATION_V01/SHA256SUMS','61c03ea7712ec85c171567fafa2ca513700d222d89ca9548261f9cf0eddb579e'),
 (working/'CW01_MVL01_FIRST_IGNITION_CLOSEOUT_R01_V01/FIRST_IGNITION_CLOSEOUT_REPORT.md','2b893b170bd2a2a4b13f45bf82b1a929d7481e9f5d657a7ebfecb17e1525dd36'),
 (working/'CW01_MVL01_FIRST_IGNITION_CLOSEOUT_R01_V01/SHA256SUMS','2d0f11da7a99302c32cced5f35e753e885b30db1cb75bd1e9a57fb27d92434b8')]
 for file,h0 in known:assert sha(file)==h0,file.name
 manifests=[]
 for root,name in [(old,'SHA256SUMS'),(b,'output/SHA256SUMS'),(c,'output/SHA256SUMS'),(working/'121_W_BASELINE_V01','SHA256SUMS'),(working/'121_W_ABC_EVALUATION_V01','SHA256SUMS')]:
  out=subprocess.run(['/usr/bin/shasum','-a','256','-c',name],cwd=root,text=True,capture_output=True,check=True)
  manifests.append([str(root),len(out.stdout.splitlines())])
 for label,root in [('B',b),('C',c)]:
  for rel,v in j(old/(label+'_FREEZE_ARTIFACTS.json'))['artifacts'].items():assert sha(root/rel)==v['sha256'],(label,rel)
 for file in (b/'IMPLEMENTATION_COMMON_PROMPT.md',c/'IMPLEMENTATION_COMMON_PROMPT.md'):
  assert sha(file)=='e22dd54c0a9047c5d5e72f282d98bcc75ba8f28dfa9d854c672ebbd4899402c0'
 assert not any(pathlib.Path(str(app/'assets_v1_5.sqlite')+s).exists() for s in ('-wal','-shm','-journal'))
 for p0 in (D/'EVALUATION_COHORT_PRIVATE.json',D/'EVALUATION_BOUNDARY_AUXILIARY.json'):
  assert sha(p0)==sha(old/p0.name)
 for orig,copy in ((known[0][0],P/'code/A.py'),(known[3][0],P/'tests/B/src/search_b.py'),(known[4][0],P/'tests/C/src/asset_search_fts.py')):
  assert sha(orig)==sha(copy)
 save('private/postverify.json',dict(environment=dict(host=socket.gethostname(),os=platform.mac_ver()[0],arch=platform.machine(),python=platform.python_version(),sqlite=sqlite3.sqlite_version),originals={str(x):h for x,h in known},manifests=manifests,b_and_c_complete_frozen_artifacts='36+52 PASS',operating_original_sidecars=0,time=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat()))
def build():
 rr=j(D/'functional.json')+j(D/'functional_addendum.json')
 li=j(D/'lifecycle.json')
 g=j(D/'performance_aggregate.json')
 ix=j(D/'index_aggregate.json')
 acc=j(D/'accuracy_summary.json')
 pq={(x['scale'],x['layer'],x['mode'],x['engine'],x['bucket'],x['id']):x for x in g}
 ii={(x['scale'],x['scenario'],x['engine']):x for x in ix}
 def pr(n,layer,mode,k,bucket='all',name='all',key='latency_ms',metric='p95'):
  x=pq.get((str(n),layer,mode,k,bucket,name))
  return x['metrics'][key][metric] if x else None
 def i(n,scenario,k,key='total_ms',metric='p95'):
  return ii[(str(n),scenario,k)]['metrics'][key][metric]
 def diff(x,a):
  return 100*(x/a-1) if x is not None and a else None
 cov=['# 후보 커버리지','','| 계층 | B 활성 / 누락 | C 활성 / 누락 |','|---|---:|---:|']
 for layer in dict.fromkeys(x['layer'] for x in rr):
  cells=[]
  for k in 'BC':
   subset=[x for x in rr if x['layer']==layer and x['engine']==k]
   active=[x for x in subset if x['accelerated']]
   cells.append(f"{len(active)}/{len(subset)} · {sum(x['missed'] or 0 for x in active)}")
  cov.append(f'| {layer} | '+ ' | '.join(cells)+' |')
 failures=[{k:x.get(k) for k in ('layer','id','engine','equal','diff','missed','reason')} for x in rr if not x['equal'] or x['missed']]
 cov+=['','별칭을 포함한 A 네 열 LIKE에서 rowid를 독립 추출했다. 가속 활성에서 B audit와 C debug 후보를 집합으로 비교했다. 폴백 질의는 별도로 전체 객체를 대조했다. edge는 NUL 본문 행 포함, edge_clean은 그 행 제거, edge_nul_fields는 NUL 경로와 별도 제목을 가진 한 행이다. operating_p2는 페이지 2·크기 1의 추가 진단이다.','', '불일치 증거: '+(json.dumps(failures,ensure_ascii=False) if failures else '0건.')]
 put('CANDIDATE_COVERAGE_REPORT.md','\n'.join(cov))
 perf=['# A/B/C 공통 성능','', '단위 ms, nearest-rank p95. 모든 혼합 행은 각 엔진 1,500회(50질의×30), ABC/ACB/BAC/BCA/CAB/CBA 회전. 가속 계측의 주 비교는 동일 연결 조건 안에서 수행했다.','',
 '| 배수 | 연결 | 혼합 p95 A / B / C | 선택적 3자 이상 p95 A / B / C | B/C 혼합 변화 | B/C 선택적 변화 |','|---|---|---:|---:|---:|---:|']
 decisions={}
 for n in (1,5,10):
  for mode in ('reuse','fresh'):
   x=[pr(n,'mixed',mode,k) for k in 'ABC']; y=[pr(n,'mixed',mode,k,'gate','selective_3plus') for k in 'ABC']
   d=[diff(v,x[0]) for v in x[1:]]; e=[diff(v,y[0]) for v in y[1:]]
   perf.append(f"| {n}x | {mode} | {' / '.join(map(fmt,x))} | {' / '.join(map(fmt,y))} | {' / '.join(map(pct,d))} | {' / '.join(map(pct,e))} |")
   for k,mi,se in zip('BC',d,e):decisions[(n,mode,k)]=(mi<=-20,se<=-30)
 perf+=['','### 최초 세대·새 프로세스·A 원형','',
 '| 배수 | 최초 세대 p95 A/B/C | 검증만 p95 B/C | 첫 프로세스 전체 p95 A/B/C | A 원형 새 연결 혼합 p95 |','|---|---:|---:|---:|---:|']
 for n in (1,5,10):
  values=[' / '.join(fmt(pr(n,'first_diagnostic','first_generation',k)) for k in 'ABC'),' / '.join(fmt(pr(n,'first_diagnostic','first_generation',k,key='verify_ms')) for k in 'BC'),' / '.join(fmt(pr(n,'first_diagnostic','first_process',k,key='outer_ms')) for k in 'ABC'),fmt(pr(n,'native_A_diagnostic','fresh_native_A','A'))]
  perf.append(f"| {n}x | "+' | '.join(values)+' |')
 perf+=['','최초 세대 및 첫 프로세스는 선택적 고정 1질의 × 엔진별·배수별 30회. 새 프로세스 전체에는 Python·공통 평가 모듈 초기화가 포함된다. 전체 50질의의 새 프로세스 기동 분포는 NOT_TESTED. 각 새 연결의 검증은 혼합 fresh에 포함된다.','',
 '### 보조 p95 · 1배 고정 입력','',
 '| 보조 유형 | 연결 | A / B / C p95 | B/C 대비 |','|---|---|---:|---:|']
 auxg={}
 for q in aux['cases']:
  key=q['id']
  for mode in ('reuse','fresh'):
   x=[pr(1,'aux',mode,k,'query',key) for k in 'ABC']
   if x[0] is None:continue
   d=[diff(v,x[0]) for v in x[1:]]
   auxg[(key,mode)]={k:val<=10 for k,val in zip('BC',d)}
   perf.append(f"| {key} | {mode} | {' / '.join(map(fmt,x))} | {' / '.join(map(pct,d))} |")
 err=sum(x['errors'] for x in g if x['bucket']=='all')
 perf+=['',f'실패/타임아웃 분류 합계 {err}건. 보조 각 셀 30회, 독립 혼합 통계에서 제외. MATCH 주입 fresh 및 5/10배 보조 계층은 NOT_TESTED. 각 보조 유형당 하나의 고정 문자열이므로 일반화 범위가 제한된다.','',
 'ABC_BENCHMARK_RAW.csv에 개별 외부 시간·직렬화·연결·검증·조회·후처리·후보수·폴백을 기록했다. B 후보·재검사 SQL 및 manual이 sqlite_ms로 합쳐져 있어 구성별 개별값은 미산출. C 후보와 docs 재검사/조회 및 manual은 별도 컬럼이다. A의 후보 단계는 해당 없음. private/benchmark_grouped.csv에 질의·유형별 mean/p50/p95/max와 호출·오류·가속·폴백을 포함한다. HTTP end-to-end와 실제 운영 트래픽 성능은 NOT_TESTED.']
 put('ABC_PERFORMANCE_SUMMARY.md','\n'.join(perf))
 idx=['# 합성 색인·공간 시험','',
 '같은 SQL로 같은 시작 상태에서 1/5/10배를 복제하고 검색 색인을 생성·갱신했다. 각 배수 및 엔진의 전체 생성 6회, 한 건·배치 25건·무변경·삭제·이름 변경 각 30회. B/C 쓰기 경로는 공통 평가자 loader이고 조회 활성화 시 각 동결 구현의 세대 검증을 더했다. C의 검증을 유발한 조회 전체도 원시에 별도 기록했다. 운영 refresh와 실제 파일 스캔·배포는 NOT_TESTED.','',
 '| 배수 | 시나리오 | A/B/C 전체 p95 ms | B/C 증가율 | B/C 검증 p95 ms | A/B/C DB bytes (최대 관측) |','|---|---|---:|---:|---:|---:|']
 for n in (1,5,10):
  for case in ('full','one','batch','unchanged','delete','rename'):
   x=[i(n,case,k) for k in 'ABC']
   y=[i(n,case,k,'candidate_verify_ms') for k in 'BC']
   sizes=[int(i(n,case,k,'db_bytes','max')) for k in 'ABC']
   idx.append(f"| {n}x | {case} | {' / '.join(map(fmt,x))} | {' / '.join(pct(diff(v,x[0])) for v in x[1:])} | {' / '.join(map(fmt,y))} | {' / '.join(f'{v:,}' for v in sizes)} |")
 idx+=['','### B 세대 검증 구성 · 전체 생성 뒤 p95','', '| 배수 | 메모리 백업 | FTS 내부 검사 | docs/ft 교차검사 및 나머지 | C 전수 검증 |','|---|---:|---:|---:|---:|']
 for n in (1,5,10):
  idx.append(f"| {n}x | {fmt(i(n,'full','B','b_memory_backup_ms'))} | {fmt(i(n,'full','B','b_native_fts_ms'))} | {fmt(i(n,'full','B','b_crosscheck_and_other_ms'))} | {fmt(i(n,'full','C','candidate_verify_ms'))} |")
 idx+=['','전체 시간은 원본 합성 행 조회·SQLite 복제·SQL 쓰기·FTS 갱신·커밋·검증·파일 교체를 포함한다. 구간별 p95의 합은 전체 p95와 일반적으로 다르다. private/index_raw.csv와 private/index_aggregate.json에 각 구간, FTS shadow·별도 인덱스, 커밋 전 sidecar 최대 관측값을 기록했다. 시스템 전체의 실제 임시 저장공간 최고치는 NOT_TESTED. 첫 프로세스 RSS는 별도 메모리 진단이며 저장 공간에 합산하지 않았다.']
 put('INDEX_REFRESH_AND_STORAGE_REPORT.md','\n'.join(idx))
 issues=['# 제약과 후속 통합 위험','',
 '- B의 Step 4-B 작업 DB 21개 위치 규약 FAIL은 기존 기록대로 유지. Step 4-C 변경·시험 DB는 새 tests 폴더에서 작업했다.',
 '- B가 검증한 스냅샷을 재사용할 때 커밋 뒤 새 요청의 가시성은 수명주기 관리가 필요하다. C는 세대 변경 때 검증 재수행 및 재연결이 필요하다.',
 '- C 기존 개발에서 오류 직후 last_metrics 잔류가 확인됐다. 공식 평가의 오류는 외부 타이머로 분류하고 해당 내부값을 재사용하지 않았다.',
 '- A 어댑터는 행 수집을 계측하므로 A 원형 새 연결과 별도다. 첫 프로세스, 새 연결 반복, 검증 후 재사용을 다른 성능 조건으로 해석했다.',
 '- 공개/보류의 초성 10개 기대 미충족은 현행 A와 공통이며 이번 성능 후보의 신규 회귀가 아니다.',
 '- 실운영 HTTP 동시성, 재사용 연결의 운영 통합, 운영 문서 전체 refresh 및 실제 배포·복구는 NOT_TESTED.',
 '- 보조 검색은 1배 고정 소표본. 5/10배에서 부족한 보조 셀은 PASS로 간주하지 않는다.']
 if failures:issues+=['','추가 기능 불일치: '+json.dumps(failures,ensure_ascii=False)]
 put('BC_KNOWN_ISSUES_AND_LIMITATIONS.md','\n'.join(issues))
 gate={k:not any(x['engine']==k for x in failures) and all(r['equal'] and r['safe'] and not r['missed'] for r in li if r['engine']==k) for k in 'BC'}
 lines=['# A/B/C 최종 판정표','',
 '| 후보 | 기능 | 성능 | 운영 채택 판단 |','|---|---|---|---|',
 '| A | 기준선 및 회귀 대조 PASS | 비교 기준 | 현행 유지 권고 |']
 for k in 'BC':
  lines.append(f"| {k} | {'PASS' if gate[k] else 'FAIL'} | 기준 미달 | {'보류' if gate[k] else '부적합'} |")
 lines+=['','| 규모 | 연결 | B 혼합/선택적 | C 혼합/선택적 |','|---|---|---|---|']
 yn=lambda x:'PASS' if x else '기준 미달'
 for n in (1,5,10):
  for mode in ('reuse','fresh'):
   lines.append(f"| {n}x | {mode} | {' / '.join(map(yn,decisions[n,mode,'B']))} | {' / '.join(map(yn,decisions[n,mode,'C']))} |")
 lines+=['','| 1배 보조 유형 | 연결 | B (악화 10% 이내) | C (악화 10% 이내) |','|---|---|---|---|']
 for (case,mode),x in auxg.items():lines.append(f'| {case} | {mode} | {yn(x["B"])} | {yn(x["C"])} |')
 lines+=['','| 배수 | 색인 전체 생성 +10% 이내 B/C | 증분 각 +10% 이내 B/C | 저장 +5% 이내 B/C |','|---|---|---|---|']
 for n in (1,5,10):
  tests=lambda key:' / '.join(yn(key(k)) for k in 'BC')
  full=tests(lambda k:diff(i(n,'full',k),i(n,'full','A'))<=10)
  inc=tests(lambda k:all(diff(i(n,s,k),i(n,s,'A'))<=10 for s in ('one','batch','unchanged','delete','rename')))
  storage=tests(lambda k:all(diff(i(n,s,k,'db_bytes','max'),i(n,s,'A','db_bytes','max'))<=5 for s in ('full','one','batch','unchanged','delete','rename')))
  lines.append(f'| {n}x | {full} | {inc} | {storage} |')
 lines+=['','판단 근거는 운영과 유사한 새 연결의 검증비용과 보조 질의, 색인 수명주기다. 재사용 연결의 선택적 검색 편익은 격리 계측에서 관측됐다. 채택 판단은 121 Chat에 남긴다. 후속 D 연구를 택할 경우 세대 검증을 갱신 시점으로 옮기고 짧은·다건에서 A 경로로 분기하는 별도 판본 및 통합 시험을 검토할 수 있다.']
 put('ABC_FINAL_SCORECARD.md','\n'.join(lines))
 save('private/adoption_summary.json',dict(gates=gate,performance={f'{n}/{m}/{k}':v for (n,m,k),v in decisions.items()},errors=err,failures=failures))
 print('REPORTS',gate,'error',err,flush=True)
def final():
 h=sha(P/'ABC_FINAL_SCORECARD.md')
 s=j(D/'adoption_summary.json')
 body=f"""# Step 4-C 최종 보고 및 121 Chat 인계

MacStudioui-MacStudio.local (c377300b-a710-43a6-8169-f17e87175403)에서 Step 4-C 격리 평가를 완료했다. 운영 v1.5 소스/DB와 B/C 88개 동결 산출물의 바이트를 사후 검증했다. 결과 경로 \`{DROOT}\`.

기본 운영 9건과 1/5/10배 공개 30·보류 20의 전체 객체 일치 및 정확도 비악화를 확인했다. 추가 경계 결과를 포함한 기능 판정 B {'PASS' if s['gates']['B'] else 'FAIL'}, C {'PASS' if s['gates']['C'] else 'FAIL'}. 격리 세대 갱신·삭제·이름 변경·폴백·복구 35개 검사 PASS. 공식 성능 판정 B/C 기준 미달. 새 연결 검증과 재사용 반복의 결과를 분리했다. 해당 조건의 세부 수치는 ABC_PERFORMANCE_SUMMARY.md, 색인과 저장은 INDEX_REFRESH_AND_STORAGE_REPORT.md에 있다. 최종 권고는 A 유지다.

## 121 Chat 복사본

\`\`\`text
121 Chat / Step 4-C 공식 평가 종료 검토

장치 MacStudioui-MacStudio.local · c377300b-a710-43a6-8169-f17e87175403. 운영 A v1.5 및 동결 B/C의 Step 4-C 격리 평가를 완료했습니다. 운영 9건, 공개 30건과 보류 20건의 기본 반환 객체가 A와 일치했고 합성 정확도 Recall/Precision/MRR/nDCG@10은 각각 0.800/0.160/0.800/0.800입니다. 추가 경계 포함 기능 게이트 B {'PASS' if s['gates']['B'] else 'FAIL'}, C {'PASS' if s['gates']['C'] else 'FAIL'}입니다. 기능·성능은 ABC_FINAL_SCORECARD.md에서 구분했습니다.

증거 {DROOT}
ABC_FINAL_SCORECARD.md SHA-256 {h}
ABC_PERFORMANCE_SUMMARY.md, ABC_BENCHMARK_RAW.csv, INDEX_REFRESH_AND_STORAGE_REPORT.md, SHA256SUMS를 확인해 주세요.

현재 권고는 A 유지입니다. B/C의 재사용 연결 가속과 새 연결 검증비용을 분리해 비교했습니다. 보조 검색은 1배 별도, 1/5/10배 기본 혼합은 동결된 동일 가중치로 시험했습니다. 운영 HTTP·동시 접속·배포/복구는 별도 검증입니다.
결정 요청은 A 유지로 종료할지, 세대 검증 위치와 다건/폴백 정책을 별도 D 연구로 승인할지입니다. 운영 서비스 변경과 배포는 별도 승인 후에만 검토합니다.
\`\`\`
"""
 put('STEP4C_FINAL_REPORT.md',body)
 paths=sorted(f for f in P.rglob('*') if f.is_file() and f.name!='SHA256SUMS' and not f.is_symlink())
 checksum=P/'SHA256SUMS'
 with checksum.open('x',encoding='utf-8') as f:
  for x in paths:f.write(f'{sha(x)}  {x.relative_to(P)}\n')
 out=subprocess.run(['/usr/bin/shasum','-a','256','-c','SHA256SUMS'],cwd=P,text=True,capture_output=True,check=True)
 assert len(out.stdout.splitlines())==len(paths)
 for x in (*paths,checksum):x.chmod(0o400)
 print('SEALED',len(paths),sha(checksum),sha(P/'STEP4C_FINAL_REPORT.md'),h,flush=True)
if __name__=='__main__':
 protection();build();final()
