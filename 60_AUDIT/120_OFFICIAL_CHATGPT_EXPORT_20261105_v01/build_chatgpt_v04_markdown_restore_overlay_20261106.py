#!/usr/bin/env python3
"""v0.4 private Safari archive, source snapshot + user-attested 21 restorations.
Do NOT mutate the official 2026-11-05 export, or v0.1/0.2/0.3 viewers.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib,json,os,re,shutil,copy

ROOT=Path('/Users/yongho/ROUTABL-ChatGPT-Archive/2026-11-05')
SRC=ROOT/'00_EXTRACTED_ORIGINAL'
V01=ROOT/'10_GUI_VIEWER'
V03=ROOT/'12_GUI_PROJECT_IDS_V03'
V04=ROOT/'13_GUI_MARKDOWN_V04'
AUDIT=ROOT/'20_AUDIT'
RID='g-p-6a92532988c881918be08fc0ad4dbaed'
UTC_DATE='2026-11-06'
EXTRA_TITLES=('고객 주소록 등록','Firebase 요금 변경 알림')

def replace_once(s,old,new):
 count=s.count(old)
 if count!=1:raise ValueError('EXPECTED_ONE_REPLACEMENT '+str(count)+' '+old[:70])
 return s.replace(old,new,1)
def checksum(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,data):
 with p.open('x',encoding='utf8') as f:f.write(data)
def main():
 os.umask(0o077)
 assert SRC.is_dir() and V03.is_dir() and not V04.exists(),'REFUSE_MISSING_INPUT_OR_OVERWRITE_V04'
 chats=[]
 for f in sorted(SRC.glob('conversations-*.json')):
  chats+=json.loads(f.read_text('utf8'))
 assert len(chats)==327
 byid={c['conversation_id']:c for c in chats}
 assert len(byid)==327
 restorations=[c for c in chats if c.get('conversation_template_id')==RID and c.get('is_archived') is True]
 assert len(restorations)==19
 added=[]
 for title in EXTRA_TITLES:
  hits=[c for c in chats if c.get('title')==title]
  assert len(hits)==1
  c=hits[0]
  assert c.get('conversation_template_id') is None and c.get('is_archived') is True
  added.append(c)
 assert len(added)==2
 ids={c['conversation_id'] for c in restorations+added}
 assert len(ids)==21
 oldledger=json.loads((V03/'project-id-ledger.json').read_text('utf8'))
 assert len(oldledger['conversations'])==327
 V04.mkdir(mode=0o700)
 (V04/'chats').mkdir(mode=0o700)
 os.symlink('../10_GUI_VIEWER/assets',V04/'assets')
 for fn in ['style.css','project-style.css','search-data.js']:
  src=(V01 if fn!='project-style.css' else V03)/fn
  os.link(src,V04/fn)
 for p in (V03/'chats').glob('*.html'):
  content=p.read_text('utf8')
  cid=next((c for c in ids if c in p.name),None)
  if cid is not None:
   origin=byid[cid]
   kind='원래 라우터블 프로젝트 ID 유지' if origin.get('conversation_template_id')==RID else '원본 ID 없음 · 사용자 라우터블 프로젝트 이동 확인'
   badge='<div class="restore-note"><strong>2026-11-06 사용자 복원 확인</strong> · '+kind+'<div>공식 2026-11-05 내보내기에서는 보관됨으로 기록되어 있습니다. 현재 상태는 사용자가 ChatGPT에서 직접 옮겼다고 알려준 확인 기록이며, 원본의 날짜·소속 필드를 변경하지 않았습니다.</div></div>'
   content=replace_once(content,'<header class="chat-header">',badge+'<header class="chat-header">')
  content=replace_once(content,'</head>','<link rel="stylesheet" href="../v04-style.css"></head>')
  write(V04/'chats'/p.name,content)
 assert len(list((V04/'chats').glob('*.html')))==327
 ledger=copy.deepcopy(oldledger)
 ledger['schema']='routabl-v04-export-and-user-confirmed-restoration'
 ledger['based_on_snapshot']='2026-11-05'
 ledger['user_report_date_kst']='2026-11-06'
 ledger['project_membership_overlay_origin']='USER_ATTESTED_IN_CHAT_NOT_LIVE_BROWSER_VERIFIED'
 ledger['unchanged_export_original_project_id_count']=164
 ledger['unchanged_export_original_no_project_id_count']=163
 ledger['user_reported_restored_19_with_original_routabl_id']=19
 ledger['user_reported_moved_2_without_original_project_id']=2
 ledger['effective_routabl_count']=121
 ledger['source_routabl_count']=119
 ledger['effective_unlinked_count']=161
 ledger['source_unlinked_count']=163
 ledger['user_confirmation_records']=[]
 for c in sorted(restorations+added,key=lambda v:v.get('create_time') or 0):
  cid=c['conversation_id'];record=ledger['conversations'][cid]
  record['v04_user_reported_restored_to_routabl']=True
  record['v04_user_reported_date_kst']=UTC_DATE
  record['v04_user_report_source']='user statement in current ChatGPT chat; not live platform inspection'
  if c.get('conversation_template_id') is None:
   record['v04_effective_project_id_for_gui']=RID
   record['v04_assignment_class']='USER_CONFIRMED_MOVED_PROJECT_SOURCE_ID_NULL'
  else:
   record['v04_effective_project_id_for_gui']=RID
   record['v04_assignment_class']='SOURCE_PROJECT_ID_AND_USER_CONFIRMED_UNARCHIVED'
  ledger['user_confirmation_records'].append({
   'conversation_id':cid,'title':c['title'],'source_project_id':c.get('conversation_template_id'),
   'source_is_archived_on_2026_11_05':True,'user_reported_project_id':RID,
   'user_reported_unarchived':True,
   'evidence_class':record['v04_assignment_class'],
   'statement_date_kst':UTC_DATE
  })
 write(V04/'restoration-ledger.json',json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
 data=json.loads((V03/'project-id-data.js').read_text('utf8').removeprefix('window.ROUTABL_PROJECT_ID_DATA=').rstrip(';\n'))
 assert len(data['projects'])==8 and len(data['conversations'])==327
 for project in data['projects']:
  if project['project_id']==RID:
   assert project['count']==119
   project['source_export_count']=119
   project['count']=121
   project['v04_user_reported_added_count']=2
   project['v04_user_confirmed_restored_count']=21
   project['status_note']='원본 프로젝트 ID 119건 + 사용자 라우터블 이동 확인 2건; 현재 계정 실시간 조회 미실시'
  elif project['project_id']=='NO_PROJECT_ID_IN_EXPORT':
   assert project['count']==163
   project['source_export_count']=163
   project['count']=161
   project['v04_moved_by_user_count']=2
 for record in ledger['user_confirmation_records']:
  x=data['conversations'][record['conversation_id']]
  x['v04_user_confirmed_restored']=True
  x['v04_user_reported_date_kst']=UTC_DATE
  x['v04_confirmation_class']=record['evidence_class']
  if record['source_project_id'] is None:
   assert x['project_id'] is None
   x['effective_project_id']=RID
 assert sum(p['count'] for p in data['projects'])==327
 assert sum(1 for x in data['conversations'].values() if x.get('v04_user_confirmed_restored'))==21
 write(V04/'project-id-data.js','window.ROUTABL_PROJECT_ID_DATA='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n')
 # Save v0.3 JS unchanged to separately versioned working file, then apply narrow UI-layer patches.
 s=(V03/'app.js').read_text('utf8')
 s=replace_once(s,'function projOf(c){return c.project_id||UNLINKED;}',
     'function projOf(c){return c.effective_project_id||c.project_id||UNLINKED;}')
 s=replace_once(s,'const titleOnly=el("titleOnly"),count=el("resultCount"),title=el("selectedTitle"),subtitle=el("selectedDescription");',
     'const titleOnly=el("titleOnly"),count=el("resultCount"),title=el("selectedTitle"),subtitle=el("selectedDescription");const restored=el("restoreFilter");')
 s=replace_once(s,'if(archived.value==="archived"&&!record.export_archived)return false;',
     'if(archived.value==="archived"&&!record.export_archived)return false;\n     if(restored.value==="confirmed"&&!record.v04_user_confirmed_restored)return false;\n     if(restored.value==="other"&&record.v04_user_confirmed_restored)return false;')
 s=replace_once(s,'" · ID 확인"));',
     '" · ID 확인"));') if False else s
 s=replace_once(s,'pr.textContent=p.project_id==="ALL"?"327개 전체 대화":(evidenceStatus(p)+(p.project_id===UNLINKED?"":" · ID 확인"));',
     'pr.textContent=p.project_id==="ALL"?"327개 전체 대화":(p.project_id==="NO_PROJECT_ID_IN_EXPORT"?"2026-11-05 원본 163건 중 2건 사용자 이동 확인":(p.project_id==="'+RID+'"?"119건 원본 ID + 2건 사용자 확인":evidenceStatus(p)+" · ID 확인"));')
 s=replace_once(s,'status.className="project-indicator"+(key===UNLINKED?" missing":"");',
     'status.className="project-indicator"+(!c.project_id?" missing":"");')
 s=replace_once(s,'status.textContent=key===UNLINKED?"프로젝트 ID 없음":"공식 내보내기 ID 확인";',
     'status.textContent=c.project_id?"공식 내보내기 ID 확인":(c.effective_project_id?"사용자 확인 · 원본 프로젝트 ID 없음":"프로젝트 ID 없음");')
 s=replace_once(s,'labels.append(status,group);',
     'labels.append(status,group);\n     if(c.v04_user_confirmed_restored){const restoredBadge=document.createElement("span");restoredBadge.className="project-indicator user";restoredBadge.textContent="11/06 사용자 복원 확인";labels.append(restoredBadge);}')
 s=replace_once(s,'diff.textContent=key===UNLINKED?"원본 프로젝트 소속 불명 · v0.2 제목 추정: "+c.v02_inferred_group',
     'diff.textContent=!c.project_id?(c.effective_project_id?"11/05 원본에는 프로젝트 ID 없음 · 11/06 사용자 라우터블 이동 확인 · v0.2 분류: "+c.v02_inferred_group:"원본 프로젝트 소속 불명 · v0.2 제목 추정: "+c.v02_inferred_group)')
 s=replace_once(s,'for(const c of [order,archived,titleOnly])c.addEventListener("change",renderRows);',
     'for(const c of [order,archived,titleOnly,restored])c.addEventListener("change",renderRows);')
 s=replace_once(s,'(c.export_archived?"보관 상태":"일반 상태")', '(c.export_archived?"11/05 보관":"11/05 일반")') if '(c.export_archived?"보관 상태":"일반 상태")' in s else s
 s=replace_once(s,'c.export_archived?"보관 상태":"일반 상태"', 'c.export_archived?"11/05 보관":"11/05 일반"') if 'c.export_archived?"보관 상태":"일반 상태"' in s else s
 s=replace_once(s,'count.textContent="검색 결과 "+rows.length+"건 · 전체 327건 · 프로젝트 ID 확인 164건 · ID 없음 163건";',
     'count.textContent="검색 결과 "+rows.length+"건 · 전체 327건 · 원본 프로젝트 ID 164건 · 사용자 추가 분류 2건 · 복원 확인 21건";')
 write(V04/'app.js',s)
 index=(V03/'index.html').read_text('utf8')
 index=replace_once(index,'</head>','<link rel="stylesheet" href="v04-style.css"></head>')
 index=index.replace('v0.3','v0.4')
 index=replace_once(index,'실제 프로젝트 ID로 대화 정리','프로젝트 복원 · Markdown 서식 개선')
 index=replace_once(index,'<strong>164</strong><span>프로젝트 ID 확인</span>',
   '<strong>121</strong><span>라우터블 (원본 ID 119 + 사용자 확인 2)</span>')
 index=replace_once(index,'<strong>7</strong><span>확인된 프로젝트 ID</span>',
   '<strong>21</strong><span>사용자가 복원 확인한 채팅</span>')
 index=replace_once(index,'<div id="v03-layout">',
   '<div class="notice"><strong>2026년 11월 6일 복원 기록 반영:</strong> 원본에서 라우터블 ID가 있었던 보관 채팅 19건, 원본 ID는 없었으나 사용자가 라우터블 프로젝트로 옮긴 채팅 2건을 구분해 표시합니다. 원본의 11월 5일 보관 여부·프로젝트 ID는 변경하지 않았습니다.</div><div id="v03-layout">')
 index=replace_once(index,'<select class="select" id="order" aria-label="정렬">',
   '<select class="select" id="restoreFilter" aria-label="사용자 복원 확인 필터"><option value="all">11/06 복원 여부 전체</option><option value="confirmed">사용자 복원 확인 21건</option><option value="other">기타 채팅</option></select><select class="select" id="order" aria-label="정렬">')
 index=replace_once(index,'<a href="../11_GUI_PROJECTS_V02/index.html">이전 제목 추정 v0.2</a>',
   '<a href="../12_GUI_PROJECT_IDS_V03/index.html">이전 프로젝트 ID 화면 v0.3</a> · <a href="../11_GUI_PROJECTS_V02/index.html">이전 제목 추정 v0.2</a>')
 # Explicit dates/status, avoid claiming to have live account browser inspected.
 index=index.replace('<option value="all">보관 상태 전체</option>','<option value="all">11/5 원본 상태 전체</option>')
 index=index.replace('<option value="archived">보관 채팅만</option>','<option value="archived">11/5 당시 보관 162건</option>')
 index=index.replace('<option value="active">일반 채팅만</option>','<option value="active">11/5 당시 일반 165건</option>')
 index=index.replace('<div class="notice">**사용법:**','<div class="notice"><strong>사용법:</strong>')
 index=index.replace('프로젝트 <strong>소속 ID 164건은 2026-11-05 공식 ZIP에서 직접 확인</strong>',
  '프로젝트 <strong>원본 소속 ID 164건은 2026-11-05 공식 ZIP에서 직접 확인</strong>')
 index=index.replace('이름을 입력하고 「직접 확인」을 체크하세요.','이름을 입력하고 「직접 확인」을 체크하세요.')
 write(V04/'index.html',index)
 record={'v04_root':str(V04),'built_kst':datetime.now(ZoneInfo('Asia/Seoul')).isoformat(timespec='seconds'),
  'source_v03':str(V03),'original_export_snapshot':'2026-11-05',
  'original_zip_unchanged':True,'source_v03_unchanged':True,
  'routabl_source_project_id_count':119,'routabl_effective_gui_count':121,
  'reported_archive_restorations_count':19,'reported_project_moves_count':2,
  'report_provenance':'user statement 2026-11-06, not independently checked via account',
  'source_archived_flag_still_true_for_21':True,
  'new_files':['restoration-ledger.json','project-id-data.js','app.js','index.html'],
  'source_ledger_sha256':checksum(V03/'project-id-ledger.json'),
  'new_restoration_ledger_sha256':checksum(V04/'restoration-ledger.json')}
 write(AUDIT/'v04_restoration_overlay_preflight_20261106.json',json.dumps(record,ensure_ascii=False,indent=2)+'\n')
 print('V04_OVERLAY_CREATED',json.dumps(record,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
