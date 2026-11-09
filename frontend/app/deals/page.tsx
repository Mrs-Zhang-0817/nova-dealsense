"use client";
import {useEffect,useState} from "react";
import {api,Market,statuses,money} from "@/services/deals";
type Row={id:string,deal_number:string,name:string,buyer_name:string,destination_country:string,currency:string,estimated_value:string,status:string,created_at:string};
export default function List(){
 const [markets,M]=useState<Market[]>([]),[rows,R]=useState<Row[]>([]),[loading,L]=useState(true),[q,Q]=useState(""),[country,C]=useState(""),[status,S]=useState(""),[page,P]=useState(1),[total,T]=useState(0),[err,E]=useState("");
 useEffect(()=>{api("/markets").then(M).catch(e=>E(e.message))},[]);
 useEffect(()=>{let active=true;L(true);api("/deals?"+new URLSearchParams({q,destination_country:country,status,page:String(page)})).then(data=>{if(active){L(false);R(data.items);T(data.total)}}).catch(e=>{if(active){L(false);E(e.message)}});return()=>{active=false}},[q,country,status,page]);
 return <><h1>交易列表</h1><div className="grid"><label>搜索<input value={q} onChange={e=>{Q(e.target.value);P(1)}} placeholder="订单号、订单名或买家"/></label><label>目的市场<select value={country} onChange={e=>{C(e.target.value);P(1)}}><option value="">全部市场</option>{markets.map(m=><option key={m.country_code} value={m.country_code}>{m.country_name_zh}</option>)}</select></label><label>状态<select value={status} onChange={e=>{S(e.target.value);P(1)}}><option value="">全部状态</option>{Object.entries(statuses).map(([k,v])=><option key={k} value={k}>{v}</option>)}</select></label><a className="action" href="/deals/new">创建订单</a></div><p role="alert">{err}</p>
 <div className="scroll"><table><thead><tr>{["订单号","订单名称","买家","目的市场","预计订单金额","状态","创建日期"].map(h=><th key={h}>{h}</th>)}</tr></thead><tbody>{(!rows.length||loading)&&<tr><td colSpan={7}>{loading?"正在读取订单…":"没有匹配的订单"}</td></tr>}{rows.map(r=><tr key={r.id}><td><a href={"/deals/"+r.id}>{r.deal_number}</a></td><td><a href={"/deals/"+r.id}>{r.name}</a></td><td>{r.buyer_name}</td><td>{markets.find(m=>m.country_code===r.destination_country)?.country_name_zh || r.destination_country}</td><td>{r.currency} {money(r.estimated_value)}</td><td>{statuses[r.status]}</td><td>{r.created_at.slice(0,10)}</td></tr>)}</tbody></table></div><div className="grid"><button disabled={page===1} onClick={()=>P(page-1)}>上一页</button>共 {total} 条 · 第 {page} 页<button disabled={page*20>=total} onClick={()=>P(page+1)}>下一页</button></div></>;
}

