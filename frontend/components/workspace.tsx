"use client";
import {useEffect, useState} from "react";
import zh from "@/messages/zh-CN.json";
import en from "@/messages/en.json";
import {checkHealth} from "@/services/api";
import {DecisionDashboard} from "./decision-dashboard";
import {Button} from "./ui/button";

export function Workspace() {
  const [english, setEnglish] = useState(false);
  const [status, setStatus] = useState<"checking"|"online"|"offline">("checking");
  const [attempt, setAttempt] = useState(0);
  const t = english ? en : zh;
  useEffect(() => { document.documentElement.lang = english ? "en" : "zh-CN"; }, [english]);
  useEffect(() => {
    const controller = new AbortController();
    setStatus("checking");
    checkHealth(controller.signal).then(ok => setStatus(ok ? "online" : "offline"))
      .catch(() => { if (!controller.signal.aborted) setStatus("offline"); });
    return () => controller.abort();
  }, [attempt]);
  return <main><header><strong>{t.brand}</strong><a href="/optimizer">{t.names[3]}</a><a href="/deals">{t.names[1]}</a><Button onClick={()=>setEnglish(!english)}>{t.switch}</Button></header>
    <section><small>{t.workspace}</small><h1>{t.title}</h1><p>{t.intro}</p></section>
    <article><div><small>{t.market}</small><h2>{t.route}</h2></div><div><small>{t.connection}</small><p role="status" className={status}>{t[status]}</p>
    {status === "offline" && <Button onClick={()=>setAttempt(attempt+1)}>{t.retry}</Button>}</div></article>
    <div id="overview"><DecisionDashboard english={english}/></div><h2>{t.modules}</h2><ul>{t.names.map((name,i)=><li key={name}><a href={["#overview","/deals","/deals","/optimizer","/deals","/deals"][i]}>{name}</a></li>)}</ul></main>;
}




