"use client";
import {useParams} from "next/navigation";
import {useEffect,useState} from "react";
import {api} from "@/services/deals";
import "../../deals/orders.css";
type Report={title:string,report_number:string,generated_at:string,demo_inputs:boolean,sections:{title:string,rows:[string,string][]}[],source:{deal:{id:string}}};
export default function ReportPage(){
 const {id}=useParams<{id:string}>(),[report,R]=useState<Report>(),[error,E]=useState("");
 useEffect(()=>{api("/reports/"+id).then(R).catch(e=>E(e.message))},[id]);
 if(!report)return <main><p>{error||"正在读取报告…"}</p></main>;
 const url=(process.env.NEXT_PUBLIC_API_BASE_URL||"http://localhost:8000/api/v1")+"/reports/"+id+"/download";
 return <main className="orders"><header><a href="/">NOVA DealSense</a><a href={"/deals/"+report.source.deal.id+"/scenarios"}>返回方案对比</a></header><h1>{report.title}</h1><p>{report.report_number} · {new Date(report.generated_at).toLocaleString("zh-CN")} · {report.demo_inputs?"演示输入":"已保存报告"}</p><a className="action" href={url}>下载 PDF</a>{report.sections.map(s=><section key={s.title} className="panel"><h2>{s.title}</h2><dl>{s.rows.map(([k,v],i)=><div key={i} className="row"><dt>{k}</dt><dd>{v}</dd></div>)}</dl></section>)}</main>
}
