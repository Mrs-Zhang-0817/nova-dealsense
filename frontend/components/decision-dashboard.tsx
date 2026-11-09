"use client";
import {useEffect,useState} from "react";
import {api,money} from "@/services/deals";
type Stats={total_value:Record<string,string>,feasible_runs:number,active:number,runs:number,feasible:number,infeasible:number,decisions:number,reports:{id:string,report_number:string}[]};
export function DecisionDashboard({english}:{english:boolean}){
 const [all,A]=useState<Record<string,Stats>>(),[origin,O]=useState("actual"),[error,E]=useState("");
 useEffect(()=>{api("/dashboard").then(A).catch(e=>E(e.message))},[]);
 const data=all?.[origin];
 const labels=english?["Active deals","Optimization runs","Feasible runs","Latest run infeasible","Saved selections"]:["活跃订单","优化运行","可行优化结果","最近一次不可行的订单","已保存选择"];
 return <div><h2>{english?"Decision overview":"决策总览"}</h2><select aria-label="数据来源" style={{background:"var(--card)"}} value={origin} onChange={e=>O(e.target.value)}>{["actual","demo","unknown"].map((k,i)=><option key={k} value={k}>{(english?["Actual business","Demo","Unclassified"]:["真实业务","演示数据","来源未标注"])[i]}</option>)}</select>{data?<><p className="portfolio-value">{english?"Total order value":"订单总额"}　{Object.entries(data.total_value||{}).map(([c,v])=>c+" "+money(v)).join(" · ")||(english?"No orders":"暂无订单")}</p><ul>{[data.active,data.runs,data.feasible_runs,data.infeasible,data.decisions].map((v,i)=><li key={i}>{labels[i]} <strong>{v}</strong></li>)}</ul><h2>{english?"Recent reports":"近期决策报告"}</h2>{data.reports.length?data.reports.map(r=><p key={r.id}><a href={"/reports/"+r.id}>{r.report_number}</a></p>):<p>{english?"No reports in this group.":"此分类暂无决策报告。"}</p>}</>:<p>{error||"…"}</p>}</div>
}

