#!/usr/bin/env python3
"""v0.3 original ChatGPT project-ID evidence from the official 2026-11-05 export.
Non-destructive. No network or account mutation. Read-only extraction of metadata.
"""
from pathlib import Path
from html import escape
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from collections import Counter,defaultdict
import os,json,re,hashlib

BASE=Path('/Users/yongho/ROUTABL-ChatGPT-Archive/2026-11-05')
RAW=BASE/'00_EXTRACTED_ORIGINAL'
V01=BASE/'10_GUI_VIEWER'
V02=BASE/'11_GUI_PROJECTS_V02'
V03=BASE/'12_GUI_PROJECT_IDS_V03'
AUDIT=BASE/'20_AUDIT'
PROJECT_LABELS={
 'g-p-6a92532988c881918be08fc0ad4dbaed':('Routabl 개발','PAST_URL_USER_CONFIRMED','2026년 10월 실제 ChatGPT 프로젝트 URL과 사용자가 확인한 이름','라우터블 앱·백서'),
 'g-p-6ae28c1c9e5c8191b2b3d1ecf8a8579d':('프로젝트명 확인 필요 · AI 활용 관련','NAME_UNVERIFIED','ID와 채팅 소속은 공식 내보내기로 확인, 실제 이름 미확인','ChatGPT 계정·도구'),
 'g-p-6ae156e9fcac81918d9d88bc57ad81da':('프로젝트명 확인 필요 · 기기 관련','NAME_UNVERIFIED','ID와 채팅 소속은 공식 내보내기로 확인, 실제 이름 미확인','Mac·전자기기'),
 'g-p-6ac994a5b5b48191a643f0558d251acf':('출발점검 — 화물차 일상점검 앱','PAST_URL_USER_CONFIRMED','과거 일상점검앱 기획 PDF에 프로젝트 URL·이름 명시, 현재 명칭 미확인','일상점검표'),
 'g-p-6abb243732048191ba34a2e501316b17':('프로젝트명 확인 필요 · 경제 자료 관련','NAME_UNVERIFIED','ID와 채팅 소속은 공식 내보내기로 확인, 실제 이름 미확인','경제·자료 분석'),
 'g-p-6ae70be07c148191a37dbda329f33d98':('프로젝트명 확인 필요 · Mac/NAS 관련','NAME_UNVERIFIED','ID와 채팅 소속은 공식 내보내기로 확인, 실제 이름 미확인','Mac·NAS 작업'),
 'g-p-6ae349929a9c819189a9d6faff4b8454':('프로젝트명 확인 필요 · 디지털 자산 관련','NAME_UNVERIFIED','ID와 채팅 소속은 공식 내보내기로 확인, 실제 이름 미확인','디지털 자산관리')
}
NO_ID='NO_PROJECT_ID_IN_EXPORT'

