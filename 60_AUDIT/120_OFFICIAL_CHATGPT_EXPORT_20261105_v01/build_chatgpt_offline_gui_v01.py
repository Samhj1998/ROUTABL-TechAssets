#!/usr/bin/env python3
"""Read-only source conversion: official ChatGPT export -> offline Safari GUI.
Only explicit user+assistant visible content; other JSON remains in extracted original.
Local private files only. No network, no remote dependency, no model transformations.
"""
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import Counter
from urllib.parse import quote
from html import escape
import hashlib, os, re, json, unicodedata, stat, sys

ROOT=Path('/Users/yongho/ROUTABL-ChatGPT-Archive/2026-11-05')
RAW=ROOT/'00_EXTRACTED_ORIGINAL'
GUI=ROOT/'10_GUI_VIEWER'
CHATS=GUI/'chats'
ASSETS=GUI/'assets'
RECEIPT=ROOT/'20_AUDIT'/'gui_build_validation_v0.1.json'
KST=timezone(timedelta(hours=9))
os.umask(0o077)

def h(s):return escape(str(s or ''), quote=True)
def n(s):return unicodedata.normalize('NFKC',str(s or '')).lower()
def tstr(ts):
 try:return datetime.fromtimestamp(float(ts),KST).strftime('%Y-%m-%d %H:%M')
 except (ValueError,TypeError,OverflowError,OSError):return '시간 미기록'
def title_of(chat):
 title=chat.get('title')
 return (str(title).strip() if title else '(제목 없음)') or '(제목 없음)'
def sha(p):
 a=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(2*1024*1024),b''):a.update(b)
 return a.hexdigest()
def write_new(p,txt):
 with p.open('x',encoding='utf-8') as f:f.write(txt)
def safe_ext(p, preferred=''):
 with p.open('rb') as f:b=f.read(64)
 ext=Path(preferred).suffix.lower()
 if b.startswith(b'\x89PNG\r\n\x1a\n'):return '.png'
 if b.startswith(b'\xff\xd8\xff'):return '.jpg'
 if b.startswith((b'GIF87a',b'GIF89a')):return '.gif'
 if b.startswith(b'RIFF') and b[8:12]==b'WEBP':return '.webp'
 if b.startswith(b'%PDF'):return '.pdf'
 if b[4:12] in (b'ftypheic',b'ftypheix',b'ftyphevc',b'ftypmif1'):return '.heic'
 if b.startswith(b'PK\x03\x04'):
  return ext if ext in ('.docx','.xlsx','.pptx','.zip','.odt','.ods','.odp') else '.zip'
 if b[:4]==b'ID3' or b[:2] in (b'\xff\xfb',b'\xff\xf3'):return '.mp3'
 if b[4:8]==b'ftyp':return '.mp4' if ext in ('.mov','.mp4') else '.mp4'
 return ''
def eligible(node):
 msg=node.get('message') or {}
 if (msg.get('author') or {}).get('role') not in ('user','assistant'):return False
 cont=msg.get('content') or {}
 if cont.get('content_type') not in ('text','multimodal_text'):return False
 if (msg.get('metadata') or {}).get('is_visually_hidden_from_conversation'):return False
 return True
def extract_parts(msg):
 content=msg.get('content') or {}
 text_parts=[];refs=[]
 for p in content.get('parts',[]) if isinstance(content.get('parts',[]),list) else []:
  if isinstance(p,str):
   if p.strip():text_parts.append(p)
  elif isinstance(p,dict):
   c=p.get('content_type','')
   if c=='image_asset_pointer':
    ap=p.get('asset_pointer')
    if isinstance(ap,str):refs.append((ap.split('/')[-1],None))
   elif isinstance(p.get('text'),str) and p['text'].strip():text_parts.append(p['text'])
 if not text_parts and isinstance(content.get('text'),str):text_parts.append(content['text'])
 for item in (msg.get('metadata') or {}).get('attachments',[]):
  if isinstance(item,dict) and item.get('id'):refs.append((str(item['id']),str(item.get('name') or '')))
 return '\n\n'.join(text_parts),refs
