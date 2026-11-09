"""Read decoded JSON source values when identifying earlier bottle demo fixtures."""
from alembic import op

revision="0005"
down_revision="0004"

def upgrade():
    op.execute("""
        UPDATE deals AS d SET data_origin='demo'
        WHERE d.data_origin='unknown' AND d.name LIKE '%演示%'
        AND EXISTS (SELECT 1 FROM json_array_elements(d.exchange_rates) AS rate
                    WHERE rate->>'source'='手工演示汇率')
    """)

def downgrade():
    # Origin is editable business data. Preserve later user corrections.
    pass
