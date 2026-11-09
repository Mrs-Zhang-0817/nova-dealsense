from decimal import Decimal, ROUND_HALF_UP, localcontext
from app.schemas.deals import DealIn

def calculate(deal: DealIn):
    """Round each extended line to eight decimal places in the reporting currency."""
    rates = {}
    for fx in deal.exchange_rates:
        key = (fx.base, fx.quote)
        if fx.base == fx.quote or key in rates or key[::-1] in rates:
            raise ValueError("汇率币种对重复或相同")
        rates[key] = fx.rate

    def convert(amount, currency):
        target = deal.currency
        if currency == target:
            value = amount
        elif (currency, target) in rates:
            value = amount * rates[currency, target]
        elif (target, currency) in rates:
            value = amount / rates[target, currency]
        else:
            raise ValueError(f"缺少 {currency} 与 {target} 的汇率")
        return value.quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)

    with localcontext() as ctx:
        ctx.prec = 80
        lines = [(convert(i.quantity*i.unit_price,i.unit_price_currency),
                  convert(i.quantity*i.unit_manufacturing_cost,i.cost_currency)) for i in deal.items]
        costs = [convert(c.amount,c.currency) for c in deal.costs]
        revenue = sum((r for r,_ in lines), Decimal(0))
        manufacturing = sum((m for (_,m),i in zip(lines,deal.items) if i.manufacturing_confirmed),Decimal(0))
        extra = sum((a for a,c in zip(costs,deal.costs) if c.confirmed and c.included),Decimal(0))
        total = manufacturing + extra
        profit = revenue - total
        return lines, costs, dict(revenue=revenue,manufacturing_cost=manufacturing,additional_costs=extra,
            total_included_cost=total,contribution_profit=profit,
            contribution_margin=(profit/revenue if revenue else None),
            contribution_margin_percent=((profit*100/revenue).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if revenue else None),
            has_estimates=any(not i.manufacturing_confirmed for i in deal.items) or any(c.included and not c.confirmed for c in deal.costs))

