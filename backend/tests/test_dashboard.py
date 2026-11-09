from decimal import Decimal
from uuid import uuid4
import unittest,socket
import test_api
from test_finance import bottle

class DashboardRegression(unittest.TestCase):
    start=test_api.ApiTest.start
    stop=test_api.ApiTest.stop
    req=test_api.ApiTest.req

    def test_totals_follow_create_edit_restart(self):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1",0))
            self.port=sock.getsockname()[1]
        self.start()
        def stats():return self.req("GET","/dashboard")[1]
        old=stats()
        payload=bottle()
        payload.update(data_origin="demo")
        payload["items"][0]["product"]["sku"]=uuid4().hex
        deal=self.req("POST","/deals",payload)[1]
        path="/deals/"+deal["id"]
        baseline=Decimal(old["demo"]["total_value"].get("USD","0"))
        new=stats()
        self.assertEqual(new["actual"],old["actual"])
        self.assertEqual(new["demo"]["active"],old["demo"]["active"]+1)
        self.assertEqual(Decimal(new["demo"]["total_value"]["USD"]),baseline+15000)
        payload.pop("buyer")
        payload["buyer_id"]=deal["buyer_id"]
        line=payload["items"][0]
        line.pop("product")
        line.update(product_id=deal["items"][0]["product_id"],unit_price="4")
        self.req("PUT",path,payload)
        edited=stats()
        self.assertEqual(Decimal(edited["demo"]["total_value"]["USD"]),baseline+20000)
        self.stop()
        self.start()
        self.assertEqual(stats(),edited)
        self.req("DELETE",path)
        self.req("DELETE","/buyers/"+deal["buyer_id"])
        self.req("DELETE","/products/"+line["product_id"])
