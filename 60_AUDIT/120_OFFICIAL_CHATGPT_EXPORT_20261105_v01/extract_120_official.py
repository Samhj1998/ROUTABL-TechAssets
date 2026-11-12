#!/usr/bin/python3
"""Non-destructive source-preserving extraction of ChatGPT 120 from owner export."""
from pathlib import Path
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
import hashlib,json,zipfile,os,collections

BASE=Path('/Users/yongho/ROUTABL-TechAssets')
ARCHIVE_DIR=BASE/'20_ORIGINALS/ChatGPT-Account-Exports/2026-11-05/00_ORIGINAL'
OUT=BASE/'20_ORIGINALS/ChatGPT-Account-Exports/2026-11-05/10_CHAT_120'
AUDIT=BASE/'60_AUDIT/120_OFFICIAL_CHATGPT_EXPORT_20261105_v01'
EXPECTED='06efc5c5c787d59b7d1bd62566974563416b29792bb17ac318335475884c5553'
CONV_ID='6ae898f1-a73c-83ec-ba41-3decfb9617d5'
os.umask(0o077)
src=list(ARCHIVE_DIR.glob('*.zip'))
assert len(src)==1 and src[0].is_file() and not src[0].is_symlink()
assert hashlib.sha256(src[0].read_bytes()).hexdigest()==EXPECTED
with zipfile.ZipFile(src[0]) as zipf:
    name='conversations-003.json'
    data=json.loads(zipf.read(name))
    matches=[x for x in data if x.get('conversation_id')==CONV_ID]
assert len(matches)==1
c=matches[0]
assert c['title'].startswith('120.') and len(c['mapping'])==731
assert not OUT.exists(), 'NO_OVERWRITE_EXISTING_EXTRACTION'
OUT.mkdir(mode=0o700,parents=False)
def preserve_bytes(name,payload):
    target=OUT/name
    with target.open('xb') as w:
        w.write(payload)
        w.flush()
        os.fsync(w.fileno())
    os.chmod(target,0o600)
    return {'path':str(target),'bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest()}
raw=(json.dumps(c,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
rawrcpt=preserve_bytes('120_ORIGINAL_CONVERSATION_RECORD.json',raw)
mp=c['mapping']
nodes=[]
cur=c.get('current_node'); seen=set()
while cur and cur in mp and cur not in seen:
    seen.add(cur);nodes.append(mp[cur]);cur=mp[cur].get('parent')
assert len(nodes)==len(mp), 'UNVISITED_BRANCH_OR_MISSING_CHAIN'
nodes.reverse()
counts=collections.Counter()
md=['# 120. 라우터블 기술자산 통합관리체계 — 공식 내보내기 가독본',
    '','**출처:** 2026-11-05 ChatGPT 계정 전체 내보내기 ZIP 중 단일 대화 레코드',
    '**보존 원칙:** 원본 JSON은 별도 불변 사본, 아래는 사용자가 읽는 대화 부분만 추출한 파생본',
    '**주의:** thoughts/reasoning_recap 노드와 내부 단계는 읽기용 텍스트에서 제외. 원본 레코드에는 변형 없이 보존.',
    '**시간:** 원본 메시지 timestamp를 KST로 변환. 일부 내용은 마크다운·구조화 부품을 포함.',
    '']
for node in nodes:
    m=node.get('message') or {}
    if not m:
        counts['empty']+=1
        continue
    role=(m.get('author') or {}).get('role','unknown')
    co=m.get('content') or {};kind=co.get('content_type','none')
    counts[f'{role}/{kind}']+=1
    if role not in ('user','assistant') or kind not in ('text','multimodal_text'):
        continue
    pieces=[]
    for part in co.get('parts') or []:
        if isinstance(part,str):
            pieces.append(part)
        elif isinstance(part,dict):
            if part.get('content_type')=='text' and isinstance(part.get('text'),str):
                pieces.append(part['text'])
            else:
                counts['nontext_parts_referenced']+=1
                pieces.append('[비텍스트 첨부/멀티모달 구성요소 — 원본 JSON 참조]')
    if not pieces:
        counts['empty_visible_parts']+=1
        continue
    ts=m.get('create_time')
    when=datetime.fromtimestamp(ts,ZoneInfo('Asia/Seoul')).isoformat(timespec='seconds') if isinstance(ts,(int,float)) else '시간 미기록'
    role_ko='사용자' if role=='user' else 'ChatGPT'
    md+=['',f'## {role_ko} — {when} — 메시지 ID {m.get("id") or node.get("id")}','', '\n\n'.join(pieces),'']
    counts[f'{role}_readable_messages']+=1
    counts[f'{role}_characters']+=sum(len(x) for x in pieces)
readable=preserve_bytes('120_READABLE_CHAT_USER_ASSISTANT.md',('\n'.join(md)+'\n').encode('utf8'))
metadata={'source_zip_sha256':EXPECTED,'source_member':name,'source_conversation_id':CONV_ID,'title':c['title'],
          'conversation_created_unix':c.get('create_time'),'conversation_updated_unix':c.get('update_time'),
          'is_archived':c.get('is_archived'),'mapping_nodes':len(mp),'linear_chain_nodes':len(nodes),
          'counts':dict(counts),'original_record':rawrcpt,'readable_markdown':readable,
          'private_archive':'P3_LOCAL_ENCRYPTED_BACKUP_ONLY',
          'full_export_zip_untouched':True,'PDF_comparison':'PENDING','library_completeness':'PENDING'}
receipt=(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n').encode('utf8')
with (AUDIT/'120_EXTRACTION_VERIFICATION_v0.1.json').open('xb') as f:f.write(receipt)
os.chmod(AUDIT/'120_EXTRACTION_VERIFICATION_v0.1.json',0o600)
print(json.dumps({'status':'EXTRACTED_SINGLE_CHAT_120','original_record_bytes':rawrcpt['bytes'],
 'readable_bytes':readable['bytes'],'original_record_sha256':rawrcpt['sha256'],
 'readable_sha256':readable['sha256'],'mapping_nodes':len(mp),
 'readable_user_messages':counts['user_readable_messages'],
 'readable_assistant_messages':counts['assistant_readable_messages'],
 'raw_backup_independent':'PENDING'},ensure_ascii=False))
