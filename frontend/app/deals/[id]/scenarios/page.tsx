"use client";
import {useParams} from "next/navigation";
import {useEffect,useState} from "react";
import {api,money} from "@/services/deals";
const states:Record<string,string>={FEASIBLE:"可行",INFEASIBLE:"不可行",INSUFFICIENT_DATA:"依据不足"};
const objectives:Record<string,string>={PROFIT_FIRST:"利润优先",BUYER_FIT:"买家匹配",LOW_RISK:"低风险"};
type Run={run_id:string,objective:string,status:string,created_at:string};
type Row={id:string,name:string,price:string,shipping:string,quantity:number,financials:Record<string,string>,utilization:string,delivery_days:number,feasibility:string,slack:number,explanation:{facts:string[],ranking:string,assumptions:string}};
type Data={currency:string,objective:string,rows:Row[],summary:{status:string,truncated:boolean,evaluated:number,diagnostics:Record<string,number>|string[]}};
type Selection={id:string,selected_by:string,selection_note:string,scenario_id:string,created_at:string};
type Report={id:string,report_number:string};
export default function Page(){
 const {id}=useParams<{id:string}>(),[runs,R]=useState<Run[]>([]),[run,U]=useState(""),[err,E]=useState(""),[decisions,H]=useState<Selection[]>([]),[reports,T]=useState<Report[]>([]),[busy,B]=useState(false);
 const refresh=()=>Promise.all([api("/deals/"+id+"/decisions").then(H),api("/deals/"+id+"/reports").then(T)]);
 useEffect(()=>{Promise.all([refresh(),api("/deals/"+id+"/optimization-history").then((r:Run[])=>{R(r);const key=new URLSearchParams(location.search).get("run");U(r.find(x=>x.run_id===key)?.run_id||r[0]?.run_id||"")})]).catch(e=>E(e.message))},[id]);
 async function generate(selection:string){B(true);try{const res=await api("/deals/"+id+"/reports","POST",{decision_selection_id:selection});location.assign("/reports/"+res.id)}catch(e){E((e as Error).message);B(false)}}
 return <><a href={"/deals/"+id}>返回订单</a><h1>方案对比</h1><label>历史优化运行<select value={run} onChange={e=>U(e.target.value)}>{runs.map(r=><option key={r.run_id} value={r.run_id}>{objectives[r.objective]} · {states[r.status]} · {new Date(r.created_at).toLocaleString("zh-CN")}</option>)}</select></label>
 {run?<Comparison key={run} id={id} run={run} saved={refresh}/>:<p>暂无优化记录。<a href={"/optimizer?deal="+id}>运行反向优化</a></p>}
 <p role="alert">{err}</p><h2>决策记录</h2>{!decisions.length&&<p>尚未选择方案。</p>}{decisions.map((s,i)=><div className="panel" key={s.id}><strong>{i===0?"当前选择":"历史选择"} · {s.selected_by}</strong><p>{new Date(s.created_at).toLocaleString("zh-CN")} · {s.selection_note||"未填写说明"}</p><button disabled={busy} onClick={()=>generate(s.id)}>生成决策报告</button></div>)}
 <h2 id="reports">决策报告</h2>{reports.length?reports.map(r=><p key={r.id}><a href={"/reports/"+r.id}>{r.report_number} · 查看报告</a></p>):<p>暂无报告。</p>}</>
}
function Comparison({id,run,saved}:{id:string,run:string,saved:()=>Promise<unknown>}){
 const [data,D]=useState<Data>(),[ids,I]=useState<string[]>([]),[chosen,C]=useState(""),[err,E]=useState(""),[busy,B]=useState(false),[notice,N]=useState("");
 useEffect(()=>{api("/optimization/"+run+"/comparison").then((v:Data)=>{D(v);I(v.rows.slice(0,3).map(s=>s.id));C(v.rows.find(s=>s.feasibility==="FEASIBLE")?.id||"")}).catch(e=>E(e.message))},[run]);
 if(!data)return <p>{err||"正在读取候选…"}</p>;
 const rows=ids.map(k=>data.rows.find(r=>r.id===k)!).filter(Boolean),feasible=data.rows.filter(x=>x.feasibility==="FEASIBLE");
 const cur=data.currency;
 const metrics:[string,(s:Row)=>string][]=[["优化目标",()=>data.objective],["单价 · "+cur,s=>money(s.price)],["数量",s=>String(s.quantity)],["物流方案",s=>s.shipping],["预计收入 · "+cur,s=>money(s.financials.revenue)],["预计总成本 · "+cur,s=>money(s.financials.total_included_cost)],["预计贡献利润 · "+cur,s=>money(s.financials.contribution_profit)],["预计贡献率",s=>s.financials.contribution_margin_percent+"%"],["交付天数",s=>String(s.delivery_days)],["产能占用率",s=>s.utilization+"%"],["可行性",s=>states[s.feasibility]]];
 return <><h2>{states[data.summary.status]} · 已评估 {data.summary.evaluated} 个候选，可行 {feasible.length} 个</h2>{data.summary.truncated&&<p role="alert">搜索已截断，排序仅覆盖已检查候选。</p>}{Array.isArray(data.summary.diagnostics)&&data.summary.diagnostics.map(s=><p key={s}>{s}</p>)}
 {!!rows.length&&<><p>以下为基于已确认纳入成本及人工交付条件的预计结果。可切换列查看其他候选。</p><div className="scroll"><table><thead><tr><th>指标</th>{ids.map((key,i)=><th key={i}><select aria-label={"对比列 "+(i+1)} value={key} onChange={e=>I(ids.map((v,j)=>j===i?e.target.value:v))}>{data.rows.map(r=><option disabled={ids.includes(r.id)&&r.id!==key} value={r.id} key={r.id}>{r.name} · {states[r.feasibility]}</option>)}</select></th>)}</tr></thead><tbody>{metrics.map(([label,get])=><tr key={label}><th>{label}</th>{rows.map(r=><td key={r.id}>{get(r)}</td>)}</tr>)}</tbody></table></div>
 <h2>指标图示</h2><div className="grid">{[6,7,1,8].map(idx=>{const [label,get]=metrics[idx];const values=rows.map(r=>Number(get(r).replace("%","")));const lo=Math.min(0,...values),hi=Math.max(0,...values);return <div className="panel" key={idx}><strong>{label}</strong>{rows.map((r,i)=><p key={r.id}>{r.name} <meter min={lo} max={hi||1} value={values[i]}/> {get(r)}</p>)}</div>})}</div>
 <h2>依据与权衡</h2>{rows.map(r=><div className="panel" key={r.id}><strong>{r.name} · {states[r.feasibility]}</strong><p>数学结果：{r.explanation.facts.join("、")}；交付余量 {r.slack} 天。</p><p>人工假设：{r.explanation.assumptions}</p><p>算法排序：{r.explanation.ranking}</p></div>)}</>}
 {!!feasible.length&&<form onSubmit={async e=>{e.preventDefault();const f=new FormData(e.currentTarget);B(true);E("");try{await api("/deals/"+id+"/decisions","POST",{optimization_run_id:run,scenario_id:chosen,selected_by:f.get("author"),selection_note:f.get("note")});await saved();N("选择已保存")}catch(x){E((x as Error).message)}finally{B(false)}}}><fieldset><legend>选择可行方案</legend><div className="grid"><label>首选方案<select value={chosen} onChange={e=>C(e.target.value)}>{feasible.map(r=><option key={r.id} value={r.id}>{r.name} · {cur} {money(r.price)}</option>)}</select></label><label>决策人<input name="author" required maxLength={240}/></label><label>选择说明<input name="note" maxLength={1000}/></label><button disabled={busy}>保存选择</button></div></fieldset></form>}<p role="status">{notice}</p><p role="alert">{err}</p></>
}
