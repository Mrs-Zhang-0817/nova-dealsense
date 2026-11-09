import unittest
from uuid import uuid4
from decimal import Decimal as D
from pydantic import ValidationError
from app.optimization.engine import evaluate,reverse_price,LIMIT
from app.schemas.optimization import Optimization
from test_finance import bottle

def params(id=None,**updates):
    data=dict(deal_id=id or uuid4(),objective="PROFIT_FIRST",target_margin=".25",minimum_profit="0",
        price_min="3",price_max="3.07",price_step=".01",quantity_min=5000,quantity_max=5000,
        quantity_step=1,production_capacity=5000,delivery_deadline_days=10,setup_days=1,
        production_units_per_day=1000,shipping_options=[dict(name="演示物流",days=4)])
    return Optimization(**(data|updates))

class OptimizerTests(unittest.TestCase):
    def setUp(self):
        self.s=bottle()
        self.s["constraints"]=[]
        self.s["costs"][0]["id"]="fixed"

    def run_case(self,**kwargs):
        return evaluate(self.s,params(**kwargs))

    def test_reference_and_rounding(self):
        summary,rows=self.run_case()
        best=rows[0]
        self.assertEqual(summary["status"],"FEASIBLE")
        self.assertEqual(best["minimum_margin_price"],D("3.07"))
        self.assertEqual(best["financials"]["contribution_profit"],3850)
        self.assertEqual(best["financials"]["contribution_margin_percent"],D("25.08"))
        self.assertEqual(best["financials"]["manufacturing_cost"],9000)
        self.assertEqual(best["financials"]["total_included_cost"],11500)
        self.assertEqual(best["financials"]["revenue"],15350)
        self.assertEqual(best["delivery_days"],10)
        self.assertTrue(all(v["passed"] for v in best["constraint_results"].values()))
        self.assertEqual(reverse_price(D("11.501"),5,D(".25"),D(".05"),D("3.02")),D("3.07"))

    def test_each_hard_constraint(self):
        for key,update in [("unit_ceiling",dict(customer_unit_price_ceiling=3)),("budget",dict(customer_total_budget=15000)),
                           ("moq",dict(minimum_order_quantity=5001)),("capacity",dict(production_capacity=4999)),
                           ("deadline",dict(delivery_deadline_days=9)),("profit",dict(minimum_profit=3851))]:
            with self.subTest(key=key):
                summary,_=self.run_case(**update)
                self.assertEqual(summary["status"],"INFEASIBLE")
                self.assertIn(key,summary["diagnostics"])

    def test_missing_and_invalid(self):
        for changes in [dict(setup_days=None),dict(production_units_per_day=None),dict(shipping_options=[]),dict(quantity_max=5001)]:
            self.assertEqual(self.run_case(**changes)[0]["status"],"INSUFFICIENT_DATA")
        for changes in [dict(target_margin=1),dict(target_margin=-1),dict(quantity_min=0),dict(quantity_step=-1)]:
            with self.assertRaises(ValidationError):
                params(**changes)
        self.s["exchange_rates"]=[]
        self.assertEqual(self.run_case()[0]["status"],"INSUFFICIENT_DATA")

    def test_replacement_and_variable_cost(self):
        self.s["costs"][0]["cost_type"]="logistics"
        _,rows=self.run_case(shipping_options=[dict(name="替换",days=4,replacement_cost="2000")])
        self.assertEqual(rows[0]["financials"]["additional_costs"],2000)
        _,rows=self.run_case(quantity_min=2500,quantity_max=2500,additional_cost_adjustments={"fixed":"per_unit"})
        self.assertEqual(rows[0]["financials"]["additional_costs"],1250)

    def test_objectives_and_cutoff(self):
        for objective,price in [("PROFIT_FIRST","3.09"),("BUYER_FIT","3.07"),("LOW_RISK","3.09")]:
            _,rows=self.run_case(objective=objective,price_max="3.09")
            self.assertEqual(rows[0]["price"],D(price))
            self.assertEqual(sum(r["feasibility"]=="FEASIBLE" for r in rows),3)
        summary,rows=self.run_case(price_step=".00001")
        self.assertTrue(summary["truncated"])
        self.assertEqual(len(rows),LIMIT)
        self.assertEqual(summary["status"],"INSUFFICIENT_DATA")
