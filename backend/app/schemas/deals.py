from datetime import date
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, model_validator

Country = Annotated[str, Field(pattern=r"^[A-Z]{2}$")]
Currency = Annotated[str, Field(pattern=r"^[A-Z]{3}$")]
Name = Annotated[str, Field(min_length=1, max_length=240)]
Amount = Annotated[Decimal, Field(ge=0, max_digits=18, decimal_places=8)]
Positive = Annotated[Decimal, Field(gt=0, max_digits=18, decimal_places=8)]

class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

class BuyerIn(Input):
    company_name: Name
    country_code: Country
    contact_name: str | None = None
    email: str | None = Field(None, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    notes: str | None = None

class ProductIn(Input):
    name: Name
    sku: Name
    unit: Name
    hs_code: str | None = None
    description: str | None = None
    default_cost: Amount | None = None
    default_cost_currency: Currency | None = None

    @model_validator(mode="after")
    def cost_pair(self):
        if (self.default_cost is None) != (self.default_cost_currency is None):
            raise ValueError("默认成本和币种必须一起填写")
        return self

class Rate(Input):
    base: Currency
    quote: Currency
    rate: Positive
    date: date
    source: Name

class Item(Input):
    product_id: UUID | None = None
    product: ProductIn | None = None
    quantity: Positive
    unit_price: Amount
    unit_price_currency: Currency
    unit_manufacturing_cost: Amount
    cost_currency: Currency
    manufacturing_confirmed: bool = True

class Cost(Input):
    cost_type: Literal["packaging","logistics","insurance","other"]
    description: str | None = None
    amount: Amount
    currency: Currency
    source_type: Name = "manual"
    source_reference: str | None = None
    confirmed: bool
    included: bool = True

class Limit(Input):
    constraint_type: Name
    operator: Literal["<=",">=","="]
    value: Decimal
    unit: Name
    is_hard: bool
    description: str | None = None

class DealIn(Input):
    data_origin: Literal["unknown","actual","demo"] = "unknown"
    name: Name
    buyer_id: UUID | None = None
    buyer: BuyerIn | None = None
    origin_country: Country
    destination_country: Country
    currency: Currency
    incoterm: Literal["EXW","FCA","FAS","FOB","CFR","CIF","CPT","CIP","DAP","DPU","DDP"]
    status: Literal["draft","confirmed","closed"] = "draft"
    requested_deadline: date | None = None
    customer_target_price: Amount | None = None
    target_margin: Annotated[Decimal, Field(ge=0,le=1)] | None = None
    notes: str | None = None
    items: list[Item] = Field(min_length=1)
    costs: list[Cost] = Field(default_factory=list)
    constraints: list[Limit] = Field(default_factory=list)
    exchange_rates: list[Rate] = Field(default_factory=list)

