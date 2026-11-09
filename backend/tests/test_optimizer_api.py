import socket
import unittest
from uuid import uuid4
import test_api
from test_finance import bottle
from test_optimizer import params
from app.api.business import encode
from app.optimization.engine import evaluate
from app.schemas.optimization import Optimization

class HistoryTest(unittest.TestCase):
    start=test_api.ApiTest.start
    stop=test_api.ApiTest.stop
    req=test_api.ApiTest.req

    def test_replay_after_edit_and_restart(self):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1",0))
            self.port=sock.getsockname()[1]
        self.start()
        body=bottle()
        body["items"][0]["product"]["sku"]=uuid4().hex
        _,deal=self.req("POST","/deals",body)
        path="/deals/"+deal["id"]
        request=params(deal["id"]).model_dump(mode="json")
        status,result=self.req("POST",path+"/optimize",request)
        self.assertEqual(status,201)
        endpoint="/optimization/"+result["run_id"]
        before=self.req("GET",endpoint)[1]
        self.assertEqual(before["recommended"]["price"],"3.07")
        body.pop("buyer")
        body["buyer_id"]=deal["buyer_id"]
        body["items"][0].pop("product")
        body["items"][0].update(product_id=deal["items"][0]["product_id"],unit_manufacturing_cost="15")
        self.req("PUT",path,body)
        _,second=self.req("POST",path+"/optimize",request)
        self.assertEqual(second["status"],"INFEASIBLE")
        self.stop()
        self.start()
        self.assertEqual(len(self.req("GET",path+"/optimization-history")[1]),2)
        self.assertEqual(self.req("GET",endpoint)[1],before)
        snapshot=before["input_snapshot"]
        _,replayed=evaluate(snapshot["deal"],Optimization(**snapshot["parameters"]))
        self.assertEqual(self.req("GET",endpoint+"/scenarios")[1],encode(replayed))
        self.req("DELETE",path)
        self.req("DELETE","/buyers/"+deal["buyer_id"])
        self.req("DELETE","/products/"+deal["items"][0]["product_id"])
        self.assertEqual(self.req("GET",endpoint)[1],before)
