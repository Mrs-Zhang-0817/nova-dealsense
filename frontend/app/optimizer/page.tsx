"use client";
import {FormEvent,useEffect,useState} from "react";
import {api,money} from "@/services/deals";
import "../deals/orders.css";

type DealChoice={id:string,name:string,deal_number:string};
type Deal=DealChoice & {currency:string,items:{quantity:string}[],costs:{id:string,description:string,cost_type:string,included:boolean}[],financials:Record<string,string>};
const labels:Record<string,string>={FEASIBLE:"可行",INFEASIBLE:"不可行",INSUFFICIENT_DATA:"依据不足",PROFIT_FIRST:"利润优先",BUYER_FIT:"买家匹配",LOW_RISK:"低风险",margin:"贡献率",profit:"最低利润",capacity:"产能",deadline:"交期",budget:"客户总预算",unit_ceiling:"客户单价上限",moq:"起订量",quantity_range:"数量范围"};
type Candidate={price:string,quantity:number,shipping:string,delivery_days:number,minimum_margin_price:string,financials:Record<string,string>};
type Run={run_id:string,status:string,truncated:boolean,evaluated:number,objective:string,diagnostics:string[]|Record<string,number>,recommended:Candidate|null,alternatives:Candidate[]};
type History={run_id:string,status:string,created_at:string};
export default function Page(){
 const [choices,C]=useState<DealChoice[]>([]),[id,I]=useState(""),[error,E]=useState("");
 useEffect(()=>{(async()=>{const list:DealChoice[]=[];let page=1;while(true){const res=await api("/deals?page_size=100&page="+page++);list.push(...res.items);if(list.length>=res.total||!res.items.length)break}C(list);I(list.find(r=>r.id===new URLSearchParams(location.search).get("deal"))?.id||list[0]?.id||"")})().catch(e=>E(e.message))},[]);
 return <main className="orders"><header><a href="/">NOVA DealSense</a><a href="/deals">订单管理</a></header><h1>反向交易优化</h1><label>选择订单<select value={id} onChange={e=>I(e.target.value)}>{choices.map(c=><option value={c.id} key={c.id}>{c.name} · {c.deal_number}</option>)}</select></label><p role="alert">{error}</p>{id&&<Editor key={id} id={id}/>}</main>
}
function Editor({id}:{id:string}){
 const [deal,D]=useState<Deal>(),[history,H]=useState<History[]>([]),[result,R]=useState<Run>(),[err,E]=useState(""),[busy,B]=useState(false),[ships,S]=useState(1);
 const refresh=()=>api("/deals/"+id+"/optimization-history").then(H);
 useEffect(()=>{Promise.all([api("/deals/"+id).then(D),refresh()]).catch(e=>E(e.message))},[id]);
 const input=(k:string,label:string,required=true,initial="",integer=false)=><label key={k}>{label}<input name={k} required={required} type="number" step={integer?"1":"any"} min="0" defaultValue={initial}/></label>;
 async function submit(e:FormEvent<HTMLFormElement>){e.preventDefault();B(true);E("");R(undefined);
 const f=new FormData(e.currentTarget),body:Record<string,unknown>={deal_id:id},adjust:Record<string,string>={};
 for(const [key,v] of f.entries()){if(!v)continue;if(key.startsWith("cost:"))adjust[key.slice(5)]=String(v);else if(!key.startsWith("ship:"))body[key]=v}
 body.additional_cost_adjustments=adjust;body.shipping_options=Array.from({length:ships},(_,i)=>({name:f.get("ship:name"+i),days:f.get("ship:days"+i),replacement_cost:f.get("ship:cost"+i)||null}));
 try{R(await api("/deals/"+id+"/optimize","POST",body));await refresh()}catch(ex){E((ex as Error).message)}finally{B(false)}}
 if(!deal)return <p role="alert">{err||"正在读取订单…"}</p>;
 return <><div className="panel"><strong>原订单 · {deal.currency}</strong><p>收入 {money(deal.financials.revenue)}　计入成本 {money(deal.financials.total_included_cost)}　贡献利润 {money(deal.financials.contribution_profit)}　贡献率 {deal.financials.contribution_margin_percent??"—"}%</p></div>
 <form onSubmit={submit}><fieldset><legend>财务目标 · {deal.currency}</legend><div className="grid"><label>排序目标<select name="objective">{["PROFIT_FIRST","BUYER_FIT","LOW_RISK"].map(o=><option key={o} value={o}>{labels[o]}</option>)}</select></label>{input("target_margin","目标贡献率（0.25 表示 25%）")}{input("minimum_profit","最低贡献利润")}{input("price_min","最低协商价")}{input("price_max","最高协商价")}{input("price_step","报价步长")}{input("customer_unit_price_ceiling","客户单价上限",false)}{input("customer_total_budget","客户总预算",false)}</div></fieldset>
 <fieldset><legend>数量与交付</legend><div className="grid">{input("quantity_min","最低数量",true,deal.items[0]?.quantity,true)}{input("quantity_max","最高数量",true,deal.items[0]?.quantity,true)}{input("quantity_step","数量步长",true,"1",true)}{input("minimum_order_quantity","起订量",false,"",true)}{input("production_capacity","可用总产能",true,"",true)}{input("delivery_deadline_days","客户交期（天）",true,"",true)}{input("setup_days","准备天数",false,"",true)}{input("production_units_per_day","日产能",false,"",true)}</div></fieldset>
 <fieldset><legend>物流与成本</legend><p>替换运费为整单金额，将替换现有物流类别成本。留空沿用订单成本。请核实其他费用中是否含运费。</p>{Array.from({length:ships},(_,i)=><div key={i} className="grid row"><label>物流方案<input name={"ship:name"+i} required/></label>{input("ship:days"+i,"运输天数",true,"",true)}{input("ship:cost"+i,"替换运费",false)}</div>)}<button type="button" disabled={ships>=32} onClick={()=>S(ships+1)}>添加物流方案</button>{ships>0&&<button type="button" onClick={()=>S(ships-1)}>移除末项物流</button>}
 {deal.costs.filter(c=>c.included).map(c=><label key={c.id}>{c.description||c.cost_type} · 数量变化时<select name={"cost:"+c.id}><option value="">待确认</option><option value="fixed">整单固定</option><option value="per_unit">随数量等比例变化</option></select></label>)}</fieldset>
 <button disabled={busy}>{busy?"计算中…":"运行优化"}</button></form><p role="alert">{err}</p>
 {result&&<section className="panel"><h2>{labels[result.status]} · {labels[result.objective]}</h2><p>已检查 {result.evaluated} 个候选{result.truncated?"，达到搜索上限，仅展示已检查范围。":""}</p>
 {Array.isArray(result.diagnostics)?result.diagnostics.map(t=><p key={t}>{t}</p>):Object.entries(result.diagnostics).map(([k,v])=><p key={k}>{labels[k]}未满足：{v} 个候选</p>)}
 {[...(result.recommended?[result.recommended]:[]),...result.alternatives].map((c,i)=><div key={i} className="row"><strong>{i?"备选方案 "+i:"推荐方案"}</strong><p>单价 {money(c.price)} · 数量 {c.quantity} · {c.shipping} · 交付 {c.delivery_days} 天</p><p>目标贡献率最低报价 {money(c.minimum_margin_price)}　贡献利润 {money(c.financials.contribution_profit)}　贡献率 {c.financials.contribution_margin_percent}%</p></div>)}</section>}
 <a className="action" href={"/deals/"+id+"/scenarios"+(result?"?run="+result.run_id:"")}>比较已保存方案</a><h2 id="history">优化历史</h2>{history.map(h=><p key={h.run_id}><button onClick={()=>api("/optimization/"+h.run_id).then(R).catch(e=>E(e.message))}>{new Date(h.created_at).toLocaleString("zh-CN")} · {labels[h.status]}</button></p>)}</>
}

