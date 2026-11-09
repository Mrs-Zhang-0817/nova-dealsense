"use client";
import {useParams} from "next/navigation";
import {useEffect,useState} from "react";
import {api,statuses,categories,money} from "@/services/deals";
type Line={id:string,product_name_snapshot:string,sku_snapshot:string,quantity:string,unit:string,unit_price:string,unit_price_currency:string,unit_manufacturing_cost:string,cost_currency:string,converted_manufacturing_cost:string,manufacturing_confirmed:boolean};
type Cost={id:string,cost_type:string,description:string,amount:string,currency:string,converted_amount:string,confirmed:boolean,included:boolean};
type Detail={name:string,deal_number:string,buyer:{company_name:string,country_code:string,contact_name:string,email:string},origin_country:string,destination_country:string,currency:string,incoterm:string,status:string,requested_deadline:string,notes:string,items:Line[],costs:Cost[],exchange_rates:{base:string,quote:string,rate:string,date:string,source:string}[],financials:Record<string,string>&{has_estimates:boolean}};
export default function Page(){const {id}=useParams<{id:string}>();const [d,D]=useState<Detail>(),[err,E]=useState("");useEffect(()=>{api("/deals/"+id).then(D).catch(e=>E(e.message))},[id]);if(!d)return <p role="alert">{err||"正在读取订单…"}</p>;
 return <><h1>{d.name}</h1><div className="grid">{d.deal_number} · {statuses[d.status]} <a className="action" href={"/deals/"+id+"/edit"}>编辑订单</a></div><nav className="grid panel"><a href="#analysis">订单分析</a><a href={"/optimizer?deal="+id}>反向优化</a><a href={"/optimizer?deal="+id+"#history"}>历史优化</a><a href={"/deals/"+id+"/scenarios"}>方案对比</a><a href={"/deals/"+id+"/scenarios#reports"}>决策报告</a></nav><div className="panel"><h2>买家与交付</h2>{d.buyer.company_name}（{d.buyer.country_code}） {d.buyer.contact_name} {d.buyer.email}<p>{d.origin_country} → {d.destination_country} · {d.incoterm} · {d.currency}</p><p>要求交付日期 {d.requested_deadline||"未填写"}　{d.notes}</p></div>
 <h2>商品与制造成本</h2>{d.items.map(i=><div className="panel" key={i.id}><strong>{i.product_name_snapshot} · {i.sku_snapshot}</strong><p>{i.quantity} {i.unit} × {i.unit_price_currency} {i.unit_price}</p>单位制造成本 {i.cost_currency} {i.unit_manufacturing_cost} · 折算合计 {d.currency} {money(i.converted_manufacturing_cost)}（{i.manufacturing_confirmed?"已确认":"估算"}）</div>)}
 <h2>其他订单成本</h2>{d.costs.map(c=><p key={c.id}>{categories[c.cost_type]} · {c.description} · {c.currency} {c.amount} → {d.currency} {money(c.converted_amount)}（{c.confirmed?"已确认":"估算"}，{c.included?"纳入":"排除"}）</p>)}
 <h2>汇率记录</h2>{d.exchange_rates.map(r=><p key={r.base+r.quote}>1 {r.base} = {r.rate} {r.quote} · {r.date} · {r.source}</p>)}
 <h2 id="analysis">订单财务 · {d.currency}</h2>{d.financials.has_estimates&&<p>尚有未确认费用，当前贡献利润仅扣除已确认且纳入的成本。</p>}<div className="panel">{Object.entries({revenue:"销售收入",manufacturing_cost:"制造成本",additional_costs:"其他已计成本",total_included_cost:"计入总成本",contribution_profit:"贡献利润",contribution_margin:"贡献率"}).map(([k,label])=><p key={k}>{label}　<strong>{k==="contribution_margin"?(d.financials[k]?d.financials.contribution_margin_percent+"%":"无收入，无法计算"):money(d.financials[k])}</strong></p>)}</div></>;
}


