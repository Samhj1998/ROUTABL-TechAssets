#!/usr/bin/env python3
"""Create independent project/topic classification v02 without modifying the Nov 5 export or v01 GUI."""
from pathlib import Path
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
from html import escape
from collections import Counter
import json,os,re,shutil,hashlib,unicodedata

BASE=Path('/Users/yongho/ROUTABL-ChatGPT-Archive/2026-11-05')
RAW=BASE/'00_EXTRACTED_ORIGINAL'
OLD=BASE/'10_GUI_VIEWER'
NEW=BASE/'11_GUI_PROJECTS_V02'
AUDIT=BASE/'20_AUDIT'
KST=ZoneInfo('Asia/Seoul')
GROUPS=[
 ('routabl','라우터블 개발','앱·Firebase·배차·백서 관련'),
 ('digital','디지털 자산관리','저장장치·NAS·백업·자산 관리'),
 ('chatgpt','ChatGPT 활용·계정 및 보안 관리','AI 도구·계정·사용량·보관 채팅'),
 ('checklist','일상점검앱','차량 일상점검 앱 개발'),
 ('digitopia','Digitopia','블로그·홈페이지·지식 콘텐츠'),
 ('devices','맥·기기 및 네트워크','컴퓨터·디바이스·네트워크 운영'),
 ('review','기타·분류 확인 필요','프로젝트 정보 미제공 또는 제목 근거 부족')
]
NAME=dict((k,v) for k,v,_ in GROUPS)
RULES=[
 ('checklist',r'일상점검(?:표|앱)|점검표_AndroidStudio','명시된 일상점검앱 명칭','높음'),
 ('routabl',r'라우터블|루터블|루티벨|DISPATCH\s*One|디스패치원|MyDeliveryApp|SmartDispatch|Routivel|Routabl','라우터블 또는 이전 앱 브랜드가 제목에 등장','높음'),
 ('digital',r'디지털\s*자산관리|기술자산\s*통합관리(?:체계)?','디지털 자산관리·기술자산 운영 명칭','높음'),
 ('digitopia',r'Digitopia|디지토피아|네이버\s*블로그|블로그\s*운영','Digitopia·블로그 명칭','높음'),
 ('routabl',r'기사앱|기사용\s*앱|고객앱|고객용\s*앱|배차|정산|Firestore|Firebase|Kotlin|Android Studio|고객\s*주소록|미수등록|픽업|영수증|대리기사|운송비|퀵서비스','기사앱·고객앱·배차/데이터 기능 단어','중간'),
 ('chatgpt',r'ChatGPT|챗지피티|OpenAI|GPT[- ]?[0-9]|AI\s*협업|Work\s*모드|AI\s*도구|Claude|Gemini|제미나이|크레딧|프롬프트|용어사전|채팅\s*기록|아카이브\s*복원|보관된\s*채팅','ChatGPT·AI 활용·계정 운영 단어','중간'),
 ('digital',r'NAS\s*백업|Synology\s*Drive|Google\s*Drive\s*동기화|SSD\s*백업|파일\s*동기화|폴더\s*이동|외장\s*SSD\s*활용|파일공유\s*설정','저장장치·백업·파일 동기화 단어','중간'),
 ('digitopia',r'홈페이지|웹사이트\s*제작|콘텐츠\s*정제|지식\s*자산','홈페이지·지식 콘텐츠 단어','중간'),
 ('devices',r'맥북|맥스튜디오|Mac\s*Studio|MacBook|macOS|Finder|파인더|아이패드|갤럭시|SSD|NVMe|모니터|네트워크|공유기|기가랜|와이파이|KT\s*인터넷|키보드|트랙패드|마우스|GPU|CPU|화면공유|무선\s*디버깅','기기·운영환경 단어','중간')
]
RULES=[(cat,re.compile(pattern,re.I),reason,confidence) for cat,pattern,reason,confidence in RULES]

