"""Populate three labelled local demo deals via supported HTTP endpoints."""
import argparse,json
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlparse,quote

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument("--api",default="http://localhost:8000/api/v1")
base=parser.parse_args().api.rstrip("/")
if urlparse(base).hostname not in ("localhost","127.0.0.1"):raise SystemExit("仅支持本机演示服务")

def api(path,data=None):
    req=Request(base+path,data=json.dumps(data).encode() if data is not None else None,headers={"Content-Type":"application/json"})
    with urlopen(req,timeout=60) as res:return json.load(res)

for case in json.loads((root/"sample_data/cases.json").read_text(encoding="utf8")):
    existing=[d for d in api("/deals?q="+quote(case["name"]))["items"] if d["data_origin"]=="demo" and d["name"]==case["name"]]
    if existing:deal=existing[0]
    else:
        body=json.loads((root/"sample_data/bottle.json").read_text(encoding="utf8"))
        body.update(name=case["name"],data_origin="demo",target_margin=".25")
        body["items"][0]["product"]["sku"]="SUBMISSION-BOTTLE-"+case["key"]
        deal=api("/deals",body)
    path="/deals/"+deal["id"]
    history=api(path+"/optimization-history")
    for objective in (["PROFIT_FIRST","LOW_RISK","BUYER_FIT"] if case["key"]=="feasible" else ["BUYER_FIT"]):
        previous=next((r for r in history if r["objective"]==objective and r["status"]==case["expected"]),None)
        if previous:run=previous
        else:
            params=dict(deal_id=deal["id"],objective=objective,target_margin=".25",minimum_profit="0",price_min="3.00",price_max="3.09",price_step=".01",
                quantity_min=5000,quantity_max=5000,quantity_step=1,production_capacity=5000,delivery_deadline_days=10,setup_days=1,
                production_units_per_day=1000,shipping_options=[{"name":"演示物流","days":4}])
            params.update(case["overrides"])
            run=api(path+"/optimize",params)
        if run["status"]!=case["expected"]:raise RuntimeError("演示结果与预期不符")
        if case["key"]=="feasible" and objective=="BUYER_FIT" and not api(path+"/reports"):
            rows=api("/optimization/"+run["run_id"]+"/comparison")["rows"]
            pick=api(path+"/decisions",dict(optimization_run_id=run["run_id"],scenario_id=rows[0]["id"],selected_by="演示评审",selection_note="达到目标贡献率的最低报价"))
            api(path+"/reports",dict(decision_selection_id=pick["id"]))
    print(case["key"],deal["id"],case["expected"])
