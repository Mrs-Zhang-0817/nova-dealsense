import io
import socket
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen
from uuid import uuid4
from pypdf import PdfReader
import test_api
from test_finance import bottle
from test_optimizer import params

class DecisionFlow(unittest.TestCase):
    start=test_api.ApiTest.start
    stop=test_api.ApiTest.stop
    req=test_api.ApiTest.req

    def test_selection_pdf_and_history(self):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1",0))
            self.port=sock.getsockname()[1]
        self.start()
        def make():
            b=bottle()
            b["data_origin"]="demo"
            b["items"][0]["product"]["sku"]=uuid4().hex
            b["costs"].append(dict(cost_type="insurance",amount="17",currency="USD",confirmed=False,included=False))
            return b,self.req("POST","/deals",b)[1]
        body,deal=make()
        _,other=make()
        path="/deals/"+deal["id"]
        data=params(deal["id"],price_min="3.06",price_max="3.09").model_dump(mode="json")
        run=self.req("POST",path+"/optimize",data)[1]
        rows=self.req("GET","/optimization/"+run["run_id"]+"/comparison")[1]["rows"]
        pick=dict(optimization_run_id=run["run_id"],scenario_id=rows[-1]["id"],selected_by="验收人员",selection_note="核对报价与利润")
        def reject(url,value):
            with self.assertRaises(HTTPError) as cm:self.req("POST",url,value)
            self.assertIn(cm.exception.code,(404,422))
        reject(path+"/decisions",pick)
        pick["scenario_id"]=rows[0]["id"]
        reject("/deals/"+other["id"]+"/decisions",pick)
        reject(path+"/reports",{})
        first=self.req("POST",path+"/decisions",pick)[1]
        pick["scenario_id"]=rows[1]["id"]
        second=self.req("POST",path+"/decisions",pick)[1]
        self.assertEqual(self.req("GET",path+"/decisions")[1][0]["id"],second["id"])
        self.assertEqual(self.req("GET","/decisions/"+first["id"])[1]["scenario_id"],rows[0]["id"])
        req={"decision_selection_id":second["id"]}
        reject("/deals/"+other["id"]+"/reports",req)
        report_id=self.req("POST",path+"/reports",req)[1]["id"]
        report="/reports/"+report_id
        data=self.req("GET",report)[1]
        self.assertEqual(data["selected"]["id"],rows[1]["id"])
        self.assertEqual(data["currency"],"USD")
        self.assertTrue(any("未确认" in w for w in data["warnings"]))
        self.assertEqual(len(data["sections"]),8)
        def download():
            with urlopen(f"http://127.0.0.1:{self.port}/api/v1"+report+"/download") as response:
                self.assertEqual(response.headers.get_content_type(),"application/pdf")
                return response.read()
        pdf=download()
        self.assertTrue(pdf.startswith(b"%PDF-"))
        parsed=PdfReader(io.BytesIO(pdf))
        self.assertGreaterEqual(len(parsed.pages),5)
        text="".join(p.extract_text() for p in parsed.pages)
        for term in ("跨境交易决策分析报告","预计贡献利润","USD","风险与局限"):
            self.assertIn(term,text)
        body.pop("buyer")
        body["buyer_id"]=deal["buyer_id"]
        body["items"][0].pop("product")
        body["items"][0].update(product_id=deal["items"][0]["product_id"],unit_price="8")
        self.req("PUT",path,body)
        self.stop()
        self.start()
        self.assertEqual(self.req("GET",report)[1],data)
        self.assertEqual(download(),pdf)
        self.assertGreater(self.req("GET","/dashboard")[1]["demo"]["decisions"],0)
        # A large grid yields feasible candidates but has incomplete coverage.
        args=params(deal["id"],price_min="3.07",price_max="5",price_step=".001").model_dump(mode="json")
        limited=self.req("POST",path+"/optimize",args)[1]
        self.assertTrue(limited["truncated"])
        candidates=self.req("GET","/optimization/"+limited["run_id"]+"/comparison")[1]
        self.assertTrue(candidates["summary"]["truncated"])
        chosen=self.req("POST",path+"/decisions",dict(pick,optimization_run_id=limited["run_id"],scenario_id=candidates["rows"][0]["id"]))[1]
        limited_report=self.req("POST",path+"/reports",{"decision_selection_id":chosen["id"]})[1]
        warnings=self.req("GET","/reports/"+limited_report["id"])[1]["warnings"]
        self.assertTrue(any("截断" in w for w in warnings))
        for d in (deal,other):
            self.req("DELETE","/deals/"+d["id"])
            self.req("DELETE","/buyers/"+d["buyer_id"])
            self.req("DELETE","/products/"+d["items"][0]["product_id"])

