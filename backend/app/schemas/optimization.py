from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID
from pydantic import Field, model_validator
from app.schemas.deals import Input, Name, Amount, Positive

Count = Annotated[int, Field(gt=0, le=10**9)]
Days = Annotated[int, Field(ge=0, le=10**9)]

class Shipping(Input):
    name: Name
    days: Days
    replacement_cost: Amount | None = None

class Optimization(Input):
    deal_id: UUID
    objective: Literal["PROFIT_FIRST","BUYER_FIT","LOW_RISK"]
    target_margin: Annotated[Amount, Field(lt=1)]
    minimum_profit: Amount
    price_min: Positive
    price_max: Positive
    price_step: Positive
    quantity_min: Count
    quantity_max: Count
    quantity_step: Count
    production_capacity: Count
    delivery_deadline_days: Count
    customer_unit_price_ceiling: Amount | None = None
    customer_total_budget: Amount | None = None
    minimum_order_quantity: Count | None = None
    setup_days: Days | None = None
    production_units_per_day: Count | None = None
    shipping_options: list[Shipping] = Field(default_factory=list,max_length=32)
    additional_cost_adjustments: dict[str,Literal["fixed","per_unit"]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def bounds(self):
        if self.price_min>self.price_max or self.quantity_min>self.quantity_max:
            raise ValueError("协商范围的下限超过上限")
        if len(set(s.name for s in self.shipping_options)) != len(self.shipping_options):
            raise ValueError("物流方案名称重复")
        return self
