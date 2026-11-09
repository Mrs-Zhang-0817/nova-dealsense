import uuid
from sqlalchemy import Column, String, JSON, Uuid, ForeignKey, Integer, DateTime, func
from app.core.database import Base

class OptimizationRun(Base):
    __tablename__ = "optimization_runs"
    id = Column(Uuid(), primary_key=True, default=uuid.uuid4)
    deal_id = Column(Uuid(), ForeignKey("deals.id", ondelete="SET NULL"), nullable=True)
    objective = Column(String(), nullable=False)
    status = Column(String(), nullable=False)
    algorithm_version = Column(String(), nullable=False)
    input_snapshot = Column(JSON(), nullable=False)
    calculation_snapshot = Column(JSON(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class Scenario(Base):
    __tablename__ = "scenarios"
    id = Column(Uuid(), primary_key=True, default=uuid.uuid4)
    optimization_run_id = Column(Uuid(), ForeignKey("optimization_runs.id", ondelete="CASCADE"), nullable=False)
    position = Column(Integer(), nullable=False)
    result = Column(JSON(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
