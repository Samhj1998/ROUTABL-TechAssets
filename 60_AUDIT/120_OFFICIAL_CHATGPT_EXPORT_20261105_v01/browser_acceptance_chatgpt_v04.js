"use strict";
const fs=require("fs");
const path=require("path");
const root="/Users/yongho/ROUTABL-ChatGPT-Archive/2026-11-05";
const gui=path.join(root,"13_GUI_MARKDOWN_V04");
const packageRoot="/Users/yongho/Library/Application Support/RemoteDesktopCommander/runtime-0.2.52/node_modules";
const puppeteer=require(path.join(packageRoot,"puppeteer"));
const RID="g-p-6a92532988c881918be08fc0ad4dbaed";
const origToUrl=file=>"file://"+file.split(path.sep).map((s,i)=>i===0?"":encodeURIComponent(s)).join("/");
const entry=origToUrl(path.join(gui,"index.html"));
let browser;
const result={status:"PENDING",tests:[],source_snapshot:"2026-11-05",restorations_are_user_reported:true};
function check(name,condition,detail){
 result.tests.push({test:name,pass:!!condition,detail});
 console.log("TEST",name,condition?"PASS":"FAIL",String(detail||"").slice(0,160));
 if(!condition)throw Error("V04_BROWSER_CHECK_FAILED: "+name);
}
async function run(){
 browser=await puppeteer.launch({
   headless:true,
   executablePath:"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
   args:["--disable-background-networking","--disable-sync","--disable-extensions","--disable-gpu","--no-first-run","--no-default-browser-check","--disable-default-apps",
   "--user-data-dir="+path.join(root,"20_AUDIT/CHROME_V04_SMOKETEST_PROFILE")]
 });
 const page=await browser.newPage();
 page.on("console",msg=>{if(msg.type()==="error")result.consoleErrors=(result.consoleErrors||[]).concat(msg.text().slice(0,180));});
 await page.goto(entry,{waitUntil:"load",timeout:30000});
 const text=async(id)=>page.$eval("#"+id,el=>el.textContent||"");
 let v=await text("resultCount");
 check("all_327_chat_pages",v.includes("검색 결과 327건"),v);
 const side=await page.$$eval("#projectNav button",els=>els.map(x=>({text:x.innerText,count:x.querySelector(".proj-count")?.innerText})));
 check("project_menu_8_groups",side.length===9,side.length);
 const item=side.find(x=>x.text.includes("Routabl 개발"));
 check("routabl_121_count",item&&item.count==="121",item&&item.text);
 await page.evaluate(id=>{
  const button=[...document.querySelectorAll("#projectNav button")].find(b=>b.textContent.includes("Routabl 개발"));
  if(!button)throw Error("NO_ROUTABL_BUTTON");
  button.click();
 },RID);
 v=await text("resultCount");
 check("routabl_project_121_rendered",v.includes("검색 결과 121건"),v);
 await page.select("#restoreFilter","confirmed");
 v=await text("resultCount");
 check("restored_21_rendered",v.includes("검색 결과 21건"),v);
 const reported=await page.$$eval("#results .itemtitle",els=>els.map(e=>e.textContent));
 check("added_two_both_in_routabl_list",reported.includes("고객 주소록 등록")&&reported.includes("Firebase 요금 변경 알림"),reported.filter(x=>x.includes("고객 주소록")||x.includes("Firebase 요금")));
 await page.select("#archiveFilter","archived");
 v=await text("resultCount");
 check("restored_21_were_export_archived",v.includes("검색 결과 21건"),v);
 await page.select("#restoreFilter","all");
 await page.select("#archiveFilter","all");
 v=await text("resultCount");
 check("filter_reset_121",v.includes("검색 결과 121건"),v);
 const extra=await page.$$eval("#results .item",els=>{
  const entry=els.find(n=>n.querySelector(".itemtitle")?.textContent==="고객 주소록 등록");
  return entry?{text:entry.textContent.slice(0,450),href:entry.querySelector("a")?.getAttribute("href")}:null;
 });
 check("extra_has_user_confirmed_and_original_null",extra&&extra.text.includes("사용자 확인 · 원본 프로젝트 ID 없음"),extra&&extra.text);
 await page.goto(origToUrl(path.join(gui,"chats","0008-6aea44bd-228c-83e8-a3d4-b42b23419cd7.html")),{waitUntil:"load",timeout:30000});
 const tableState=await page.evaluate(()=>{
  const t=document.querySelector(".message-content.markdown-body table");
  if(!t)return null;
  const th=t.querySelector("th");
  return {count:document.querySelectorAll(".markdown-body table").length,collapse:getComputedStyle(t).borderCollapse,heading:th?.textContent,scrollable:!!t.closest(".md-table-scroll"),codeblocks:document.querySelectorAll(".markdown-body pre").length};
 });
 check("markdown_tables_real_html",tableState&&tableState.count>0,tableState);
 check("markdown_table_styled",tableState&&tableState.collapse==="collapse"&&tableState.scrollable,tableState);
 // Source excerpt includes the user-reported formatting failure: no literal delimiters in tabular table.
 const containsPipes=await page.evaluate(()=>[...document.querySelectorAll(".markdown-body table")].some(t=>t.outerHTML.includes("|---|---|")));
 check("markdown_delimiter_not_visible_as_table_content",!containsPipes,containsPipes);
 await page.goto(entry+"?project="+RID,{waitUntil:"load",timeout:30000});
 v=await text("resultCount");
 check("direct_project_link_121",v.includes("검색 결과 121건"),v);
 const confirmed=await page.evaluate(()=>{const item=[...document.querySelectorAll("#results a.itemtitle")].find(a=>a.textContent==="기사앱 수정 요청");return item?.getAttribute("href")||null;});
 check("archived_driver_edit_chat_present",!!confirmed,confirmed);
 if(confirmed){
   await page.goto(new URL(confirmed,entry).href,{waitUntil:"load",timeout:30000});
   const note=await page.$eval(".restore-note",e=>e.textContent);
   check("detailed_20261106_user_restore_note",note.includes("2026-11-06 사용자 복원 확인"),note.slice(0,150));
 }
 result.status="PASS";result.chrome_rendered=true;result.external_network_calls=0;
 console.log("FINAL",JSON.stringify({status:result.status,passed:result.tests.filter(x=>x.pass).length,total:result.tests.length},null,2));
}
run().catch(e=>{result.status="FAIL";result.error=String(e.stack||e);console.error(result.error);process.exitCode=1;})
 .finally(async()=>{
   try{if(browser)await browser.close();}catch{}
   const report=path.join(root,"20_AUDIT/v04_browser_acceptance_20261106.json");
   fs.writeFileSync(report,JSON.stringify(result,null,2)+"\n",{encoding:"utf8",flag:"wx"});
 });