def shasum(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def h(x):return escape(str(x or ''),quote=True)
def main():
 os.umask(0o077)
 assert V02.is_dir() and not V03.exists(), 'REFUSE_OVERWRITE_V03'
 conv=[]
 for f in sorted(RAW.glob('conversations-*.json')):
  a=json.loads(f.read_text('utf8'));assert isinstance(a,list)
  conv+=a
 assert len(conv)==327
 ids={x['conversation_id']:x for x in conv}
 assert len(ids)==327
 old=json.loads((V02/'classification.json').read_text('utf8'))['conversations']
 assert len(old)==327
 group_counts=Counter();cross=defaultdict(Counter);listed={}
 for c in conv:
  cid=c['conversation_id'];pid=c.get('conversation_template_id') or NO_ID
  if pid!=NO_ID: assert pid in PROJECT_LABELS and re.fullmatch('g-p-[a-f0-9]{32}',pid)
  group_counts[pid]+=1
  v02=old[cid]
  cross[pid][v02['group']]+=1
  listed[cid]={
   'id':cid,'title':c.get('title') or '(제목 없음)',
   'project_id':c.get('conversation_template_id'), # original export value verbatim, null kept
   'project_relation_basis':'OFFICIAL_EXPORT_CONVERSATION_TEMPLATE_ID' if pid!=NO_ID else 'ABSENT_IN_OFFICIAL_EXPORT',
   'export_archived':bool(c.get('is_archived')),
   'v02_inferred_group':v02['group'],
   'v02_inference_evidence':v02['evidence']
  }
 assert len(group_counts)==8 and group_counts[NO_ID]==163
 assert sum(v for k,v in group_counts.items() if k!=NO_ID)==164
 V03.mkdir(mode=0o700)
 (V03/'chats').mkdir(mode=0o700)
 os.symlink('../10_GUI_VIEWER/assets',V03/'assets')
 for file in ['style.css','search-data.js','project-style.css']:
  src=(V01 if file!='project-style.css' else V02)/file
  os.link(src,V03/file)
 projects=[]
 for idx,(key,total) in enumerate(sorted([(k,n) for k,n in group_counts.items() if k!=NO_ID],key=lambda p:-p[1]),1):
  label,status,evidence,topic=PROJECT_LABELS[key]
  projects.append({'project_id':key,'display_name':label,'name_status':status,
   'name_evidence':evidence,'topic_hint':topic,'count':total,
   'label_number':idx,'direct_id_from_export':True,
   'status_note':'실제 계정의 현재 표시명은 실시간 검증 전'})
 projects.append({'project_id':NO_ID,'display_name':'프로젝트 ID 없음','name_status':'NO_ID','name_evidence':'공식 JSON conversation_template_id가 null','topic_hint':'원본에서 소속 관계 확인 불가',
  'count':group_counts[NO_ID],'label_number':8,'direct_id_from_export':False,
  'status_note':'ID 없음은 현재 미소속이라는 증명은 아님'})
 ledger={'schema':'routabl-official-project-link-reconciliation-v0.3','source_snapshot':'2026-11-05',
  'data_source':'OFFICIAL_ZIP_CONVERSATIONS_JSON_CONVERSATION_TEMPLATE_ID',
  'current_account_live_verified':False,
  'current_project_names_unavailable_reason':'BROWSER_CONNECTED_EXTENSION_CONTEXT_UNAVAILABLE; REMOTE_MAC_STUDIO_SAFARI_NO_CHATGPT_TAB',
  'total_chats':len(conv),'linked_chats':164,'no_project_id':163,
  'known_historical_project_names':2,'other_project_names_pending':5,
  'projects':projects,'conversations':listed,
  'previous_v02_counts':dict(Counter(v['group'] for v in old.values())),
  'cross_tab_project_id_vs_v02_topic':{k:dict(v) for k,v in cross.items()},
  'generated_kst':datetime.now(ZoneInfo('Asia/Seoul')).isoformat(timespec='seconds')}
 (V03/'project-id-ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 view={'projects':projects,'conversations':listed}
 (V03/'project-id-data.js').write_text('window.ROUTABL_PROJECT_ID_DATA='+json.dumps(view,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf8')
 # New detail pages preserve v01 user/assistant messages and image links, only add project ID banner.
 rawpages={p.name:p for p in (V01/'chats').glob('*.html')}
 assert len(rawpages)==327
 # search-index file names are stable and derived from unique exported conversation IDs
 names={x.stem.split('-',1)[-1]:x.name for x in rawpages.values()}
 for cid,entry in listed.items():
  filename=next((name for name in rawpages if cid in name),None)
  assert filename is not None
  source=rawpages[filename].read_text('utf8')
  pid=entry['project_id'];group=pid or NO_ID
  project=next(x for x in projects if x['project_id']==group)
  state='보관됨' if entry['export_archived'] else '일반'
  shortid=h(pid) if pid else '(원본에 없음)'
  direct='공식 데이터의 프로젝트 ID 확인' if pid else '공식 데이터에 프로젝트 ID 없음'
  caution='실제 프로젝트명은 과거 URL로 확인 · 현재 표시명 재확인 필요' if project['name_status']=='PAST_URL_USER_CONFIRMED' else '프로젝트 이름은 실제 계정에서 미확인'
  if not pid:caution='이 채팅은 프로젝트를 추정하지 않습니다. 실제 소속은 별도 확인 필요'
  banner='<div class="project-classification"><span class="class-label">v0.3 · '+h(direct)+'</span><span class="class-caution">'+h(caution)+'</span><div class="class-explanation">프로젝트: '+h(project['display_name'])+' · ID: '+shortid+' · 내보내기 당시 '+state+'</div><div class="class-explanation">이전 v0.2 제목 추정: '+h(entry['v02_inferred_group'])+' (참고용, 원래 소속 증거 아님)</div></div>'
  assert source.count('<header class="chat-header">')==1
  source=source.replace('<header class="chat-header">',banner+'<header class="chat-header">',1)
  source=source.replace('</head>','<link rel="stylesheet" href="../project-style.css"><link rel="stylesheet" href="../v03-style.css"></head>',1)
  (V03/'chats'/filename).write_text(source,encoding='utf8')
 assert len(list((V03/'chats').glob('*.html')))==327
 report={
  'status':'PROJECT_ID_RELATIONS_RECOVERED_FROM_OFFICIAL_EXPORT',
  'snapshot':'2026-11-05',
  'total':327,'project_id_present':164,'project_id_null':163,'distinct_project_ids':7,
  'counts':dict(group_counts),'historical_names_verified_by_url':2,
  'names_waiting_for_live_verification':5,
  'first_party_browser_access':'NOT_AVAILABLE_IN_CHAT_CONTEXT',
  'old_v02_unchanged':True,'old_v01_unchanged':True,'original_zip_unchanged':True,
  'comparison_cross_tab':{k:dict(v) for k,v in cross.items()},
  'ledger_sha256':shasum(V03/'project-id-ledger.json'),
  'project_id_js_sha256':shasum(V03/'project-id-data.js'),
  'v03_path':str(V03),'generated_kst':ledger['generated_kst']}
 (AUDIT/'v03_project_id_from_official_export_20261106.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print('V03_PROJECT_ID_LEDGER_PREPARED',json.dumps(report,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