def choose(title):
 t=unicodedata.normalize('NFKC',str(title or '')).strip()
 if not t:return ('review','제목 없음: 원래 프로젝트 확인 필요','확인 필요')
 # Strong label exists, but project assignment is ALWAYS inferred, never exported.
 for category,pattern,reason,confidence in RULES:
  m=pattern.search(t)
  if m:
   # Exception: multi-purpose continuation chat 96 needs review, do not assume original project.
   if re.match(r'^96\.',t) and 'Digitopia' in t:
    return ('review','96번은 백서 연속 대화와 Digitopia 주제가 겹쳐 기존 프로젝트 소속 확인 필요','확인 필요')
   return (category,reason+' ('+m.group(0)+')',confidence)
 return ('review','제목에서 신뢰할 수 있는 프로젝트 단서를 찾지 못함','확인 필요')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 os.umask(0o077)
 assert OLD.is_dir() and RAW.is_dir() and not NEW.exists(),'MISSING_SOURCE_OR_DEST_EXISTS'
 with (OLD/'search-data.js').open(encoding='utf-8') as f:
  source=f.read()
 assert source.startswith('window.ROUTABL_CHATS=')
 old_catalog=json.loads(source[len('window.ROUTABL_CHATS='):].rstrip('\n;'))
 assert len(old_catalog)==327
 allchats=[]
 for f in sorted(RAW.glob('conversations-*.json')):
  allchats.extend(json.loads(f.read_text('utf-8')))
 ids={c['conversation_id']:c for c in allchats}
 assert len(ids)==327
 NEW.mkdir(mode=0o700)
 (NEW/'chats').mkdir(mode=0o700)
 assert (OLD/'assets').is_dir()
 # Relative symlink keeps 1.8GB of original+media data in one private location.
 os.symlink('../10_GUI_VIEWER/assets',NEW/'assets')
 os.link(OLD/'search-data.js',NEW/'search-data.js')
 entries={};counts=Counter()
 for item in old_catalog:
  cid=item['id']; chat=ids[cid]
  group,why,confidence=choose(chat.get('title',''))
  status='보관됨' if chat.get('is_archived') is True else '일반'
  e={'group':group,'evidence':why,'confidence':confidence,'source':'제목 기반 추천·공식 원본 프로젝트 식별자 없음','archived':bool(chat.get('is_archived')),'export_date':'2026-11-05'}
  entries[cid]=e;counts[group]+=1
  old=OLD/'chats'/item['file'];dst=NEW/'chats'/item['file']
  raw=old.read_text('utf-8')
  assert 'class="chat-header"' in raw and '</body></html>' in raw
  label=NAME[group];d=escape
  notice='<div class="project-classification"><span class="class-label">추천 분류: '+d(label)+'</span><span class="class-caution">원래 ChatGPT 프로젝트 소속은 미확인</span><div class="class-explanation">근거: '+d(why)+' · 판정: '+d(confidence)+' · 내보내기 당시: '+status+'</div></div>'
  raw=raw.replace('<header class="chat-header">',notice+'<header class="chat-header">',1)
  dst.write_text(raw,encoding='utf-8')
 # Save machine-readable immutable snapshot alongside UI assets.
 obj={'schema':'routabl-classification-v0.2','source':'official ChatGPT export 2026-11-05',
      'project_membership':'NOT_EXPORTED','classification_is':'TOPIC_INFERENCE_NOT_CONFIRMED_CHATGPT_PROJECT',
      'groups':[{'key':k,'name':v,'description':desc} for k,v,desc in GROUPS],
      'conversations':entries}
 (NEW/'classification.json').write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 (NEW/'project-data.js').write_text('window.ROUTABL_PROJECTS='+json.dumps({'groups':obj['groups'],'conversations':entries},ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
 print('CLASSIFIED',json.dumps(dict(counts),ensure_ascii=False),flush=True)
 # Do not create new index or overwrite desktop shortcut until browser smoke test passes.
 report={
 'version':'v0.2','result':'GROUPING_DATA_AND_PAGES_PREPARED','total':len(old_catalog),
 'per_group':dict(counts),'all_original_project_memberships':'UNKNOWN',
 'rules':'title-first; no forced classification of generic titles',
 'previous_gui_unmodified':True,'legacy_html_pages_untouched':True,
 'archived_in_export':sum(e['archived'] for e in entries.values()),
 'source_metadata_without_project_field':True,
 'review_queue':counts['review'],
 'v2_dir':str(NEW),'v1_dir':str(OLD),
 'original_zip_unchanged':True,
 'classifications_sha256':sha(NEW/'classification.json'),
 'generated_kst':datetime.now(KST).isoformat(timespec='seconds')}
 (AUDIT/'gui_project_classification_v02.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print('V02_PREPARED',json.dumps(report,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
