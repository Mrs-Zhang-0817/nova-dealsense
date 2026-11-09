from sqlalchemy import Column, String, JSON, Uuid, ForeignKey, Integer, DateTime, func
from alembic import op
revision="0003"
down_revision="0002"

def upgrade():
    op.create_table("optimization_runs",
        Column("id", Uuid(), primary_key=True),
        Column("deal_id", Uuid(), ForeignKey("deals.id", ondelete="SET NULL"), nullable=True),
        Column("objective", String(), nullable=False),
        Column("status", String(), nullable=False),
        Column("algorithm_version", String(), nullable=False),
        Column("input_snapshot", JSON(), nullable=False),
        Column("calculation_snapshot", JSON(), nullable=False),
        Column("completed_at", DateTime(timezone=True), nullable=False),
        Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False))
    op.create_table("scenarios",
        Column("id", Uuid(), primary_key=True),
        Column("optimization_run_id", Uuid(), ForeignKey("optimization_runs.id", ondelete="CASCADE"), nullable=False),
        Column("position", Integer(), nullable=False),
        Column("result", JSON(), nullable=False),
        Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False))

def downgrade():
    op.drop_table("scenarios")
    op.drop_table("optimization_runs")
