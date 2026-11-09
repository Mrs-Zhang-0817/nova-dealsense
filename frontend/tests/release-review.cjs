const {chromium}=require("playwright");
const fs=require("node:fs");const path=require("node:path");const assert=require("node:assert/strict");
(async()=>{
 const web=process.env.DEMO_WEB_URL||"http://localhost:3000",api=process.env.DEMO_API_URL||"http://localhost:8000/api/v1";
 const get=async p=>{const r=await fetch(api+p);assert(r.ok);return r.json()};
 const {items}=await get("/deals");const example=items.find(x=>x.name==="提交演示 A · 可行报价"&&x.data_origin==="demo");assert(example);
 const id=example.id,reports=await get("/deals/"+id+"/reports");assert(reports.length);
 const destination=process.argv[2];fs.mkdirSync(destination,{recursive:true});
 const browser=await chromium.launch({channel:"msedge"});
 try{const p=await browser.newPage();const errors=[];p.on("pageerror",e=>errors.push(e.message));
 for(const width of [1280,1440]){
  await p.setViewportSize({width,height:900});
  const pages=[["dashboard","/","决策总览"],["deals","/deals","交易列表"],["analysis","/deals/"+id,"提交演示 A · 可行报价"],["optimizer","/optimizer?deal="+id,"优化历史"],["scenarios","/deals/"+id+"/scenarios","指标图示"],["report","/reports/"+reports[0].id,"08　数据来源与假设"]];
  for(const [file,url,title] of pages){
   await p.goto(web+url);await p.getByRole("heading",{name:title,exact:true}).waitFor();
   if(file==="dashboard"){await p.getByLabel("数据来源").selectOption("demo");await p.getByRole("link",{name:reports[0].report_number}).waitFor()}
   if(file==="deals")await p.getByRole("link",{name:example.name,exact:true}).waitFor();
   assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),"page overflow: "+file);
   if(width===1440)await p.screenshot({path:path.join(destination,file+".png")});
  }
 }
 assert.deepEqual(errors,[]);console.log("6 pages at both widths; no page overflow or JS errors.",id,reports[0].id);
 const res=await fetch(api+"/reports/"+reports[0].id+"/download");assert(res.ok);
 fs.writeFileSync(path.join(destination,"bottle-report.pdf"),Buffer.from(await res.arrayBuffer()));
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