def path_nodes(chat):
 mp=chat.get('mapping') or {};current=chat.get('current_node')
 ids=[];seen=set()
 while current and current in mp and current not in seen:
  seen.add(current);ids.append(current);current=mp[current].get('parent')
 ids.reverse()
 active=[mp[i] for i in ids if eligible(mp[i])]
 alternate=[item for key,item in mp.items() if key not in seen and eligible(item)]
 alternate.sort(key=lambda v:(float((v.get('message') or {}).get('create_time') or 0),str(v.get('id',''))))
 if not active and alternate:
  return alternate,[]
 return active,alternate
def asset_element(fid,preferred,links,mapping):
 key=('/'.join(str(fid).split('/'))).split('/')[-1]
 if not re.fullmatch('[a-zA-Z0-9_-]{5,160}',key):return '',False
 src=key if key.endswith('.dat') else key+'.dat'
 display=preferred or mapping.get(src) or key
 linked=links.get(src)
 if not linked:
  return '<span class="attachment-placeholder">첨부파일 참조: '+h(display)+' (미리보기 불가 또는 원본 없음)</span>',False
 ext=Path(linked).suffix.lower()
 href='../assets/'+quote(linked)
 if ext in ('.png','.jpg','.jpeg','.gif','.webp'):
  html='<a class="attachment-card" href="'+h(href)+'" target="_blank" rel="noopener"><img loading="lazy" src="'+h(href)+'" alt="'+h(display)+'"><span class="attachment-label">이미지 · '+h(display)+'</span></a>'
 else:
  html='<a class="attachment-card" href="'+h(href)+'" target="_blank" rel="noopener"><span class="attachment-label" style="padding:12px 15px">첨부파일 열기 · '+h(display)+'</span></a>'
 return html,True
def render_message(node,links,mapping):
 msg=node.get('message') or {}
 role=(msg.get('author') or {}).get('role','')
 text,refs=extract_parts(msg)
 label='나' if role=='user' else 'ChatGPT'
 when=tstr(msg.get('create_time'))
 body='<div class="message-content">'+h(text)+'</div>' if text.strip() else ''
 attachment_html=[];seen=set();available=0;missing=0
 for fid,name in refs:
  key=str(fid).split('/')[-1]
  if key in seen:continue
  seen.add(key)
  element,ok=asset_element(key,name,links,mapping)
  if element:attachment_html.append(element)
  available+=int(ok);missing+=int(not ok)
 extra='<div class="attachment-area">'+''.join(attachment_html)+'</div>' if attachment_html else ''
 out='<section class="message '+role+'"><div class="message-head"><span class="who">'+h(label)+'</span><span class="time">'+h(when)+'</span></div>'+body+extra+'</section>'
 return out,text,available,missing,len(seen)
def html_shell(title,body,css):
 return '<!doctype html>\n<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="referrer" content="no-referrer"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'self\' \'unsafe-inline\'; img-src \'self\' data:; script-src \'self\'; connect-src \'none\'; base-uri \'none\'; object-src \'none\'; form-action \'none\'"><title>'+h(title)+'</title><link rel="stylesheet" href="'+css+'"></head><body>'+body+'</body></html>'
