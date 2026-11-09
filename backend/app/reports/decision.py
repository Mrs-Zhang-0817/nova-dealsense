from decimal import Decimal as D, localcontext
from app.schemas.optimization import Optimization
from app.schemas.deals import DealIn
from app.optimization.engine import candidate_costs
from app.services.finance import calculate

OBJECTIVES={"PROFIT_FIRST":"利润优先","BUYER_FIT":"买家匹配","LOW_RISK":"低风险"}
RULES={"PROFIT_FIRST":"按预计贡献利润从高到低排列","BUYER_FIT":"按单价、数量、交期相对客户参考条件的平均偏差从低到高排列","LOW_RISK":"按产能占用率和交期占用率的平均值从低到高排列；该指标为代理分数"}
CHECKS={"margin":"贡献率","profit":"贡献利润","capacity":"总产能","quantity_range":"协商数量","deadline":"交期","moq":"起订量","unit_ceiling":"客户单价上限","budget":"客户总预算"}
TITLE="NOVA DealSense — 跨境交易决策分析报告"

def fmt(value):
    s=format(D(str(value)),",f")
    return s.rstrip("0").rstrip(".") if "." in s else s

def present(run,row):
    r=row.result
    p=run.input_snapshot["parameters"]
    util=D(r["quantity"])*100/D(p["production_capacity"])
    facts=[CHECKS[k]+("达标" if v["passed"] else "未达标") for k,v in r["constraint_results"].items()]
    return dict(**r,id=str(row.id),name=f"方案 {row.position+1}",position=row.position,
                utilization=str(util.quantize(D(".01"))),slack=p["delivery_deadline_days"]-r["delivery_days"],
                explanation=dict(facts=facts,assumptions=f"总产能 {p['production_capacity']} 件，交期 {p['delivery_deadline_days']} 天",
                ranking=RULES[run.objective]+(f"，已评估可行候选中第 {row.position+1} 名" if r["feasibility"]=="FEASIBLE" else "；本方案未通过约束")))

