"""Run from backend with the migrated development DB. Only test-owned records are removed."""
import json
import socket
import subprocess
import sys
import time
import unittest
from urllib.request import Request,urlopen
from urllib.error import HTTPError, URLError
from uuid import uuid4
from test_finance import bottle

class ApiTest(unittest.TestCase):
    def start(self):
        self.proc=subprocess.Popen([sys.executable,"-m","uvicorn","app.main:app","--port",str(self.port),"--no-access-log"])
        self.addCleanup(self.stop)
        for _ in range(100):
            try:
                self.req("GET","/health")
                return
            except URLError:
                time.sleep(.1)
        self.fail("API startup timed out")

    def stop(self):
        if self.proc.poll() is None:
            self.proc.terminate()
            self.proc.wait(10)

    def req(self,method,path,body=None):
        payload=None if body is None else json.dumps(body).encode()
        request=Request(f"http://127.0.0.1:{self.port}/api/v1"+path,payload,method=method,headers={"Content-Type":"application/json"})
        with urlopen(request,timeout=10) as response:
            raw=response.read()
            return response.status,json.loads(raw) if raw else None

    def test_workflow_and_restart(self):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1",0))
            self.port=sock.getsockname()[1]
        self.start()
        self.assertTrue({"CN","US"} <= {r["country_code"] for r in self.req("GET","/markets")[1]})
        self.assertEqual(self.req("GET","/markets/US")[1]["default_currency"],"USD")
        for route,body in [("buyers",{"company_name":"API test","country_code":"CN"}),
                           ("products",{"name":"API test","unit":"件","sku":uuid4().hex})]:
            status,row=self.req("POST","/"+route,body)
            self.assertEqual(status,201)
            self.assertIn(row["id"],[r["id"] for r in self.req("GET","/"+route)[1]])
            self.assertEqual(self.req("DELETE","/"+route+"/"+row["id"])[0],204)
        payload=bottle()
        payload["items"][0]["product"]["sku"]=uuid4().hex
        status,created=self.req("POST","/deals",payload)
        self.assertEqual(status,201)
        path="/deals/"+created["id"]
        self.assertEqual(self.req("GET",path)[1],created)
        self.stop()
        self.start()
        self.assertEqual(self.req("GET",path)[1],created)
        buyer=created["buyer_id"]
        product=created["items"][0]["product_id"]
        payload["buyer_id"]=buyer
        del payload["buyer"]
        item=payload["items"][0]
        original=item.pop("product")
        item["product_id"]=product
        original["name"]="Changed catalog name"
        self.req("PUT","/products/"+product,original)
        payload["name"]="Revised"
        updated=self.req("PUT",path,payload)[1]
        self.assertEqual(updated["name"],"Revised")
        self.assertEqual(updated["items"][0]["product_name_snapshot"],"Stainless Steel Bottle")
        self.assertIn(created["id"],[r["id"] for r in self.req("GET","/deals?q=Revised&status=draft&destination_country=US")[1]["items"]])
        self.assertEqual(self.req("DELETE",path)[0],204)
        with self.assertRaises(HTTPError) as ctx:
            self.req("GET",path)
        self.assertEqual(ctx.exception.code,404)
        self.req("PUT","/buyers/"+buyer,{"company_name":"Updated","country_code":"US"})
        for route,key in [("buyers",buyer),("products",product)]:
            self.assertTrue(self.req("GET","/"+route+"/"+key)[1]["id"])
            self.assertEqual(self.req("DELETE","/"+route+"/"+key)[0],204)

