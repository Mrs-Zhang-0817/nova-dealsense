from datetime import datetime,timezone
from uuid import UUID,uuid4
from fastapi import APIRouter,HTTPException,Response
from pydantic import Field
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from app.schemas.deals import Input,Name
from app.models.business import Deal, DealItem
from app.models.optimization import OptimizationRun,Scenario
from app.models.decision import Selection,DecisionReport
from app.reports.decision import present,snapshot,OBJECTIVES
from app.reports.pdf import render
from .business import DB,lookup,fields

router=APIRouter()
class Pick(Input):
    optimization_run_id:UUID
    scenario_id:UUID
    selected_by:Name
    selection_note:str=Field("",max_length=1000)

class Generate(Input):
    decision_selection_id:UUID

def scenarios(db,run):
    return db.scalars(select(Scenario).where(Scenario.optimization_run_id==run.id).order_by(Scenario.position)).all()

@router.get("/optimization/{id}/comparison")
def comparison(id:UUID,db:Session=DB):
    run=lookup(db,OptimizationRun,id)
    return dict(currency=run.input_snapshot["deal"]["currency"],objective=OBJECTIVES[run.objective],
                summary=run.calculation_snapshot,rows=[present(run,r) for r in scenarios(db,run)])

@router.post("/deals/{id}/decisions",status_code=201)
def choose(id:UUID,pick:Pick,db:Session=DB):
    run=lookup(db,OptimizationRun,pick.optimization_run_id)
    scenario=lookup(db,Scenario,pick.scenario_id)
    if run.deal_id!=id or scenario.optimization_run_id!=run.id or scenario.result["feasibility"]!="FEASIBLE":
        raise HTTPException(422,"只能选择本订单本次运行中的可行方案")
    selection=Selection(deal_id=id,**pick.model_dump())
    db.add(selection)
    db.flush()
    result=fields(selection)
    db.commit()
    return result

@router.get("/deals/{id}/decisions")
def selections(id:UUID,db:Session=DB):
    lookup(db,Deal,id)
    return [fields(s) for s in db.scalars(select(Selection).where(Selection.deal_id==id).order_by(Selection.created_at.desc(),Selection.id))]

@router.get("/decisions/{id}")
def decision(id:UUID,db:Session=DB):
    record=lookup(db,Selection,id)
    return dict(**fields(record),scenario=present(lookup(db,OptimizationRun,record.optimization_run_id),lookup(db,Scenario,record.scenario_id)))

@router.post("/deals/{id}/reports",status_code=201)
def generate(id:UUID,body:Generate,db:Session=DB):
    selection=lookup(db,Selection,body.decision_selection_id)
    if selection.deal_id!=id:raise HTTPException(422,"所选决策不属于该订单")
    run=lookup(db,OptimizationRun,selection.optimization_run_id)
    chosen=present(run,lookup(db,Scenario,selection.scenario_id))
    candidates=[r for r in scenarios(db,run) if r.id!=selection.scenario_id and r.result["feasibility"]=="FEASIBLE"]
    now=datetime.now(timezone.utc)
    number="ND-"+now.strftime("%Y%m%d")+"-"+uuid4().hex[:10].upper()
    data=snapshot(run,chosen,[present(run,r) for r in candidates[:3]],selection,number,now.isoformat(timespec="seconds"))
    report=DecisionReport(decision_selection_id=selection.id,report_number=number,report_snapshot=data,pdf=render(data))
    db.add(report)
    db.flush()
    result=dict(id=report.id,report_number=number)
    db.commit()
    return result

@router.get("/reports/{id}")
def report(id:UUID,db:Session=DB):
    r=lookup(db,DecisionReport,id)
    return dict(id=r.id,**r.report_snapshot)

@router.get("/reports/{id}/download")
def download(id:UUID,db:Session=DB):
    r=lookup(db,DecisionReport,id)
    return Response(r.pdf,media_type="application/pdf",headers={"Content-Disposition":f'attachment; filename="{r.report_number}.pdf"'})

def report_list(db,deal_id=None,origin=None):
    query=select(DecisionReport.id,DecisionReport.report_number,DecisionReport.created_at).join(Selection)
    if deal_id is not None:query=query.where(Selection.deal_id==deal_id)
    if origin is not None:query=query.join(Deal).where(Deal.data_origin==origin)
    query=query.order_by(DecisionReport.created_at.desc())
    if deal_id is None:query=query.limit(5)
    return [dict(r._mapping) for r in db.execute(query)]

@router.get("/deals/{id}/reports")
def reports(id:UUID,db:Session=DB):
    return report_list(db,id)

@router.get("/dashboard")
def dashboard(db:Session=DB):
    latest=select(OptimizationRun.status).where(OptimizationRun.deal_id==Deal.id).order_by(OptimizationRun.created_at.desc(),OptimizationRun.id).limit(1).scalar_subquery()
    out={}
    for origin in ("actual","demo","unknown"):
        active=db.scalar(select(func.count()).select_from(Deal).where(Deal.data_origin==origin,Deal.status!="closed"))
        def count(model):
            return db.scalar(select(func.count()).select_from(model).join(Deal,model.deal_id==Deal.id).where(Deal.data_origin==origin))
        def status_count(status):
            return db.scalar(select(func.count()).select_from(Deal).where(Deal.data_origin==origin,latest==status))
        values=db.execute(select(Deal.currency,func.sum(DealItem.converted_revenue)).join(Deal,DealItem.deal_id==Deal.id).where(Deal.data_origin==origin).group_by(Deal.currency).order_by(Deal.currency))
        successful=db.scalar(select(func.count()).select_from(OptimizationRun).join(Deal).where(Deal.data_origin==origin,OptimizationRun.status=="FEASIBLE"))
        out[origin]=dict(total_value={code:str(amount) for code,amount in values},feasible_runs=successful,active=active,runs=count(OptimizationRun),feasible=status_count("FEASIBLE"),infeasible=status_count("INFEASIBLE"),
                         decisions=count(Selection),reports=report_list(db,origin=origin))
    return out

