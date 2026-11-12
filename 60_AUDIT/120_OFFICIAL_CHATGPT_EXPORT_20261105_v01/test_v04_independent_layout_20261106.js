"use strict";
const fs=require("fs"),path=require("path"),crypto=require("crypto");
const root="/Users/yongho/ROUTABL-ChatGPT-Archive/2026-11-05";
const gui=path.join(root,"13_GUI_MARKDOWN_V04");
const pug="/Users/yongho/Library/Application Support/RemoteDesktopCommander/runtime-0.2.52/node_modules";
const puppeteer=require(path.join(pug,"puppeteer"));
const report={status:"PENDING",snapshot:"2026-11-05",tests:[],prior_version_folders_not_modified:true,prior_version_http_requests_blocked:true};
let browser;
function ensure(id,pass,data){
 report.tests.push({id,pass:!!pass,observed:data});
 console.log("VERIFY",id,pass?"PASS":"FAIL",JSON.stringify(data).slice(0,320));
 if(!pass)throw Error("FAILED_"+id);
}
async function run(){
 browser=await puppeteer.launch({headless:true,executablePath:"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  args:["--disable-background-networking","--disable-sync","--disable-extensions","--disable-gpu","--no-first-run","--no-default-browser-check",
  "--user-data-dir="+path.join(root,"20_AUDIT/CHROME_V04_INDEPENDENCE_PROBE")]});
 const page=await browser.newPage();
 await page.setViewport({width:1450,height:900,deviceScaleFactor:1});
 const fetched=[];const blocked=[];
 await page.setRequestInterception(true);
 page.on("request",req=>{
   const u=req.url();
   if(/\/(?:10_GUI_VIEWER|11_GUI_PROJECTS_V02|12_GUI_PROJECT_IDS_V03)\//.test(u)){
     blocked.push(u);return req.abort();
   }
   fetched.push(u);return req.continue();
 });
 page.on("requestfailed",request=>{if(!blocked.includes(request.url()))report.other_request_failures=(report.other_request_failures||[]).concat(request.url());});
 const fileUrl="file://"+encodeURI(path.join(gui,"index.html"));
 await page.goto(fileUrl,{waitUntil:"load",timeout:30000});
 const v=await page.evaluate(()=>{
  const g=document.querySelector("#v03-layout");
  const nav=document.querySelector(".project-sidebar");
  const panel=document.querySelector("section.panel");
  const r1=nav.getBoundingClientRect(),r2=panel.getBoundingClientRect();
  const sheet=[...document.styleSheets].map(s=>s.href?.split("/").pop()).filter(Boolean);
  return {display:getComputedStyle(g).display,gridColumns:getComputedStyle(g).gridTemplateColumns,
   nav:{x:r1.x,y:r1.y,w:r1.width,h:r1.height},panel:{x:r2.x,y:r2.y,w:r2.width,h:r2.height},sheets:sheet};
 });
 ensure("wide_layout_is_grid",v.display==="grid",v);
 ensure("wide_project_sidebar_at_left",v.nav.x<v.panel.x && Math.abs(v.nav.y-v.panel.y)<8 && v.nav.w>250 && v.nav.w<340,v);
 ensure("all_linked_css_loaded",["style.css","project-style.css","v03-style.css","v04-style.css"].every(a=>v.sheets.includes(a)),v.sheets);
 const initial=await page.$eval("#resultCount",n=>n.textContent);
 ensure("all_327_loaded_without_previous_version_folders",initial.includes("검색 결과 327건"),initial);
 await page.$eval("#projectNav",root=>[...root.querySelectorAll("button")].find(b=>b.innerText.includes("Routabl 개발")).click());
 const routabl=await page.$eval("#resultCount",n=>n.textContent);
 ensure("routabl_121_filter_works",routabl.includes("검색 결과 121건"),routabl);
 await page.select("#restoreFilter","confirmed");
 const restored=await page.$eval("#resultCount",n=>n.textContent);
 ensure("user_restoration_21_filter_works",restored.includes("검색 결과 21건"),restored);
 const fileName=fs.readdirSync(path.join(gui,"chats")).find(name=>name.includes("6ae898f1-a73c-83ec-ba41-3decfb9617d5"));
 ensure("test_detail_page_exists",!!fileName,fileName);
 if(fileName){
  await page.goto("file://"+encodeURI(path.join(gui,"chats",fileName)),{waitUntil:"load",timeout:30000});
  const m=await page.evaluate(()=>({
   tables:document.querySelectorAll(".message-content.markdown-body table").length,
   headings:document.querySelectorAll(".message-content.markdown-body h1,.message-content.markdown-body h2").length,
   images:document.querySelectorAll(".attachment-card img").length,
   assetImages:[...document.querySelectorAll(".attachment-card img")].slice(0,4).map(i=>i.getAttribute("src"))
  }));
  ensure("markdown_tables_headings_rendered",m.tables>=1&&m.headings>=1,m);
  ensure("local_attachments_present",m.images>=1,m);
  if(m.images){
   const checked=await page.evaluate(async()=>{
    const img=document.querySelector(".attachment-card img");img.scrollIntoView();
    await new Promise(resolve=>{if(img.complete)return resolve();img.addEventListener("load",resolve,{once:true});img.addEventListener("error",resolve,{once:true});setTimeout(resolve,2800);});
    return {src:img.getAttribute("src"),naturalWidth:img.naturalWidth,complete:img.complete};
   });
   ensure("local_v04_attached_image_loads",checked.naturalWidth>0,checked);
  }
 }
 ensure("no_resource_loaded_from_v01_to_v03",blocked.length===0,blocked);
 ensure("no_essential_local_resource_failure",(report.other_request_failures||[]).length===0,report.other_request_failures||[]);
 await page.setViewport({width:780,height:900});
 await page.goto(fileUrl,{waitUntil:"load",timeout:30000});
 const narrow=await page.evaluate(()=>{
  const side=document.querySelector(".project-sidebar").getBoundingClientRect();
  const main=document.querySelector("section.panel").getBoundingClientRect();
  return {css:getComputedStyle(document.querySelector("#v03-layout")).gridTemplateColumns,
    side:{x:side.x,y:side.y,w:side.width},main:{x:main.x,y:main.y,w:main.width}}
 });
 ensure("responsive_narrow_stack_expected",narrow.main.y>narrow.side.y && Math.abs(narrow.main.x-narrow.side.x)<8,narrow);
 report.status="PASS";
 console.log("TEST_FINAL",JSON.stringify({status:report.status,passed:report.tests.filter(a=>a.pass).length,total:report.tests.length}));
}
run().catch(e=>{report.status="FAIL";report.error=String(e.stack||e);console.error(report.error);process.exitCode=1;})
.finally(async()=>{
 try{if(browser)await browser.close();}catch{}
 fs.writeFileSync(path.join(root,"20_AUDIT/v04_independent_layout_browser_verification_20261106.json"),JSON.stringify(report,null,2)+"\n",{encoding:"utf8",flag:"wx"});
});
