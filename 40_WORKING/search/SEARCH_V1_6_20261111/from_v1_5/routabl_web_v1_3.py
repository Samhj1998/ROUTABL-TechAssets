#!/usr/bin/env python3
"""ROUTABL local-only search UI (127.0.0.1). Never writes NAS or Firebase."""
import contextlib, importlib.util, io, json, urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
index_script=Path(__file__).with_name('routabl_assetsearch_v1_3.py')
s=importlib.util.spec_from_file_location('assets',str(index_script))
engine=importlib.util.module_from_spec(s);s.loader.exec_module(engine)
PAGE="""<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>라우터블 기술자산 검색</title><style>
:root{font-family:-apple-system,BlinkMacSystemFont,'Noto Sans KR',sans-serif;color:#1b303b;background:#f3f7f8}
main{max-width:930px;margin:35px auto;padding:0 18px}h1{font-size:27px;color:#133655}p{line-height:1.6}
form{display:flex;gap:8px;margin:24px 0}input{flex:1;border:1px solid #bbccd4;border-radius:9px;padding:13px;font-size:17px}
button{border:0;border-radius:9px;background:#126b78;color:white;padding:10px 16px;cursor:pointer;font-size:15px}
.item{background:white;padding:16px 19px;margin:10px 0;border:1px solid #dfebed;border-radius:12px}
.title{font-weight:650;font-size:17px}small{color:#56707d;display:block;margin-top:7px;overflow-wrap:anywhere}
.tag{background:#e5f1f1;color:#185d67;padding:4px 8px;border-radius:9px;font-size:12px;display:inline-block;margin:5px 5px 0 0}
h2{margin-top:35px;color:#254d5c}#meta{color:#486574}
footer{margin:25px 0;color:#6a7d87;font-size:13px}
</style><main><h1>라우터블 기술자산 통합검색</h1>
<p>원고 · 검증 · 출처 · 실행 경로를 검색합니다. <b>원본 코드는 실행하지 않습니다.</b></p>
<form id="search"><input id="q" autocomplete="off" placeholder="예: 주소등록, cloud_access.py, 초성검색, DATA-01, F1"><button>검색</button></form>
<p id="meta">로컬 Mac에서만 사용 · NAS 및 Mac 원본 읽기 전용 · 일반 코드 내용 색인 · 인증정보 제외 · 태그는 일부 자동 제안</p><section id="results"></section>
<footer>v1.3 일반 소스 내용 검색 · 기밀 메타데이터 보호 | 인쇄용·대외 공개용 아님 | PDF와 ZIP 내부는 일부 파일명 검색만 지원</footer>
</main><script>
const $=x=>document.getElementById(x);
function el(tag,text,cl){let n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cl)n.className=cl;return n}
function row(title,path,tags,description){const d=el('div',undefined,'item');d.append(el('div',title,'title'));
d.append(el('small','위치: '+path));d.append(el('small',description));if(tags)d.append(el('span',tags,'tag'));return d}
$('search').onsubmit=async e=>{e.preventDefault();let q=$('q').value.trim();if(!q)return;
$('results').replaceChildren();$('meta').textContent='검색 중…';
try{let r=await fetch('/api?q='+encodeURIComponent(q));let data=await r.json();
$('meta').textContent='일반 결과 '+data.match_count+'건 · 별도 관리 기술자산 '+data.manual.length+'건 (일부 중복 가능)';
if(data.manual.length){$('results').append(el('h2','사례·위험·실행경로'));for(let x of data.manual){
$('results').append(row(x.title,x.path,x.tags,x.source_grade+' / '+x.validation_grade+' — '+x.details));}}
$('results').append(el('h2','NAS 보관자료 · Mac 코드/문서'));
for(let x of data.top){$('results').append(row(x.title,x.path,x.tags,x.status+(x.archive_member?' · ZIP 내부 파일명':' · 원본 파일')))}
if(!data.manual.length&&!data.top.length)$('results').append(el('p','검색 결과 없음. 다른 키워드나 기술자산 ID를 사용해 보세요.'));
}catch(err){$('meta').textContent='검색 오류: '+err.message}};
</script></html>"""
class App(BaseHTTPRequestHandler):
 def do_GET(self):
  p=urllib.parse.urlsplit(self.path)
  if p.path=='/api':
   q=urllib.parse.parse_qs(p.query).get('q',[''])[0].strip()[:100]
   if not q:self.reply(400,b'{}','application/json');return
   out=io.StringIO()
   try:
    with contextlib.redirect_stdout(out):engine.query(q)
    self.reply(200,out.getvalue().encode('utf-8'),'application/json; charset=utf-8')
   except Exception as e:
    self.reply(500,json.dumps({'error':str(e)}).encode('utf-8'),'application/json')
   return
  if p.path=='/':self.reply(200,PAGE.encode('utf-8'),'text/html; charset=utf-8')
  else:self.reply(404,b'Not Found','text/plain')
 def reply(self,status,body,mime):
  self.send_response(status);self.send_header('Content-Type',mime)
  self.send_header('Cache-Control','no-store')
  self.send_header('X-Content-Type-Options','nosniff')
  self.send_header('Content-Security-Policy',"default-src 'self' 'unsafe-inline'")
  self.end_headers();self.wfile.write(body)
 def log_message(self,*args):pass
if __name__=='__main__':
 print('라우터블 기술자산 검색: http://127.0.0.1:8767')
 ThreadingHTTPServer(('127.0.0.1',8767),App).serve_forever()
