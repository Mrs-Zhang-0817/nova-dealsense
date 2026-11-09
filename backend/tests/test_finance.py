import json
import unittest
from decimal import Decimal
from pathlib import Path
from pydantic import ValidationError
from app.schemas.deals import DealIn
from app.services.finance import calculate

def bottle():
    return json.loads((Path(__file__).resolve().parents[2]/"sample_data/bottle.json").read_text(encoding="utf8"))

class FinanceTest(unittest.TestCase):
    def totals(self,data):
        return calculate(DealIn(**data))[2]

    def test_bottle(self):
        result=self.totals(bottle())
        for key,value in dict(revenue="15000",manufacturing_cost="9000",additional_costs="2500",total_included_cost="11500",contribution_profit="3500").items():
            self.assertEqual(result[key],Decimal(value))
        self.assertEqual(result["manufacturing_cost"]/5000,Decimal("1.80"))
        self.assertEqual((result["contribution_margin"]*100).quantize(Decimal(".01")),Decimal("23.33"))

    def test_direct_rate_and_precision(self):
        data=bottle()
        data["exchange_rates"][0].update(base="CNY",quote="USD",rate="0.1")
        data["items"][0].update(quantity="3",unit_manufacturing_cost="0.1")
        self.assertEqual(self.totals(data)["manufacturing_cost"],Decimal("0.03"))

    def test_missing_rate(self):
        data=bottle()
        data["exchange_rates"]=[]
        with self.assertRaisesRegex(ValueError,"汇率"):
            self.totals(data)

    def test_invalid_quantity_and_missing_cost(self):
        data=bottle()
        for value in ["0","-1"]:
            data["items"][0]["quantity"]=value
            with self.assertRaises(ValidationError):
                self.totals(data)
        data=bottle()
        del data["items"][0]["unit_manufacturing_cost"]
        with self.assertRaises(ValidationError):
            self.totals(data)

    def test_zero_and_pending(self):
        data=bottle()
        data["items"][0].update(unit_price="0",manufacturing_confirmed=False)
        data["costs"][0]["confirmed"]=False
        result=self.totals(data)
        self.assertIsNone(result["contribution_margin"])
        self.assertEqual(result["total_included_cost"],0)
        self.assertTrue(result["has_estimates"])
