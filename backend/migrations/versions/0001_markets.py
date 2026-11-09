from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None

def upgrade():
    markets = op.create_table("markets",
        sa.Column("country_code", sa.String(2), primary_key=True),
        sa.Column("country_name_zh", sa.String(), nullable=False),
        sa.Column("country_name_en", sa.String(), nullable=False),
        sa.Column("default_currency", sa.String(3), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.Column("rules_status", sa.String(), nullable=False))
    for code, zh, en, currency in [("CN","中国","China","CNY"), ("US","美国","United States","USD")]:
        op.bulk_insert(markets, [dict(country_code=code, country_name_zh=zh, country_name_en=en,
            default_currency=currency, is_enabled=True, rules_status="unconfigured")])

def downgrade():
    op.drop_table("markets")
