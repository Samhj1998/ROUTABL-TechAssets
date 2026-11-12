"use strict";
/**
 * Offline static Markdown rendering, preserving original chat text in official export.
 * Outputs safe HTML only: Markdown-It html:false, linkify:false, image renderer disabled.
 * No network connections, no browser script eval, no raw HTML execution.
 */
const fs=require("fs");
const path=require("path");
const crypto=require("crypto");
const root="/Users/yongho/ROUTABL-ChatGPT-Archive/2026-11-05";
const gui=path.join(root,"13_GUI_MARKDOWN_V04");
const prior=path.join(root,"12_GUI_PROJECT_IDS_V03");
const audit=path.join(root,"20_AUDIT");
const packageRoot="/Users/yongho/Library/Application Support/RemoteDesktopCommander/runtime-0.2.52/node_modules";
const MarkdownIt=require(path.join(packageRoot,"markdown-it"));
const {decodeHTML}=require(path.join(packageRoot,"entities"));
const md=new MarkdownIt({html:false,linkify:false,breaks:true,typographer:false});
const htmlEscape=s=>String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
md.renderer.rules.image=(tokens,index,options,env,self)=>{
  const token=tokens[index];
  const label=htmlEscape(token.content||token.attrGet("alt")||"이미지");
  return '<span class="md-image-ref" aria-label="Markdown 이미지 참조">[이미지 참조: '+label+']</span>';
};
const priorOpen=md.renderer.rules.link_open||((tokens,idx,options,env,self)=>self.renderToken(tokens,idx,options));
md.renderer.rules.link_open=(tokens,idx,opts,env,self)=>{
 tokens[idx].attrSet("rel","noopener noreferrer");
 tokens[idx].attrSet("target","_blank");
 return priorOpen(tokens,idx,opts,env,self);
};
function render(source){
 const decoded=decodeHTML(source);
 if(!decoded.trim())return "";
 const out=md.render(decoded);
 return out.replace(/<table>/g,'<div class="md-table-scroll"><table>')
           .replace(/<\/table>/g,'</table></div>');
}
const tests=[
 ["| 항목 | 결과 |\n|---|---|\n| 백업 시도 | false |", "<table>"],
 ["**중요**", "<strong>중요</strong>"],
 ["# 제목\n\n- 하나\n- 둘", "<h1>제목</h1>"],
 ["~~취소~~", "<s>취소</s>"],
 ["\u0060\u0060\u0060kotlin\nval a = 5\n\u0060\u0060\u0060", "<pre><code"],
 ["<script>alert('x')</script>", "&lt;script&gt;"],
 ["[공격](javascript:alert(1))", "javascript:"],
];
for(const [input,expect] of tests){
 const result=render(input);
 if(input.startsWith("[공격]")){
  if(result.includes('href="javascript:')||result.includes('src="javascript:'))throw Error("UNSAFE_URL_ACCEPTED");
 }else if(!result.includes(expect))throw Error("MARKDOWN_UNIT_TEST_FAILED "+expect);
}
const files=fs.readdirSync(path.join(gui,"chats")).filter(n=>n.endsWith(".html")).sort();
if(files.length!==327)throw Error("INVALID_PAGE_COUNT "+files.length);
const pattern=/<div class="message-content">([\s\S]*?)<\/div>/g;
const counts={pages:0,markdown_messages:0,tables:0,headings:0,codeBlocks:0,strongTags:0,blockquoteTags:0,bulletOrOrderedLists:0,source_html_escaped:0};
let matchedExample=null;
for(const fname of files){
 const file=path.join(gui,"chats",fname);
 const txt=fs.readFileSync(file,"utf8");
 let number=0;
 const updated=txt.replace(pattern,(full,source)=>{
   number++;
   const rendered=render(source);
   counts.tables+=(rendered.match(/<table>/g)||[]).length;
   counts.headings+=(rendered.match(/<h[1-6]>/g)||[]).length;
   counts.codeBlocks+=(rendered.match(/<pre>/g)||[]).length;
   counts.strongTags+=(rendered.match(/<strong>/g)||[]).length;
   counts.blockquoteTags+=(rendered.match(/<blockquote>/g)||[]).length;
   counts.bulletOrOrderedLists+=(rendered.match(/<(?:ul|ol)>/g)||[]).length;
   if(source.includes("&lt;script")&&rendered.includes("&lt;script"))counts.source_html_escaped++;
   if(!matchedExample&&rendered.includes("백업 시도")&&rendered.includes("<table>")){
     matchedExample={page:fname,table_present:true};
   }
   return '<div class="message-content markdown-body">'+rendered+'</div>';
 });
 if(number===0&&txt.includes('class="message-content"'))throw Error("REGEX_FOUND_ZERO_CONTENT "+fname);
 counts.markdown_messages+=number;
 counts.pages++;
 fs.writeFileSync(file,updated,{encoding:"utf8",flag:"w"});
 if(counts.pages%70===0)console.log("MARKDOWN_RENDER_PROGRESS",counts.pages,"/",files.length);
}
if(counts.tables<10)throw Error("SUSPICIOUS_LOW_TABLE_COUNT "+counts.tables);
if(counts.codeBlocks<10)throw Error("SUSPICIOUS_LOW_CODE_COUNT "+counts.codeBlocks);
const sourceLedger=path.join(gui,"restoration-ledger.json");
const sha=file=>crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");
const report={
 status:"SAFE_STATIC_MARKDOWN_RENDER_PASS",
 engine:"markdown-it existing local package",
 engine_source:"local RemoteDesktopCommander runtime; not loaded by browser at run time",
 markdown_options:{html:false,linkify:false,breaks:true,typographer:false},
 unsafe_raw_html_allowed:false,
 remote_markdown_image_loading_allowed:false,
 external_network_used:false,
 output_type:"fully_static_offline_html",
...counts,matched_table_example:matchedExample,
 conversation_page_count:files.length,
 restoration_overlay_sha256:sha(sourceLedger),
 export_snapshot:"2026-11-05",
};
const receipt=path.join(audit,"v04_markdown_render_receipt_20261106.json");
fs.writeFileSync(receipt,JSON.stringify(report,null,2)+"\n",{encoding:"utf8",flag:"wx"});
console.log("MARKDOWN_FINAL",JSON.stringify(report));
