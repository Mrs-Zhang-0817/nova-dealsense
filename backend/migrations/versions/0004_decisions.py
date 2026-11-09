from sqlalchemy import Column, Uuid, String, DateTime, ForeignKey, JSON, LargeBinary, func
from alembic import op
revision="0004"
down_revision="0003"

def upgrade():
    op.add_column("deals", Column("data_origin", String(), nullable=False, server_default="unknown"))
    op.execute("""UPDATE deals SET data_origin='demo' WHERE name LIKE '%演示%' AND exchange_rates::text LIKE '%演示%'""")
    op.create_table("decision_selections",
        Column("id", Uuid(), primary_key=True),
        Column("deal_id", Uuid(), ForeignKey("deals.id", ondelete="SET NULL"), nullable=True),
        Column("optimization_run_id", Uuid(), ForeignKey("optimization_runs.id"), nullable=False),
        Column("scenario_id", Uuid(), ForeignKey("scenarios.id"), nullable=False),
        Column("selected_by", String(), nullable=False),
        Column("selection_note", String(), nullable=False),
        Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False))
    op.create_table("decision_reports",
        Column("id", Uuid(), primary_key=True),
        Column("decision_selection_id", Uuid(), ForeignKey("decision_selections.id"), nullable=False),
        Column("report_number", String(), unique=True, nullable=False),
        Column("report_snapshot", JSON(), nullable=False),
        Column("pdf", LargeBinary(), nullable=False),
        Column("created_at", DateTime(timezone=True), server_default=func.now(), nullable=False))

def downgrade():
    op.drop_table("decision_reports")
    op.drop_table("decision_selections")
    op.drop_column("deals","data_origin")
