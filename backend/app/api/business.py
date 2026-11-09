from datetime import datetime, timezone
from uuid import UUID, uuid4
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, delete, func, or_
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.market import Market
from app.models.business import Buyer, Product, Deal, DealItem, CostItem, Constraint
from app.schemas.deals import BuyerIn, ProductIn, DealIn
from app.services.finance import calculate

router = APIRouter()
DB = Depends(get_db)

def fields(row):
    return {c.name:getattr(row,c.name) for c in row.__table__.columns}

def encode(value):
    return jsonable_encoder(value, custom_encoder={Decimal:str})

def lookup(db, model, key):
    row = db.get(model,key)
    if row is None:
        raise HTTPException(404,"记录不存在")
    return row

def market(db, code):
    if not lookup(db,Market,code).is_enabled:
        raise HTTPException(422,"市场未启用")

@router.get("/markets")
def markets(db:Session=DB):
    return [fields(r) for r in db.scalars(select(Market).order_by(Market.country_code))]

@router.get("/markets/{code}")
def market_info(code:str, db:Session=DB):
    return fields(lookup(db,Market,code.upper()))

def catalog(path, model, schema):
    def listing(db:Session=DB):
        return encode([fields(r) for r in db.scalars(select(model).order_by(model.created_at,model.id))])
    def detail(id:UUID, db:Session=DB):
        return encode(fields(lookup(db,model,id)))
    def save(data,db,id=None):
        if model is Buyer:
            market(db,data.country_code)
        row = lookup(db,model,id) if id else model()
        for k,v in data.model_dump().items():
            setattr(row,k,v)
        db.add(row)
        db.flush()
        result = encode(fields(row))
        db.commit()
        return result
    def create(data:schema,db:Session=DB):
        return save(data,db)
    def update(id:UUID,data:schema,db:Session=DB):
        return save(data,db,id)
    def remove(id:UUID,db:Session=DB):
        db.delete(lookup(db,model,id))
        db.commit()
        return Response(status_code=204)
    for suffix,method,handler,status in [("","GET",listing,200),("","POST",create,201),("/{id}","GET",detail,200),("/{id}","PUT",update,200),("/{id}","DELETE",remove,204)]:
        router.add_api_route(path+suffix,handler,methods=[method],status_code=status,name=model.__name__+handler.__name__)

catalog("/buyers",Buyer,BuyerIn)
catalog("/products",Product,ProductIn)

def resolve(db,model,id,data):
    if (id is None) == (data is None):
        raise HTTPException(422,"请选择现有记录或填写一条新记录")
    if id:
        return lookup(db,model,id)
    if model is Buyer:
        market(db,data.country_code)
    row = model(**data.model_dump())
    db.add(row)
    db.flush()
    return row

children = {"items":DealItem,"costs":CostItem,"constraints":Constraint}

def rows(db,model,id):
    return db.scalars(select(model).where(model.deal_id==id).order_by(model.id)).all()

def detail(db,deal,with_financials=True):
    result = fields(deal)
    result["buyer"] = fields(lookup(db,Buyer,deal.buyer_id))
    for key,model in children.items():
        result[key] = [fields(row) for row in rows(db,model,deal.id)]
    if not with_financials:
        return encode(result)
    from app.schemas.deals import Item, Cost, Limit
    payload = {k:result[k] for k in DealIn.model_fields if k not in ("buyer",*children)}
    for key,schema in [("items",Item),("costs",Cost),("constraints",Limit)]:
        payload[key] = [{k:v for k,v in row.items() if k in schema.model_fields} for row in result[key]]
    result["financials"] = calculate(DealIn(**payload))[2]
    return encode(result)

def persist(db,data,deal):
    lines, amounts, _ = calculate(data)
    for code in (data.origin_country,data.destination_country):
        market(db,code)
    buyer = resolve(db,Buyer,data.buyer_id,data.buyer)
    prior = {}
    if deal.id:
        deal.updated_at = datetime.now(timezone.utc)
        prior = {r.product_id:r for r in rows(db,DealItem,deal.id)}
        for model in children.values():
            db.execute(delete(model).where(model.deal_id==deal.id))
    for k,v in data.model_dump(exclude={"buyer","buyer_id","exchange_rates",*children}).items():
        if k == "data_origin" and deal.id and k not in data.model_fields_set:
            continue
        setattr(deal,k,v)
    deal.exchange_rates = [r.model_dump(mode="json") for r in data.exchange_rates]
    deal.buyer_id = buyer.id
    db.add(deal)
    db.flush()
    for item,(rev,mfg) in zip(data.items,lines):
        product = resolve(db,Product,item.product_id,item.product)
        old = prior.get(product.id)
        db.add(DealItem(**item.model_dump(exclude={"product","product_id"}),deal_id=deal.id,product_id=product.id,
            product_name_snapshot=old.product_name_snapshot if old else product.name,
            sku_snapshot=old.sku_snapshot if old else product.sku,unit=old.unit if old else product.unit,
            converted_revenue=rev,converted_manufacturing_cost=mfg))
    for c,a in zip(data.costs,amounts):
        db.add(CostItem(**c.model_dump(),deal_id=deal.id,converted_amount=a))
    for c in data.constraints:
        db.add(Constraint(**c.model_dump(),deal_id=deal.id))
    db.flush()
    result = detail(db,deal)
    db.commit()
    return result

@router.post("/deals",status_code=201)
def create(data:DealIn,db:Session=DB):
    return persist(db,data,Deal(deal_number="ND-"+uuid4().hex[:16].upper()))

@router.put("/deals/{id}")
def update(id:UUID,data:DealIn,db:Session=DB):
    deal = db.get(Deal,id,with_for_update=True)
    if not deal:
        raise HTTPException(404,"订单不存在")
    return persist(db,data,deal)

@router.delete("/deals/{id}",status_code=204)
def remove(id:UUID,db:Session=DB):
    db.delete(lookup(db,Deal,id))
    db.commit()
    return Response(status_code=204)

@router.get("/deals/{id}")
def get(id:UUID,db:Session=DB):
    return detail(db,lookup(db,Deal,id))

@router.get("/deals")
def listing(page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100),q:str="",destination_country:str="",status:str="",ascending:bool=False,db:Session=DB):
    query = select(Deal,Buyer.company_name).join(Buyer)
    if destination_country:
        query = query.where(Deal.destination_country==destination_country)
    if status:
        query = query.where(Deal.status==status)
    if q:
        query = query.where(or_(*(col.icontains(q,autoescape=True) for col in (Deal.name,Deal.deal_number,Buyer.company_name))))
    count = db.scalar(select(func.count()).select_from(query.subquery()))
    revenue = select(func.sum(DealItem.converted_revenue)).where(DealItem.deal_id==Deal.id).scalar_subquery()
    query = query.add_columns(revenue).order_by(Deal.created_at.asc() if ascending else Deal.created_at.desc(),Deal.id)
    return encode(dict(total=count,items=[dict(**fields(d),buyer_name=b,estimated_value=r)
        for d,b,r in db.execute(query.offset((page-1)*page_size).limit(page_size))]))



