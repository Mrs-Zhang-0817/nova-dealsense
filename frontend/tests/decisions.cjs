// Run with local API and Edge. Optionally pass a bottle deal ID; with no ID create an example via the UI.
const {chromium}=require("playwright");
const {mkdirSync}=require("node:fs");
const path=require("node:path");
const assert=require("node:assert/strict");
(async()=>{
 const browser=await chromium.launch({channel:"msedge"});
 try{
  const p=await browser.newPage();p.setDefaultTimeout(60000);
  let id=process.argv[2];
  const fill=(name,value)=>p.locator('[name="'+name+'"]').fill(String(value));
  if(!id){
   await p.goto((process.env.DEMO_WEB_URL||"http://localhost:3000")+"/deals/new");
   await p.locator("[name=data_origin]").selectOption("demo");
   for(const [k,v] of Object.entries({company:"演示采购商",name:"水瓶决策流程演示",i0name:"Stainless Steel Bottle",i0sku:"DEC-"+Date.now(),i0qty:5000,i0price:"3.00",i0cost:"12.96"}))await fill(k,v);
   await p.getByText("添加费用",{exact:true}).click();await fill("c0amount",2500);await p.locator("[name=c0confirmed]").selectOption("true");
   await p.getByText("添加汇率",{exact:true}).click();
   for(const [k,v] of Object.entries({base:"USD",quote:"CNY",rate:"7.20",date:"2026-11-08",source:"手工演示汇率"}))await fill("r0"+k,v);
   await p.getByText("保存订单",{exact:true}).click();await p.getByText("23.33%",{exact:true}).waitFor();
   id=new URL(p.url()).pathname.split("/").pop();
  }else{await p.goto((process.env.DEMO_WEB_URL||"http://localhost:3000")+"/deals/"+id);await p.getByText("23.33%",{exact:true}).waitFor()}
  await p.getByRole("link",{name:"反向优化",exact:true}).click();
  await p.waitForFunction(id=>document.querySelector('select')?.value===id,id);
  for(const [k,v] of Object.entries({target_margin:".25",minimum_profit:0,price_min:"3.00",price_max:"3.09",price_step:".01",quantity_min:5000,quantity_max:5000,production_capacity:5000,delivery_deadline_days:10,setup_days:1,production_units_per_day:1000,"ship:name0":"演示物流","ship:days0":4})) await fill(k,v);
  for(const objective of ["PROFIT_FIRST","LOW_RISK","BUYER_FIT"]){
   await p.locator("[name=objective]").selectOption(objective);
   const wait=p.waitForResponse(r=>r.url().endsWith("/optimize")&&r.request().method()==="POST");
   await p.getByText("运行优化",{exact:true}).click();const res=await (await wait).json();assert.equal(res.status,"FEASIBLE");console.log(objective,res.recommended.price);
  }
  await p.getByRole("link",{name:"比较已保存方案"}).click();
  await p.getByRole("heading",{name:/可行 3 个/}).waitFor();
  assert.equal(await p.locator("meter").count(),12);
  await fill("author","演示评审");await fill("note","选择达到 25% 贡献率且最接近原始报价的方案。");
  await p.getByText("保存选择",{exact:true}).click();
  await p.getByRole("button",{name:"生成决策报告"}).first().click();
  await p.getByRole("heading",{name:/跨境交易决策分析报告/}).waitFor();
  const dir=path.resolve(__dirname,"../../output/pdf");mkdirSync(dir,{recursive:true});
  const wait=p.waitForEvent("download");await p.getByRole("link",{name:"下载 PDF"}).click();
  const pdf=await wait;await pdf.saveAs(path.join(dir,"bottle-decision-"+id+".pdf"));
  await p.reload();await p.getByRole("heading",{name:/风险与局限/}).waitFor();
  console.log("Edge workflow OK",id,p.url());
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});

