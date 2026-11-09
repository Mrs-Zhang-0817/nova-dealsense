const {chromium}=require("playwright");
const assert=require("node:assert/strict");
(async()=>{
 const browser=await chromium.launch({channel:"msedge"});
 try{
  const page=await browser.newPage();
  await page.goto((process.env.DEMO_WEB_URL||"http://localhost:3000")+"/optimizer");
  const id=process.argv[2];
  await page.getByLabel("选择订单").selectOption(id);
  const fill=(key,value)=>page.locator('[name="'+key+'"]').fill(String(value));
  for(const [key,value] of Object.entries({target_margin:".25",minimum_profit:0,price_min:"3",price_max:"3.07",price_step:".01",quantity_min:5000,quantity_max:5000,quantity_step:1,production_capacity:5000,delivery_deadline_days:10,setup_days:1,production_units_per_day:1000,"ship:name0":"演示物流","ship:days0":4})) await fill(key,value);
  async function run(expected){
   const response=page.waitForResponse(r=>r.url().endsWith("/optimize")&&r.request().method()==="POST");
   await page.getByRole("button",{name:"运行优化"}).click();
   const r=await response;assert.equal(r.status(),201);
   const out=await r.json();assert.equal(out.status,expected);
   await page.locator("section.panel h2").waitFor();
   console.log(expected,out.run_id,out.recommended?.price,out.diagnostics);return out;
  }
  const feasible=await run("FEASIBLE");
  assert.equal(feasible.recommended.financials.contribution_margin_percent,"25.08");
  await page.getByText(/目标贡献率最低报价 3.07/).first().waitFor();
  await fill("customer_unit_price_ceiling","3.00");
  await run("INFEASIBLE");
  await page.getByText(/客户单价上限未满足/).waitFor();
  await fill("setup_days","");
  await run("INSUFFICIENT_DATA");
  await page.reload();await page.getByLabel("选择订单").selectOption(id);
  await page.getByRole("button",{name:/ · 可行$/}).first().click();
  await page.getByText(/贡献率 25.08%/).first().waitFor();
  console.log("Reloaded saved recommendation in Edge");
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});

