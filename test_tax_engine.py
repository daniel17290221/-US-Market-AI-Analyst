import unittest

from api.index import app
from api.tax_engine import analyze_family, optimize_family_allocation


class TaxEngineTests(unittest.TestCase):
    def test_financial_income_threshold_and_incremental_tax(self):
        result = analyze_family(
            [
                {
                    "id": "self",
                    "name": "본인",
                    "other_income": 50_000_000,
                    "domestic_dividends": 25_000_000,
                    "health_insurance": "employee",
                }
            ]
        )
        member = result["members"][0]

        self.assertEqual(member["financial_income_excess"], 5_000_000)
        self.assertEqual(member["tax"]["estimated_withholding"], 3_850_000)
        self.assertEqual(
            member["tax"]["incremental_comprehensive_tax"],
            1_320_000,
        )
        self.assertEqual(
            member["tax"]["estimated_additional_payment"],
            550_000,
        )

    def test_dependent_health_limit_reduces_safe_allocation_room(self):
        result = analyze_family(
            [
                {
                    "id": "spouse",
                    "name": "배우자",
                    "other_income": 5_000_000,
                    "domestic_dividends": 16_000_000,
                    "health_insurance": "dependent",
                }
            ]
        )
        member = result["members"][0]

        self.assertEqual(member["financial_income_remaining"], 4_000_000)
        self.assertEqual(member["health"]["dependent_status"], "risk")
        self.assertEqual(member["safe_additional_financial_income"], 0)

    def test_minor_gift_allowance_and_incremental_tax(self):
        result = analyze_family(
            [
                {
                    "id": "child",
                    "name": "자녀",
                    "relationship": "minor_child",
                    "age": 12,
                    "gift_received_10y": 10_000_000,
                    "planned_gift": 20_000_000,
                }
            ]
        )
        gift = result["members"][0]["gift"]

        self.assertEqual(gift["allowance"], 20_000_000)
        self.assertEqual(gift["taxable_amount_after_plan"], 10_000_000)
        self.assertEqual(gift["estimated_incremental_gift_tax"], 1_000_000)

    def test_pension_credit_room_uses_salary_rate(self):
        result = analyze_family(
            [
                {
                    "id": "self",
                    "name": "본인",
                    "gross_salary": 50_000_000,
                    "pension_contribution": 0,
                }
            ]
        )
        pension = result["members"][0]["pension"]

        self.assertEqual(pension["additional_contribution_room"], 9_000_000)
        self.assertEqual(pension["credit_rate"], 0.165)
        self.assertEqual(pension["estimated_additional_credit"], 1_485_000)

    def test_no_taxable_income_does_not_claim_pension_credit(self):
        result = analyze_family(
            [
                {
                    "id": "child",
                    "name": "자녀",
                    "relationship": "minor_child",
                    "age": 12,
                }
            ]
        )
        pension = result["members"][0]["pension"]

        self.assertEqual(pension["additional_contribution_room"], 9_000_000)
        self.assertEqual(pension["estimated_additional_credit"], 0)

    def test_allocation_uses_sheltered_accounts_before_general_account(self):
        result = optimize_family_allocation(
            [
                {
                    "id": "self",
                    "name": "본인",
                    "relationship": "self",
                    "age": 40,
                    "domestic_dividends": 18_000_000,
                    "isa_available": 20_000_000,
                    "pension_asset_room": 10_000_000,
                },
                {
                    "id": "spouse",
                    "name": "배우자",
                    "relationship": "spouse",
                    "age": 40,
                    "other_income": 15_000_000,
                    "health_insurance": "dependent",
                    "isa_available": 30_000_000,
                },
            ],
            100_000_000,
            5,
            0,
        )

        summary = result["summary"]
        accounts = {item["account"] for item in result["allocations"]}
        self.assertEqual(summary["sheltered_investment"], 60_000_000)
        self.assertGreater(summary["estimated_annual_tax_savings"], 0)
        self.assertEqual(summary["optimized_health_risk_count"], 0)
        self.assertEqual(summary["gift_required"], 30_000_000)
        self.assertEqual(accounts, {"pension", "isa", "general"})
        evidence = result["calculation_evidence"]
        self.assertEqual(
            evidence["assumptions"]["financial_income_threshold"],
            20_000_000,
        )
        self.assertEqual(
            evidence["optimized_components"]["total"],
            summary["optimized_estimated_tax"],
        )
        self.assertEqual(len(evidence["member_boundaries"]), 2)
        self.assertGreaterEqual(len(evidence["sources"]), 4)

    def test_allocation_never_exceeds_remaining_gift_allowance(self):
        result = optimize_family_allocation(
            [
                {
                    "id": "self",
                    "name": "본인",
                    "relationship": "self",
                    "age": 40,
                    "domestic_dividends": 20_000_000,
                },
                {
                    "id": "spouse",
                    "name": "배우자",
                    "relationship": "spouse",
                    "age": 40,
                    "gift_received_10y": 590_000_000,
                    "isa_available": 100_000_000,
                },
            ],
            50_000_000,
            5,
        )

        self.assertEqual(result["summary"]["gift_required"], 10_000_000)
        spouse_assets = sum(
            item["investment"]
            for item in result["allocations"]
            if item["profile_id"] == "spouse"
        )
        self.assertEqual(spouse_assets, 10_000_000)


class TaxRouteTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_family_analysis_is_stateless_and_not_cached(self):
        response = self.client.post(
            "/api/tax/family-analysis",
            json={"profiles": [{"id": "self", "name": "본인"}]},
        )
        self.addCleanup(response.close)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["estimate_only"])
        self.assertIn("no-store", response.headers["Cache-Control"])

    def test_family_analysis_limits_profile_count(self):
        response = self.client.post(
            "/api/tax/family-analysis",
            json={"profiles": [{}] * 11},
        )
        self.addCleanup(response.close)

        self.assertEqual(response.status_code, 400)
        self.assertIn("최대 10명", response.get_json()["message"])

    def test_allocation_optimization_returns_tax_savings(self):
        response = self.client.post(
            "/api/tax/allocation-optimization",
            json={
                "profiles": [
                    {
                        "id": "self",
                        "name": "본인",
                        "age": 40,
                        "isa_available": 50_000_000,
                    }
                ],
                "investment_amount": 50_000_000,
                "annual_yield_rate": 5,
                "foreign_ratio": 20,
            },
        )
        self.addCleanup(response.close)

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["summary"]["sheltered_investment"], 50_000_000)
        self.assertIn("no-store", response.headers["Cache-Control"])

    def test_allocation_optimization_validates_yield(self):
        response = self.client.post(
            "/api/tax/allocation-optimization",
            json={
                "profiles": [{"id": "self", "name": "본인"}],
                "investment_amount": 50_000_000,
                "annual_yield_rate": 50,
            },
        )
        self.addCleanup(response.close)

        self.assertEqual(response.status_code, 400)
        self.assertIn("30%", response.get_json()["message"])


if __name__ == "__main__":
    unittest.main()
