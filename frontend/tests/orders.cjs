// Browser acceptance check. Run with Playwright available and both local services running.
const {chromium} = require("playwright");
const assert = require("node:assert/strict");
(async()=>{
 const browser=await chromium.launch({channel:"msedge"});
 try {
  const p=await browser.newPage();
  await p.goto((process.env.DEMO_WEB_URL||"http://localhost:3000")+"/deals/new");
  const fill=(key,value)=>p.locator('input[name="'+key+'"]').fill(value);
  await p.locator("[name=data_origin]").selectOption("demo");
  await fill("company","演示采购商"); await fill("name","不锈钢水瓶出口演示");
  await fill("i0name","Stainless Steel Bottle"); await fill("i0sku","BOTTLE-"+Date.now());
  await fill("i0qty","5000");await fill("i0price","3.00");await fill("i0cost","12.96");
  await p.getByText("添加费用",{exact:true}).click();await fill("c0amount","2500");
  await p.locator('[name=c0confirmed]').selectOption("true");
  await p.getByText("添加汇率",{exact:true}).click();
  for(const [k,v] of Object.entries({base:"USD",quote:"CNY",rate:"7.20",date:"2026-11-08",source:"手工演示汇率"}))await fill("r0"+k,v);
  await p.getByText("保存订单",{exact:true}).click();
  await p.getByText("23.33%",{exact:true}).waitFor();
  const url=p.url();await p.close();
  const detail=await browser.newPage();await detail.goto(url);
  await detail.getByText("3500",{exact:true}).waitFor();
  await detail.getByText("编辑订单",{exact:true}).click();
  await detail.locator("[name=notes]").fill("样例已复核");
  await detail.getByText("保存订单",{exact:true}).click();
  await detail.getByText(/样例已复核/).waitFor();
  await detail.goto((process.env.DEMO_WEB_URL||"http://localhost:3000")+"/deals");
  await detail.getByPlaceholder("订单号、订单名或买家").fill("不锈钢水瓶出口演示");
  assert(await detail.locator('a[href="'+new URL(url).pathname+'"]').first().waitFor()===undefined);
  console.log("CREATE / REOPEN / EDIT / LIST OK",url);
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});


