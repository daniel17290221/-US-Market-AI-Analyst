import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from api.index import app
from api.kiwoom import (
    KiwoomAPIError,
    KiwoomClient,
    KiwoomConfigurationError,
)
from routes import kiwoom as kiwoom_routes


class FakeResponse:
    def __init__(self, payload, status_code=200, headers=None):
        self._payload = payload
        self.status_code = status_code
        self.headers = headers or {}

    def json(self):
        return self._payload


class FakeHTTP:
    def __init__(self, response):
        self.responses = response if isinstance(response, list) else [response]
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.responses.pop(0)


class KiwoomClientTests(unittest.TestCase):
    def test_missing_credentials_are_rejected(self):
        client = KiwoomClient(env={})

        with self.assertRaises(KiwoomConfigurationError):
            client.get_access_token()

    def test_mock_mode_is_default_and_status_is_safe(self):
        client = KiwoomClient(
            env={"KIWOOM_APP_KEY": "app", "KIWOOM_SECRET_KEY": "secret"}
        )

        self.assertEqual(
            client.public_status(),
            {
                "provider": "kiwoom",
                "configured": True,
                "mode": "mock",
                "read_only": True,
            },
        )

    def test_token_is_requested_once_while_cached(self):
        expiry = (datetime.now() + timedelta(hours=1)).strftime("%Y%m%d%H%M%S")
        http = FakeHTTP(
            FakeResponse(
                {
                    "return_code": 0,
                    "return_msg": "정상",
                    "token": "access-token",
                    "expires_dt": expiry,
                }
            )
        )
        client = KiwoomClient(
            env={
                "KIWOOM_APP_KEY": "app",
                "KIWOOM_SECRET_KEY": "secret",
                "KIWOOM_API_MODE": "production",
            },
            http=http,
        )

        self.assertEqual(client.get_access_token(), "access-token")
        self.assertEqual(client.get_access_token(), "access-token")
        self.assertEqual(len(http.calls), 1)
        self.assertEqual(
            http.calls[0][0], "https://api.kiwoom.com/oauth2/token"
        )
        self.assertNotIn("app", client.public_status())
        self.assertNotIn("secret", client.public_status())

    def test_api_error_does_not_leak_credentials(self):
        http = FakeHTTP(
            FakeResponse(
                {"return_code": 1, "return_msg": "인증 실패"},
                status_code=401,
            )
        )
        client = KiwoomClient(
            env={"KIWOOM_APP_KEY": "app", "KIWOOM_SECRET_KEY": "secret"},
            http=http,
        )

        with self.assertRaisesRegex(KiwoomAPIError, "인증 실패"):
            client.get_access_token()

    def test_account_snapshot_is_normalized_and_masked(self):
        expiry = (datetime.now() + timedelta(hours=1)).strftime("%Y%m%d%H%M%S")
        http = FakeHTTP(
            [
                FakeResponse(
                    {
                        "return_code": 0,
                        "token": "access-token",
                        "expires_dt": expiry,
                    }
                ),
                FakeResponse({"return_code": 0, "acctNo": "1234567890"}),
                FakeResponse(
                    {
                        "return_code": 0,
                        "entr": "1,250,000",
                        "d2_entra": "1,100,000",
                    }
                ),
                FakeResponse(
                    {
                        "return_code": 0,
                        "tot_pur_amt": "10,000,000",
                        "tot_evlt_amt": "11,500,000",
                        "tot_evlt_pl": "+1,500,000",
                        "tot_prft_rt": "15.00",
                        "prsm_dpst_aset_amt": "12,600,000",
                        "acnt_evlt_remn_indv_tot": [
                            {
                                "stk_cd": "A005930",
                                "stk_nm": "삼성전자",
                                "rmnd_qty": "100",
                                "trde_able_qty": "100",
                                "pur_pric": "70000",
                                "cur_prc": "+85000",
                                "pur_amt": "7000000",
                                "evlt_amt": "8500000",
                                "evltv_prft": "+1500000",
                                "prft_rt": "21.43",
                            }
                        ],
                    }
                ),
            ]
        )
        client = KiwoomClient(
            env={"KIWOOM_APP_KEY": "app", "KIWOOM_SECRET_KEY": "secret"},
            http=http,
        )

        snapshot = client.get_account_snapshot()

        self.assertEqual(snapshot["account"]["masked_number"], "******7890")
        self.assertEqual(snapshot["cash"]["deposit"], 1_250_000)
        self.assertEqual(snapshot["summary"]["total_profit_loss"], 1_500_000)
        self.assertEqual(snapshot["positions"][0]["symbol"], "005930")
        self.assertEqual(snapshot["positions"][0]["current_price"], 85_000)
        self.assertEqual(snapshot["positions"][0]["return_rate"], 21.43)
        self.assertEqual(
            [call[1]["headers"].get("api-id") for call in http.calls[1:]],
            ["ka00001", "kt00001", "kt00018"],
        )

    def test_positions_follow_kiwoom_continuation_headers(self):
        expiry = (datetime.now() + timedelta(hours=1)).strftime("%Y%m%d%H%M%S")
        http = FakeHTTP(
            [
                FakeResponse(
                    {
                        "return_code": 0,
                        "token": "access-token",
                        "expires_dt": expiry,
                    }
                ),
                FakeResponse(
                    {
                        "return_code": 0,
                        "acnt_evlt_remn_indv_tot": [{"stk_cd": "005930"}],
                    },
                    headers={"cont-yn": "Y", "next-key": "page-2"},
                ),
                FakeResponse(
                    {
                        "return_code": 0,
                        "acnt_evlt_remn_indv_tot": [{"stk_cd": "000660"}],
                    },
                    headers={"cont-yn": "N"},
                ),
            ]
        )
        client = KiwoomClient(
            env={"KIWOOM_APP_KEY": "app", "KIWOOM_SECRET_KEY": "secret"},
            http=http,
        )

        result = client.get_positions()

        self.assertEqual(
            [item["stk_cd"] for item in result["acnt_evlt_remn_indv_tot"]],
            ["005930", "000660"],
        )
        self.assertEqual(http.calls[2][1]["headers"]["cont-yn"], "Y")
        self.assertEqual(http.calls[2][1]["headers"]["next-key"], "page-2")

    def test_transaction_history_normalizes_buys_sells_and_dividends(self):
        expiry = (datetime.now() + timedelta(hours=1)).strftime("%Y%m%d%H%M%S")
        http = FakeHTTP(
            [
                FakeResponse(
                    {
                        "return_code": 0,
                        "token": "access-token",
                        "expires_dt": expiry,
                    }
                ),
                FakeResponse(
                    {
                        "return_code": 0,
                        "trst_ovrl_trde_prps_array": [
                            {
                                "trde_dt": "20260701",
                                "trde_no": "1",
                                "stk_cd": "A005930",
                                "stk_nm": "삼성전자",
                                "trde_qty_jwa_cnt": "10",
                                "trde_unit": "70000",
                                "trde_amt": "700000",
                                "cmsn": "500",
                            }
                        ],
                    }
                ),
                FakeResponse(
                    {
                        "return_code": 0,
                        "trst_ovrl_trde_prps_array": [
                            {
                                "trde_dt": "20260710",
                                "trde_no": "2",
                                "stk_cd": "005930",
                                "stk_nm": "삼성전자",
                                "trde_qty_jwa_cnt": "2",
                                "trde_unit": "80000",
                                "trde_amt": "160000",
                                "cmsn": "100",
                                "trde_agri_tax": "300",
                            }
                        ],
                    }
                ),
                FakeResponse(
                    {
                        "return_code": 0,
                        "trst_ovrl_trde_prps_array": [
                            {
                                "trde_dt": "20260715",
                                "trde_no": "3",
                                "rmrk_nm": "현금배당",
                                "stk_cd": "005930",
                                "stk_nm": "삼성전자",
                                "trde_amt": "10000",
                                "exct_amt": "8460",
                                "incm_resi_tax": "1540",
                            }
                        ],
                    }
                ),
            ]
        )
        client = KiwoomClient(
            env={"KIWOOM_APP_KEY": "app", "KIWOOM_SECRET_KEY": "secret"},
            http=http,
        )

        transactions = client.get_transaction_history("2026-07-01", "2026-07-17")

        self.assertEqual(
            [transaction["side"] for transaction in transactions],
            ["BUY", "SELL", "DIVIDEND"],
        )
        self.assertEqual(transactions[0]["symbol"], "005930")
        self.assertEqual(transactions[0]["fees"], 500)
        self.assertEqual(transactions[1]["taxes"], 300)
        self.assertEqual(transactions[2]["net_amount"], 8460)
        self.assertEqual(
            [call[1]["json"]["tp"] for call in http.calls[1:]],
            ["4", "5", "0"],
        )


class KiwoomRouteTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_snapshot_requires_sync_secret(self):
        with patch.dict(
            kiwoom_routes.os.environ,
            {"KIWOOM_SYNC_SECRET": "test-pin"},
            clear=False,
        ):
            response = self.client.post("/api/kiwoom/snapshot")
            self.addCleanup(response.close)

        self.assertEqual(response.status_code, 401)
        self.assertIn("no-store", response.headers["Cache-Control"])

    def test_snapshot_returns_only_masked_account_data(self):
        fake_client = Mock()
        fake_client.get_account_snapshot.return_value = {
            "provider": "kiwoom",
            "mode": "mock",
            "read_only": True,
            "account": {"masked_number": "******7890"},
            "cash": {"deposit": 1000, "estimated_d2": 900},
            "summary": {},
            "positions": [],
            "synced_at": "2026-07-17T00:00:00+00:00",
        }

        with (
            patch.dict(
                kiwoom_routes.os.environ,
                {"KIWOOM_SYNC_SECRET": "test-pin"},
                clear=False,
            ),
            patch.object(kiwoom_routes, "_client", fake_client),
        ):
            response = self.client.post(
                "/api/kiwoom/snapshot",
                headers={"X-Kiwoom-Sync-Key": "test-pin"},
            )
            self.addCleanup(response.close)
            payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(payload["connected"])
        self.assertEqual(payload["account"]["masked_number"], "******7890")
        self.assertNotIn("acctNo", payload)
        self.assertIn("no-store", response.headers["Cache-Control"])
        fake_client.get_account_snapshot.assert_called_once_with(
            include_performance=True,
            history_months=12,
            local_transactions=[],
        )

    def test_snapshot_rejects_oversized_local_ledger(self):
        with patch.dict(
            kiwoom_routes.os.environ,
            {"KIWOOM_SYNC_SECRET": "test-pin"},
            clear=False,
        ):
            response = self.client.post(
                "/api/kiwoom/snapshot",
                headers={"X-Kiwoom-Sync-Key": "test-pin"},
                json={"local_transactions": [{}] * 501},
            )
            self.addCleanup(response.close)

        self.assertEqual(response.status_code, 400)
        self.assertIn("최대 500건", response.get_json()["message"])


if __name__ == "__main__":
    unittest.main()
