import uuid
from sqlalchemy import Column, Uuid, String, DateTime, ForeignKey, JSON, LargeBinary, func
from app.core.database import Base

class Selection(Base):
    __tablename__ = "decision_selections"
    id = Column(Uuid(), primary_key=True, default=uuid.uuid4)
    deal_id = Column(Uuid(), ForeignKey("deals.id", ondelete="SET NULL"), nullable=True)
    optimization_run_id = Column(Uuid(), ForeignKey("optimization_runs.id"), nullable=False)
    scenario_id = Column(Uuid(), ForeignKey("scenarios.id"), nullable=False)
    selected_by = Column(String(), nullable=False)
    selection_note = Column(String(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class DecisionReport(Base):
    __tablename__ = "decision_reports"
    id = Column(Uuid(), primary_key=True, default=uuid.uuid4)
    decision_selection_id = Column(Uuid(), ForeignKey("decision_selections.id"), nullable=False)
    report_number = Column(String(), unique=True, nullable=False)
    report_snapshot = Column(JSON(), nullable=False)
    pdf = Column(LargeBinary(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
