import uuid
from sqlalchemy import Column, String, Text, Date, Numeric, DateTime, Boolean, JSON, Uuid, ForeignKey, func
from app.core.database import Base


class Buyer(Base):
    __tablename__ = "buyers"
    id = Column(Uuid(), primary_key=True, default=uuid.uuid4)
    company_name = Column(String(), nullable=False)
    country_code = Column(String(2), ForeignKey("markets.country_code"), nullable=False)
    contact_name = Column(String(), nullable=True)
    email = Column(String(), nullable=True)
    notes = Column(Text(), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class Product(Base):
    __tablename__ = "products"
    id = Column(Uuid(), primary_key=True, default=uuid.uuid4)
    name = Column(String(), nullable=False)
    sku = Column(String(), nullable=False, unique=True)
    hs_code = Column(String(), nullable=True)
    description = Column(Text(), nullable=True)
    unit = Column(String(), nullable=False)
    default_cost = Column(Numeric(), nullable=True)
    default_cost_currency = Column(String(3), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class Deal(Base):
    __tablename__ = "deals"
    data_origin = Column(String(), nullable=False, server_default="unknown")
    id = Column(Uuid(), primary_key=True, default=uuid.uuid4)
    deal_number = Column(String(), nullable=False, unique=True)
    name = Column(String(), nullable=False)
    buyer_id = Column(Uuid(), ForeignKey("buyers.id"), nullable=False)
    origin_country = Column(String(2), ForeignKey("markets.country_code"), nullable=False)
    destination_country = Column(String(2), ForeignKey("markets.country_code"), nullable=False)
    currency = Column(String(3), nullable=False)
    incoterm = Column(String(), nullable=False)
    status = Column(String(), nullable=False)
    requested_deadline = Column(Date(), nullable=True)
    customer_target_price = Column(Numeric(), nullable=True)
    target_margin = Column(Numeric(), nullable=True)
    notes = Column(Text(), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    exchange_rates = Column(JSON(), nullable=False)


class DealItem(Base):
    __tablename__ = "deal_items"
    id = Column(Uuid(), primary_key=True, default=uuid.uuid4)
    deal_id = Column(Uuid(), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Uuid(), ForeignKey("products.id"), nullable=False)
    product_name_snapshot = Column(String(), nullable=False)
    sku_snapshot = Column(String(), nullable=False)
    quantity = Column(Numeric(), nullable=False)
    unit_price = Column(Numeric(), nullable=False)
    unit_price_currency = Column(String(3), nullable=False)
    unit_manufacturing_cost = Column(Numeric(), nullable=False)
    cost_currency = Column(String(3), nullable=False)
    unit = Column(String(), nullable=False)
    converted_revenue = Column(Numeric(), nullable=False)
    converted_manufacturing_cost = Column(Numeric(), nullable=False)
    manufacturing_confirmed = Column(Boolean(), nullable=False)


class CostItem(Base):
    __tablename__ = "cost_items"
    id = Column(Uuid(), primary_key=True, default=uuid.uuid4)
    deal_id = Column(Uuid(), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False)
    cost_type = Column(String(), nullable=False)
    description = Column(Text(), nullable=True)
    amount = Column(Numeric(), nullable=False)
    currency = Column(String(3), nullable=False)
    source_type = Column(String(), nullable=False)
    source_reference = Column(String(), nullable=True)
    confirmed = Column(Boolean(), nullable=False)
    included = Column(Boolean(), nullable=False)
    converted_amount = Column(Numeric(), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Constraint(Base):
    __tablename__ = "constraints"
    id = Column(Uuid(), primary_key=True, default=uuid.uuid4)
    deal_id = Column(Uuid(), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False)
    constraint_type = Column(String(), nullable=False)
    operator = Column(String(), nullable=False)
    value = Column(Numeric(), nullable=False)
    unit = Column(String(), nullable=False)
    is_hard = Column(Boolean(), nullable=False)
    description = Column(Text(), nullable=True)