def snapshot(run,chosen,alternatives,selection,number,generated):
    source=run.input_snapshot
    deal=source["deal"]
    item=deal["items"][0]
    p=Optimization(**source["parameters"])
    currency=deal["currency"]
    money=lambda x:currency+" "+fmt(x)
    f=chosen["financials"]
    ship=next(s for s in p.shipping_options if s.name==chosen["shipping"])
    with localcontext() as ctx:
        ctx.prec=80
        costs=candidate_costs(deal,p,ship,chosen["quantity"],D(item["quantity"]),currency)
        args={k:v for k,v in deal.items() if k in DealIn.model_fields and k not in ("items","costs","buyer","constraints")}
        from app.schemas.deals import Rate
        args["exchange_rates"]=[Rate(**r) for r in deal["exchange_rates"]]
        base=DealIn.model_construct(**args,items=[],costs=costs)
        totals=calculate(base)[1]
        logistics=sum((val for c,val in zip(costs,totals) if c.cost_type=="logistics" and c.confirmed),D(0))
    summary=run.calculation_snapshot
    demo=deal.get("data_origin")=="demo" or any("演示" in r["source"] for r in deal["exchange_rates"])
    warnings=["运费、准备天数、日产能和运输时间按人工输入，未经承运商或工厂核验。",
              "关税、目的地税费未逐项核验；贡献利润未扣除所有企业层面费用。",
              "市场规则覆盖："+"、".join(m["country_code"]+" "+("未配置" if m["rules_status"]=="unconfigured" else m["rules_status"]) for m in source["markets"])]
    if summary["truncated"]: warnings.append("搜索已截断，排序仅覆盖已检查的候选。")
    excluded=[c for c in deal["costs"] if not c["confirmed"] or not c["included"]]
    if excluded:warnings.append(f"原订单含 {len(excluded)} 项未确认或排除的费用，详情见成本快照。")
    if demo:warnings.append("演示数据：汇率、产能及交付条件用于模拟，不代表实际客户承诺。")
    def section(title,*rows):
        return {"title":title,"rows":[[k,str(v)] for k,v in rows]}
    target=deal["customer_target_price"]
    comparisons=[chosen]+alternatives
    sections=[
        section("01　执行摘要",("订单",deal["name"]),("贸易路线",deal["origin_country"]+" → "+deal["destination_country"]),("所选可行方案",chosen["name"]+" · "+chosen["shipping"]),("预计贡献利润",money(f["contribution_profit"])),("预计贡献率",f["contribution_margin_percent"]+"%"),("结论","按冻结输入，所选方案满足全部已建模硬约束。")),
        section("02　订单概览",("买家",deal["buyer"]["company_name"]),("商品",item["product_name_snapshot"]),("原始数量",fmt(item["quantity"])+" "+item["unit"]),("原订单报价",item["unit_price_currency"]+" "+fmt(item["unit_price"])),("客户目标单价",money(target) if target is not None else "未提供"),("目的市场 / 贸易术语",deal["destination_country"]+" / "+deal["incoterm"])),
        section("03　财务分析",("预计销售收入",money(f["revenue"])),("预计制造成本",money(f["manufacturing_cost"])),("单列物流成本",money(logistics)),("其他纳入成本",money(D(f["additional_costs"])-logistics)),("预计总成本",money(f["total_included_cost"])),("预计贡献利润 / 贡献率",money(f["contribution_profit"])+" / "+f["contribution_margin_percent"]+"%")),
        section("04　优化方法",("排序目标 / 算法版本",OBJECTIVES[run.objective]+" / "+run.algorithm_version),("报价范围",f"{currency} {p.price_min} 至 {p.price_max}，步长 {p.price_step}"),("数量范围",f"{p.quantity_min} 至 {p.quantity_max}，步长 {p.quantity_step}"),("可选物流","、".join(s.name for s in p.shipping_options)),("目标贡献率 / 最低利润",fmt(p.target_margin*100)+"% / "+money(p.minimum_profit)),("搜索范围",f"已检查 {summary['evaluated']} / {summary['grid_size']} 个候选，"+("已截断" if summary["truncated"] else "已遍历全部网格")),("约束验证","、".join(chosen["explanation"]["facts"]))),
        section("05　方案对比",*((s["name"],f"报价 {money(s['price'])}，数量 {s['quantity']}，{s['shipping']}，交付 {s['delivery_days']} 天；预计贡献利润 {money(s['financials']['contribution_profit'])}，贡献率 {s['financials']['contribution_margin_percent']}%") for s in comparisons)),
        section("06　决策依据",("算法排序",chosen["explanation"]["ranking"]),("产能占用 / 交付余量",chosen["utilization"]+f"% / {chosen['slack']} 天"),("达到目标贡献率的最低报价",money(chosen["minimum_margin_price"])),("人工选择",selection.selected_by),("选择说明",selection.selection_note or "未填写")),
        section("07　风险与局限",*((str(i+1),w) for i,w in enumerate(warnings))),
        section("08　数据来源与假设",("记录性质","演示输入" if demo else {"actual":"用户标注的真实业务"}.get(deal.get("data_origin"),"未标注来源")),("生产假设",f"总产能 {p.production_capacity}，日产能 {p.production_units_per_day}，准备 {p.setup_days} 天"),("物流假设",f"{ship.name}，运输 {ship.days} 天，客户交期 {p.delivery_deadline_days} 天"),("费用来源","、".join((c["description"] or c["cost_type"])+" / "+("人工录入" if c["source_type"]=="manual" else c["source_type"]) for c in deal["costs"]) or "无附加成本行"),*((r["date"],f"1 {r['base']} = {r['rate']} {r['quote']}，来源：{r['source']}") for r in deal["exchange_rates"]))]
    return dict(title=TITLE,report_number=number,generated_at=generated,currency=currency,sections=sections,
                source=source,algorithm_version=run.algorithm_version,calculation=summary,objective=run.objective,
                selected=chosen,alternatives=alternatives,warnings=warnings,selection_id=str(selection.id),demo_inputs=demo)
