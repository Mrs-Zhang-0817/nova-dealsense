from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from .business import DB, fields, lookup, encode, detail
from app.models.business import Deal
from app.models.market import Market
from app.models.optimization import OptimizationRun, Scenario
from app.schemas.optimization import Optimization
from app.optimization.engine import VERSION, evaluate

router=APIRouter()

def saved(db,run):
    query=select(Scenario.result).where(Scenario.optimization_run_id==run.id).order_by(Scenario.position)
    preview=db.scalars(query.limit(6)).all()
    feasible=[r for r in preview if r["feasibility"]=="FEASIBLE"]
    return dict(run_id=run.id,objective=run.objective,algorithm_version=run.algorithm_version,
                **run.calculation_snapshot,recommended=next(iter(feasible),None),alternatives=feasible[1:],
                example_rejection=next((r for r in preview if r["feasibility"]=="INFEASIBLE"),None))

@router.post("/deals/{id}/optimize",status_code=201)
def optimize(id:UUID,data:Optimization,db:Session=DB):
    if data.deal_id!=id:
        raise HTTPException(422,"请求中的订单编号不一致")
    deal=db.get(Deal,id,with_for_update=True)
    if not deal:
        raise HTTPException(404,"订单不存在")
    snapshot=detail(db,deal,with_financials=False)
    markets=[fields(lookup(db,Market,code)) for code in sorted({deal.origin_country,deal.destination_country})]
    summary,results=evaluate(snapshot,data)
    run=OptimizationRun(deal_id=id,objective=data.objective,status=summary["status"],algorithm_version=VERSION,
        input_snapshot=dict(deal=snapshot,markets=markets,parameters=data.model_dump(mode="json"),
            selection="quantity, shipping input order, price; limit 1000; objective score then profit, price, quantity, name"),
        calculation_snapshot=encode(summary),completed_at=datetime.now(timezone.utc))
    db.add(run)
    db.flush()
    db.add_all([Scenario(optimization_run_id=run.id,position=i,result=encode(r)) for i,r in enumerate(results)])
    db.flush()
    response=saved(db,run)
    db.commit()
    return response

@router.get("/optimization/{run_id}")
def read(run_id:UUID,db:Session=DB):
    run=lookup(db,OptimizationRun,run_id)
    return dict(**saved(db,run),input_snapshot=run.input_snapshot)

@router.get("/optimization/{run_id}/scenarios")
def scenarios(run_id:UUID,offset:int=Query(0,ge=0),limit:int=Query(100,ge=1,le=1000),db:Session=DB):
    lookup(db,OptimizationRun,run_id)
    return db.scalars(select(Scenario.result).where(Scenario.optimization_run_id==run_id)
        .order_by(Scenario.position).offset(offset).limit(limit)).all()

@router.get("/deals/{id}/optimization-history")
def history(id:UUID,db:Session=DB):
    lookup(db,Deal,id)
    runs=db.scalars(select(OptimizationRun).where(OptimizationRun.deal_id==id).order_by(OptimizationRun.created_at.desc()))
    return [dict(run_id=r.id,status=r.status,objective=r.objective,created_at=r.created_at) for r in runs]
