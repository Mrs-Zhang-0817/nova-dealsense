from decimal import Decimal as D, ROUND_CEILING, localcontext
from app.schemas.deals import DealIn, Item, Cost
from app.schemas.optimization import Optimization
from app.services.finance import calculate

VERSION = "enum-1.0"
LIMIT = 1000

def reverse_price(cost, q, margin, step, floor):
    if q<=0 or not 0<=margin<1 or step<=0:
        raise ValueError("数量、步长或目标贡献率无效")
    with localcontext() as ctx:
        ctx.prec=80
        raw=cost/(D(q)*(1-margin))
        return floor+max(D(0),((raw-floor)/step).to_integral_value(rounding=ROUND_CEILING))*step

def validate(a, price, q, days, metrics):
    checks={}
    def record(key, actual, bound, passed):
        checks[key]=dict(actual=actual,limit=bound,passed=passed)
    record("margin",metrics["contribution_margin"],a.target_margin,metrics["contribution_margin"]>=a.target_margin)
    record("profit",metrics["contribution_profit"],a.minimum_profit,metrics["contribution_profit"]>=a.minimum_profit)
    record("capacity",q,a.production_capacity,q<=a.production_capacity)
    record("quantity_range",q,[a.quantity_min,a.quantity_max],a.quantity_min<=q<=a.quantity_max)
    record("deadline",days,a.delivery_deadline_days,days<=a.delivery_deadline_days)
    if a.minimum_order_quantity is not None:
        record("moq",q,a.minimum_order_quantity,q>=a.minimum_order_quantity)
    if a.customer_unit_price_ceiling is not None:
        record("unit_ceiling",price,a.customer_unit_price_ceiling,price<=a.customer_unit_price_ceiling)
    if a.customer_total_budget is not None:
        record("budget",metrics["revenue"],a.customer_total_budget,metrics["revenue"]<=a.customer_total_budget)
    return checks

def candidate_costs(s,a,ship,q,original,currency):
    costs=[]
    for c in s["costs"]:
        if not c["included"] or (ship.replacement_cost is not None and c["cost_type"]=="logistics"):
            continue
        cost=Cost(**{k:v for k,v in c.items() if k in Cost.model_fields})
        if a.additional_cost_adjustments.get(str(c["id"]))=="per_unit":
            cost=cost.model_copy(update={"amount":cost.amount*q/original})
        costs.append(cost)
    if ship.replacement_cost is not None:
        costs.append(Cost(cost_type="logistics",amount=ship.replacement_cost,currency=currency,confirmed=True))
    return costs

def evaluate(snapshot, a:Optimization):
    with localcontext() as ctx:
        ctx.prec=80
        return search(snapshot,a)

def search(s,a):
    problems=[]
    if len(s["items"])!=1:
        problems.append("需要单商品订单")
    if any(not i["manufacturing_confirmed"] for i in s["items"]) or any(c["included"] and not c["confirmed"] for c in s["costs"]):
        problems.append("存在未确认的纳入成本")
    if any(c["is_hard"] for c in s["constraints"]):
        problems.append("原订单含尚未映射的自定义硬约束")
    if a.setup_days is None or a.production_units_per_day is None or not a.shipping_options:
        problems.append("请补充准备天数、日产能和物流方案")
    if set(a.additional_cost_adjustments)-{str(c["id"]) for c in s["costs"]}:
        raise ValueError("成本行为引用了不存在的成本行")
    if len(s["items"])==1:
        original=D(s["items"][0]["quantity"])
        if a.quantity_min!=original or a.quantity_max!=original:
            for c in s["costs"]:
                replaced=c["cost_type"]=="logistics" and all(o.replacement_cost is not None for o in a.shipping_options)
                if c["included"] and not replaced and str(c["id"]) not in a.additional_cost_adjustments:
                    problems.append("缺少数量变化时的成本行为："+str(c["id"]))
    def incomplete(messages):
        return dict(status="INSUFFICIENT_DATA",diagnostics=messages,truncated=False,evaluated=0,data_complete=False),[]
    if problems:
        return incomplete(problems)
    row=s["items"][0]
    item=Item(**{k:v for k,v in row.items() if k in Item.model_fields})
    base=DealIn(**{k:v for k,v in s.items() if k in DealIn.model_fields and k not in ("buyer","items","costs","constraints")},items=[item])
    try:
        orig_revenue=calculate(base)[2]["revenue"]
    except ValueError as exc:
        return incomplete([str(exc)])
    ref_price=D(s["customer_target_price"]) if s.get("customer_target_price") is not None else orig_revenue/original
    if a.objective=="BUYER_FIT" and ref_price<=0:
        return incomplete(["缺少正值的客户参考单价"])
    prices=int((a.price_max-a.price_min)//a.price_step)+1
    grid=prices*((a.quantity_max-a.quantity_min)//a.quantity_step+1)*len(a.shipping_options)
    candidates=[]
    violations={}
    for q in range(a.quantity_min,a.quantity_max+1,a.quantity_step):
        for ship in a.shipping_options:
            costs=candidate_costs(s,a,ship,q,original,base.currency)
            production=a.setup_days+(q+a.production_units_per_day-1)//a.production_units_per_day
            days=production+ship.days
            for n in range(min(prices,LIMIT-len(candidates))):
                price=a.price_min+n*a.price_step
                changed=item.model_copy(update=dict(quantity=D(q),unit_price=price,unit_price_currency=base.currency))
                try:
                    metrics=calculate(base.model_copy(update=dict(items=[changed],costs=costs)))[2]
                except ValueError as exc:
                    return incomplete([str(exc)])
                checks=validate(a,price,q,days,metrics)
                failed=[k for k,v in checks.items() if not v["passed"]]
                for k in failed:
                    violations[k]=violations.get(k,0)+1
                score=-metrics["contribution_profit"]
                if a.objective=="LOW_RISK":
                    score=(D(q)/a.production_capacity+D(days)/a.delivery_deadline_days)/2
                elif a.objective=="BUYER_FIT":
                    score=(abs(price-ref_price)/ref_price+abs(q-original)/original+D(abs(days-a.delivery_deadline_days))/a.delivery_deadline_days)/3
                candidates.append(dict(price=price,quantity=q,shipping=ship.name,production_days=production,delivery_days=days,
                    minimum_margin_price=reverse_price(metrics["total_included_cost"],q,a.target_margin,a.price_step,a.price_min),
                    financials=metrics,constraint_results=checks,feasibility="INFEASIBLE" if failed else "FEASIBLE",score=score))
            if len(candidates)>=LIMIT: break
        if len(candidates)>=LIMIT: break
    candidates.sort(key=lambda r:(r["feasibility"]!="FEASIBLE",r["score"],-r["financials"]["contribution_profit"],r["price"],r["quantity"],r["shipping"]))
    truncated=grid>len(candidates)
    status="FEASIBLE" if candidates[0]["feasibility"]=="FEASIBLE" else "INSUFFICIENT_DATA" if truncated else "INFEASIBLE"
    return dict(status=status,data_complete=True,diagnostics=violations,truncated=truncated,grid_size=grid,evaluated=len(candidates)),candidates

