"""Deal management schema."""
from alembic import op
from sqlalchemy import Column, String, Text, Date, Numeric, DateTime, Boolean, JSON, Uuid, ForeignKey, func

revision = "0002"
down_revision = "0001"

def upgrade():
    op.create_table("buyers",
        Column("id", Uuid(), primary_key=True),
        Column("company_name", String(), nullable=False),
        Column("country_code", String(2), ForeignKey("markets.country_code"), nullable=False),
        Column("contact_name", String(), nullable=True),
        Column("email", String(), nullable=True),
        Column("notes", Text(), nullable=True),
        Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
        Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now())
    )
    op.create_table("products",
        Column("id", Uuid(), primary_key=True),
        Column("name", String(), nullable=False),
        Column("sku", String(), nullable=False, unique=True),
        Column("hs_code", String(), nullable=True),
        Column("description", Text(), nullable=True),
        Column("unit", String(), nullable=False),
        Column("default_cost", Numeric(), nullable=True),
        Column("default_cost_currency", String(3), nullable=True),
        Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
        Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now())
    )
    op.create_table("deals",
        Column("id", Uuid(), primary_key=True),
        Column("deal_number", String(), nullable=False, unique=True),
        Column("name", String(), nullable=False),
        Column("buyer_id", Uuid(), ForeignKey("buyers.id"), nullable=False),
        Column("origin_country", String(2), ForeignKey("markets.country_code"), nullable=False),
        Column("destination_country", String(2), ForeignKey("markets.country_code"), nullable=False),
        Column("currency", String(3), nullable=False),
        Column("incoterm", String(), nullable=False),
        Column("status", String(), nullable=False),
        Column("requested_deadline", Date(), nullable=True),
        Column("customer_target_price", Numeric(), nullable=True),
        Column("target_margin", Numeric(), nullable=True),
        Column("notes", Text(), nullable=True),
        Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
        Column("updated_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
        Column("exchange_rates", JSON(), nullable=False)
    )
    op.create_table("deal_items",
        Column("id", Uuid(), primary_key=True),
        Column("deal_id", Uuid(), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False),
        Column("product_id", Uuid(), ForeignKey("products.id"), nullable=False),
        Column("product_name_snapshot", String(), nullable=False),
        Column("sku_snapshot", String(), nullable=False),
        Column("quantity", Numeric(), nullable=False),
        Column("unit_price", Numeric(), nullable=False),
        Column("unit_price_currency", String(3), nullable=False),
        Column("unit_manufacturing_cost", Numeric(), nullable=False),
        Column("cost_currency", String(3), nullable=False),
        Column("unit", String(), nullable=False),
        Column("converted_revenue", Numeric(), nullable=False),
        Column("converted_manufacturing_cost", Numeric(), nullable=False),
        Column("manufacturing_confirmed", Boolean(), nullable=False)
    )
    op.create_table("cost_items",
        Column("id", Uuid(), primary_key=True),
        Column("deal_id", Uuid(), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False),
        Column("cost_type", String(), nullable=False),
        Column("description", Text(), nullable=True),
        Column("amount", Numeric(), nullable=False),
        Column("currency", String(3), nullable=False),
        Column("source_type", String(), nullable=False),
        Column("source_reference", String(), nullable=True),
        Column("confirmed", Boolean(), nullable=False),
        Column("included", Boolean(), nullable=False),
        Column("converted_amount", Numeric(), nullable=False),
        Column("created_at", DateTime(timezone=True), nullable=False, server_default=func.now())
    )
    op.create_table("constraints",
        Column("id", Uuid(), primary_key=True),
        Column("deal_id", Uuid(), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False),
        Column("constraint_type", String(), nullable=False),
        Column("operator", String(), nullable=False),
        Column("value", Numeric(), nullable=False),
        Column("unit", String(), nullable=False),
        Column("is_hard", Boolean(), nullable=False),
        Column("description", Text(), nullable=True)
    )

def downgrade():
    op.drop_table("constraints")
    op.drop_table("cost_items")
    op.drop_table("deal_items")
    op.drop_table("deals")
    op.drop_table("products")
    op.drop_table("buyers")