def build():
 assert RAW.is_dir() and (RAW/'chat.html').is_file()
 assert not CHATS.exists() and not ASSETS.exists() and not (GUI/'index.html').exists(),'GUI_EXISTS_USE_NEW_VERSION'
 CHATS.mkdir(mode=0o700);ASSETS.mkdir(mode=0o700)
 with (RAW/'conversation_asset_file_names.json').open(encoding='utf8') as f:mapping=json.load(f)
 links={};filetypes=Counter();unrecognized=[]
 for p in RAW.glob('*.dat'):
  ext=safe_ext(p,mapping.get(p.name,''))
  if not ext:
   unrecognized.append(p.name);continue
  new=p.stem+ext
  target=ASSETS/new
  if not target.exists():os.link(p,target)
  links[p.name]=new;filetypes[ext]+=1
 print('ASSET_LINKS_READY',json.dumps({'viewable':len(links),'types':dict(filetypes),'unknown':len(unrecognized)},ensure_ascii=False),flush=True)
 conv=[]
 for fn in ['conversations-000.json','conversations-001.json','conversations-002.json','conversations-003.json']:
  with (RAW/fn).open(encoding='utf8') as f:
   shard=json.load(f);assert isinstance(shard,list);conv.extend(shard)
 assert len(conv)==327
 conv.sort(key=lambda c:(float(c.get('update_time') or 0),str(c.get('conversation_id') or '')),reverse=True)
 used=set();catalog=[];report=[];all_messages=0;attachments=0;missing=0;alternates=0
 for i,chat in enumerate(conv,1):
  title=title_of(chat);cid=chat.get('conversation_id') or chat.get('id') or str(i)
  assert cid not in used;used.add(cid)
  filename=str(i).zfill(4)+'-'+re.sub('[^a-zA-Z0-9-]','',cid)+'.html'
  active,alt=path_nodes(chat)
  main_html=[];alt_html=[];full_text=[];has_att=0;unavail=0;per_chat=0
  for node in active:
   rendered,txt,ok,bad,total=render_message(node,links,mapping)
   main_html.append(rendered)
   if txt.strip():full_text.append(txt)
   has_att+=ok;unavail+=bad;per_chat+=total
  for node in alt:
   rendered,txt,ok,bad,total=render_message(node,links,mapping)
   alt_html.append(rendered)
   if txt.strip():full_text.append(txt)
   has_att+=ok;unavail+=bad;per_chat+=total
  all_messages+=len(active)+len(alt);attachments+=has_att;missing+=unavail;alternates+=len(alt)
  date=tstr(chat.get('update_time'))
  meta='<div class="chips"><span class="pill">현재 흐름 '+str(len(active))+'건</span><span class="pill neutral">기타 분기 '+str(len(alt))+'건</span><span class="pill neutral">첨부 확인 '+str(has_att)+'건</span></div>'
  header='<div class="topbar"><a class="brand" href="../index.html">ROUTABL <span>Archive</span><small>ChatGPT 공식 데이터 내보내기</small></a><a class="toplink" href="../index.html">← 대화 목록</a></div>'
  intro='<main><a class="back" href="../index.html">← 전체 대화로 돌아가기</a><header class="chat-header"><div class="eyebrow">대화 원문 · '+h(date)+'</div><h1>'+h(title)+'</h1>'+meta+'<div class="muted">원본 ID: '+h(cid)+'</div></header>'
  if not active:intro+='<div class="notice">현재 흐름에서 표시할 대화 텍스트가 없어, 나머지 기록을 아래에 표시합니다.</div>'
  branch='<details class="branch"><summary>다른 분기의 대화 '+str(len(alt))+'건 보기</summary><p class="note">대화 편집·재생성 등의 분기일 수 있습니다. 원본 JSON은 별도로 보존됩니다.</p>'+''.join(alt_html)+'</details>' if alt_html else ''
  tail='<p class="footnote">이 화면은 로컬에서 생성한 읽기 전용 열람본입니다. 숨겨진 내부 기록·도구 데이터는 표시하지 않으며, 모든 공식 원본 데이터는 압축 해제 폴더에 보관되어 있습니다.</p></main><a class="jump-top" href="#">↑ 맨 위로</a>'
  write_new(CHATS/filename,html_shell(title,header+intro+''.join(main_html)+branch+tail,'../style.css'))
  full=' '.join(full_text)
  preview=next((x.replace('\n',' ').strip()[:150] for x in full_text if x.strip()),'표시할 텍스트 없음')
  updated=float(chat.get('update_time') or 0)
  catalog.append({
   'id':cid,'file':filename,'title':title,'titleNorm':n(title),'dateKst':date,'updated':updated,
   'preview':preview,'mainCount':len(active),'alternativeCount':len(alt),'attachmentCount':has_att,
   'search':full,'searchNorm':n(title+' '+full)})
  report.append({'id':cid,'title':title,'file':filename,'main_count':len(active),'branch_count':len(alt),'attachment_viewable_count':has_att,'attachment_missing_count':unavail})
  if i%80==0:print('GUI_PROGRESS',i,'/',len(conv),flush=True)
 # Search catalog is a separate local script so the index HTML is fast to render.
 js='window.ROUTABL_CHATS='+json.dumps(catalog,ensure_ascii=False,separators=(',',':')).replace('\u2028','\\u2028').replace('\u2029','\\u2029')+';\n'
 write_new(GUI/'search-data.js',js)
 index_body='''<header class="topbar"><div class="brand">ROUTABL <span>Archive</span><small>Smart Transport Management · 개인 기술자산</small></div><span class="toplink">오프라인 · 로컬 전용</span></header>
 <main><section class="hero"><div><div class="eyebrow">CHATGPT OFFICIAL EXPORT / 2026.11.05</div><h1>내 대화 아카이브</h1><p class="muted">원본을 그대로 보존하고, 제목·내용을 검색해서 직접 읽을 수 있는 화면입니다.</p></div>
 <div class="stats"><div class="stat"><strong>327</strong><span>대화 기록</span></div><div class="stat"><strong>__MESSAGES__</strong><span>표시 가능한 메시지</span></div><div class="stat"><strong>__IMAGES__</strong><span>열람 가능한 첨부 참조</span></div></div></section>
 <section class="panel"><div class="toolbar"><label class="searchbox" aria-label="대화 검색"><svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="10" cy="10" r="7"/><path d="m15 15 6 6"/></svg><input id="query" placeholder="예: 120, Firebase, 고객 주소록, 백서, NAS" autocomplete="off" autofocus></label>
 <label class="toggle"><input id="titleOnly" type="checkbox">제목만 검색</label><select id="order" class="select" aria-label="정렬"><option value="recent">최근 수정순</option><option value="old">오래된 순</option><option value="title">제목 가나다순</option></select></div><div class="meta-row"><span id="resultCount">전체 대화 불러오는 중...</span><span>원본 데이터 기준</span></div><div id="results" class="results"></div></section>
 <div class="notice">사용법: 검색어 입력 → 대화 제목 클릭 → 사용자·AI 메시지 읽기 → 「전체 대화로 돌아가기」. 첨부 이미지가 있는 대화에서는 이미지도 클릭해 확대할 수 있습니다.</div>
 <p class="footnote">공식 원본 열람: <a href="../00_EXTRACTED_ORIGINAL/chat.html">ChatGPT가 제공한 chat.html 열기 (약 70MB · 로딩이 느릴 수 있음)</a>. 이 GUI는 공식 원본을 수정하지 않는 별도 열람본입니다. 인터넷 서버로 데이터를 전송하지 않습니다.</p></main><script src="search-data.js"></script><script src="app.js"></script>'''
 index_body=index_body.replace('__MESSAGES__',f'{all_messages:,}').replace('__IMAGES__',f'{attachments:,}')
 write_new(GUI/'index.html',html_shell('ROUTABL ChatGPT 대화 아카이브',index_body,'style.css'))
 assert len(catalog)==327 and len(list(CHATS.glob('*.html')))==327
 result={
  'result':'OFFLINE_SAFARI_GUI_CREATED','original_export_snapshot':'2026-11-05',
  'raw_export_path':str(RAW),'index_file':str(GUI/'index.html'),
  'conversation_count':len(conv),'unique_conversation_id_count':len(used),
  'message_count_visible_in_gui':all_messages,'alternative_branch_visible_count':alternates,
  'attachment_links_in_messages':attachments,'attachment_references_unavailable_or_unsupported':missing,
  'viewer_assets_file_count':len(links),'viewer_asset_types':dict(filetypes),
  'search_data_bytes':(GUI/'search-data.js').stat().st_size,
  'index_sha256':sha(GUI/'index.html'),'search_index_sha256':sha(GUI/'search-data.js'),
  'no_network_dependencies':True,'source_zip_untouched':True,'raw_json_unchanged':True,
  'content_display_policy':'user/assistant text and multimodal_text only; thoughts/reasoning_recap/tool-internal excluded from GUI; raw source preserved',
  'archived_branch_policy':'current_node ancestor chain plus expandable off-branch user/assistant messages',
  'generated_utc':datetime.now(timezone.utc).isoformat(),
  'per_conversation':report}
 write_new(RECEIPT,json.dumps(result,ensure_ascii=False,indent=2))
 print('FINAL_SUCCESS',json.dumps({k:v for k,v in result.items() if k!='per_conversation'},ensure_ascii=False),flush=True)

if __name__=='__main__':build()
