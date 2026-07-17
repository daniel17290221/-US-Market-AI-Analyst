"""Read-only client for the Kiwoom Securities REST API."""

from __future__ import annotations

import os
import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping, Optional

import requests

try:
    from portfolio_ledger import calculate_portfolio_performance
except ImportError:
    from .portfolio_ledger import calculate_portfolio_performance


class KiwoomError(RuntimeError):
    """Base exception for Kiwoom API failures."""


class KiwoomConfigurationError(KiwoomError):
    """Raised when required Kiwoom credentials are missing."""


class KiwoomAPIError(KiwoomError):
    """Raised when Kiwoom rejects an API request."""


class KiwoomClient:
    """Minimal OAuth client.

    This first integration phase intentionally exposes authentication only.
    Account and order APIs are added separately so the initial connection can
    remain read-only and easy to audit.
    """

    PRODUCTION_URL = "https://api.kiwoom.com"
    MOCK_URL = "https://mockapi.kiwoom.com"

    def __init__(
        self,
        *,
        env: Optional[Mapping[str, str]] = None,
        http: Any = None,
        timeout: int = 10,
    ) -> None:
        values = env if env is not None else os.environ
        self.app_key = values.get("KIWOOM_APP_KEY", "").strip()
        self.secret_key = values.get("KIWOOM_SECRET_KEY", "").strip()
        requested_mode = values.get("KIWOOM_API_MODE", "mock").strip().lower()
        self.mode = "production" if requested_mode == "production" else "mock"
        self.base_url = (
            self.PRODUCTION_URL if self.mode == "production" else self.MOCK_URL
        )
        self.http = http or requests
        self.timeout = timeout

        self._access_token: Optional[str] = None
        self._expires_at: Optional[datetime] = None
        self._token_lock = threading.Lock()

    @property
    def is_configured(self) -> bool:
        return bool(self.app_key and self.secret_key)

    def public_status(self) -> dict[str, Any]:
        """Return connection metadata without credentials or account details."""
        return {
            "provider": "kiwoom",
            "configured": self.is_configured,
            "mode": self.mode,
            "read_only": True,
        }

    def get_access_token(self, *, force_refresh: bool = False) -> str:
        if not self.is_configured:
            raise KiwoomConfigurationError(
                "KIWOOM_APP_KEY와 KIWOOM_SECRET_KEY가 필요합니다."
            )

        with self._token_lock:
            if not force_refresh and self._token_is_valid():
                return self._access_token or ""

            response = self.http.post(
                f"{self.base_url}/oauth2/token",
                json={
                    "grant_type": "client_credentials",
                    "appkey": self.app_key,
                    "secretkey": self.secret_key,
                },
                headers={"Content-Type": "application/json;charset=UTF-8"},
                timeout=self.timeout,
            )

            try:
                payload = response.json()
            except ValueError as exc:
                raise KiwoomAPIError(
                    f"키움 인증 응답을 해석할 수 없습니다. (HTTP {response.status_code})"
                ) from exc

            if response.status_code >= 400 or payload.get("return_code") not in (0, "0"):
                message = payload.get("return_msg") or payload.get("message")
                raise KiwoomAPIError(message or "키움 접근 토큰 발급에 실패했습니다.")

            token = payload.get("token")
            if not token:
                raise KiwoomAPIError("키움 인증 응답에 접근 토큰이 없습니다.")

            self._access_token = str(token)
            self._expires_at = self._parse_expiry(payload.get("expires_dt"))
            return self._access_token

    def verify_connection(self) -> dict[str, Any]:
        self.get_access_token(force_refresh=True)
        return {
            **self.public_status(),
            "connected": True,
            "token_expires_at": (
                self._expires_at.isoformat() if self._expires_at else None
            ),
        }

    def get_account_number(self) -> str:
        payload, _ = self._post_account_api("ka00001", {})
        account_number = str(payload.get("acctNo", "")).strip()
        if not account_number:
            raise KiwoomAPIError("키움 응답에서 계좌번호를 확인할 수 없습니다.")
        return account_number

    def get_deposit(self) -> dict[str, Any]:
        payload, _ = self._post_account_api("kt00001", {"qry_tp": "3"})
        return payload

    def get_positions(self) -> dict[str, Any]:
        request_body = {"qry_tp": "1", "dmst_stex_tp": "KRX"}
        combined: Optional[dict[str, Any]] = None
        positions: list[dict[str, Any]] = []
        continuation = "N"
        next_key = ""

        for _ in range(10):
            payload, response_headers = self._post_account_api(
                "kt00018",
                request_body,
                continuation=continuation,
                next_key=next_key,
            )
            if combined is None:
                combined = dict(payload)
            positions.extend(payload.get("acnt_evlt_remn_indv_tot") or [])

            continuation = str(response_headers.get("cont-yn", "N")).upper()
            next_key = str(response_headers.get("next-key", ""))
            if continuation != "Y" or not next_key:
                break

        result = combined or {}
        result["acnt_evlt_remn_indv_tot"] = positions
        return result

    def get_transaction_history(
        self,
        start_date: str,
        end_date: str,
    ) -> list[dict[str, Any]]:
        """Fetch domestic buys, sells and dividend credits from Kiwoom."""
        common_body = {
            "strt_dt": start_date.replace("-", ""),
            "end_dt": end_date.replace("-", ""),
            "stk_cd": "",
            "crnc_cd": "",
            "gds_tp": "1",
            "frgn_stex_code": "",
            "dmst_stex_tp": "%",
        }
        transactions: list[dict[str, Any]] = []
        for transaction_type, side in (("4", "BUY"), ("5", "SELL")):
            body = {**common_body, "tp": transaction_type}
            for item in self._get_transaction_pages(body):
                transactions.append(self._normalize_transaction(item, side))

        dividend_body = {**common_body, "tp": "0"}
        for item in self._get_transaction_pages(dividend_body):
            description = " ".join(
                str(item.get(field, ""))
                for field in ("rmrk_nm", "trde_kind_nm", "io_tp_nm")
            )
            if "배당" in description or "분배" in description:
                transactions.append(self._normalize_transaction(item, "DIVIDEND"))

        unique = {}
        for transaction in transactions:
            unique[transaction["id"]] = transaction
        return sorted(
            unique.values(),
            key=lambda item: (item["date"], item.get("time", ""), item["id"]),
        )

    def get_account_snapshot(
        self,
        *,
        include_performance: bool = False,
        history_months: int = 12,
        local_transactions: Optional[list[Mapping[str, Any]]] = None,
    ) -> dict[str, Any]:
        """Return a normalized, masked account snapshot for the UI."""
        account_number = self.get_account_number()
        deposit = self.get_deposit()
        balance = self.get_positions()
        raw_positions = balance.get("acnt_evlt_remn_indv_tot") or []
        positions = [self._normalize_position(item) for item in raw_positions]

        snapshot = {
            "provider": "kiwoom",
            "mode": self.mode,
            "read_only": True,
            "account": {
                "masked_number": self._mask_account_number(account_number),
            },
            "cash": {
                "deposit": self._to_int(deposit.get("entr")),
                "estimated_d2": self._to_int(deposit.get("d2_entra")),
            },
            "summary": {
                "total_purchase": self._to_int(balance.get("tot_pur_amt")),
                "total_evaluation": self._to_int(balance.get("tot_evlt_amt")),
                "total_profit_loss": self._to_int(balance.get("tot_evlt_pl")),
                "total_return_rate": self._to_float(balance.get("tot_prft_rt")),
                "estimated_assets": self._to_int(
                    balance.get("prsm_dpst_aset_amt")
                ),
            },
            "positions": positions,
            "synced_at": datetime.now(timezone.utc).isoformat(),
        }
        if include_performance:
            months = max(1, min(int(history_months), 60))
            end_date = datetime.now().date()
            start_date = _subtract_months(end_date, months)
            broker_transactions = self.get_transaction_history(
                start_date.isoformat(),
                end_date.isoformat(),
            )
            normalized_local = [
                self._normalize_local_transaction(item, index)
                for index, item in enumerate((local_transactions or [])[:500])
            ]
            all_transactions = broker_transactions + normalized_local
            snapshot["performance"] = calculate_portfolio_performance(
                positions,
                all_transactions,
            )
            snapshot["history"] = {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "broker_transaction_count": len(broker_transactions),
                "local_transaction_count": len(normalized_local),
            }
        return snapshot

    def _get_transaction_pages(
        self,
        request_body: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        transactions: list[dict[str, Any]] = []
        continuation = "N"
        next_key = ""

        for _ in range(20):
            payload, response_headers = self._post_account_api(
                "kt00015",
                request_body,
                continuation=continuation,
                next_key=next_key,
            )
            transactions.extend(
                payload.get("trst_ovrl_trde_prps_array") or []
            )
            continuation = str(response_headers.get("cont-yn", "N")).upper()
            next_key = str(response_headers.get("next-key", ""))
            if continuation != "Y" or not next_key:
                break
        return transactions

    def _post_account_api(
        self,
        api_id: str,
        body: Mapping[str, Any],
        *,
        continuation: str = "N",
        next_key: str = "",
    ) -> tuple[dict[str, Any], Mapping[str, Any]]:
        token = self.get_access_token()
        response = self.http.post(
            f"{self.base_url}/api/dostk/acnt",
            json=dict(body),
            headers={
                "Content-Type": "application/json;charset=UTF-8",
                "authorization": f"Bearer {token}",
                "api-id": api_id,
                "cont-yn": continuation,
                "next-key": next_key,
            },
            timeout=self.timeout,
        )

        try:
            payload = response.json()
        except ValueError as exc:
            raise KiwoomAPIError(
                f"키움 {api_id} 응답을 해석할 수 없습니다. "
                f"(HTTP {response.status_code})"
            ) from exc

        return_code = payload.get("return_code")
        if response.status_code >= 400 or return_code not in (None, 0, "0"):
            message = payload.get("return_msg") or payload.get("message")
            raise KiwoomAPIError(message or f"키움 {api_id} 조회에 실패했습니다.")

        return payload, getattr(response, "headers", {})

    @classmethod
    def _normalize_position(cls, item: Mapping[str, Any]) -> dict[str, Any]:
        symbol = cls._normalize_symbol(item.get("stk_cd"))

        return {
            "symbol": symbol,
            "name": str(item.get("stk_nm", "")).strip(),
            "quantity": abs(cls._to_int(item.get("rmnd_qty"))),
            "available_quantity": abs(cls._to_int(item.get("trde_able_qty"))),
            "average_price": abs(cls._to_int(item.get("pur_pric"))),
            "current_price": abs(cls._to_int(item.get("cur_prc"))),
            "purchase_amount": abs(cls._to_int(item.get("pur_amt"))),
            "evaluation_amount": abs(cls._to_int(item.get("evlt_amt"))),
            "profit_loss": cls._to_int(item.get("evltv_prft")),
            "return_rate": cls._to_float(item.get("prft_rt")),
        }

    @classmethod
    def _normalize_transaction(
        cls,
        item: Mapping[str, Any],
        side: str,
    ) -> dict[str, Any]:
        transaction_date = str(
            item.get("cntr_dt") or item.get("trde_dt") or ""
        ).strip()
        transaction_number = str(item.get("trde_no", "")).strip()
        fees = abs(cls._to_int(item.get("cmsn"))) + abs(
            cls._to_int(item.get("fc_cmsn"))
        )
        taxes = sum(
            abs(cls._to_int(item.get(field)))
            for field in (
                "trde_agri_tax",
                "fc_trde_tax",
                "incm_resi_tax",
                "frgn_pay_txam",
            )
        )
        amount = abs(cls._to_int(item.get("trde_amt")))
        settlement = abs(cls._to_int(item.get("exct_amt")))

        return {
            "id": f"kiwoom:{transaction_date}:{transaction_number}:{side}",
            "date": transaction_date,
            "time": str(item.get("proc_tm", "")).strip(),
            "side": side,
            "symbol": cls._normalize_symbol(item.get("stk_cd")),
            "name": str(item.get("stk_nm", "")).strip(),
            "quantity": abs(cls._to_int(item.get("trde_qty_jwa_cnt"))),
            "unit_price": abs(cls._to_int(item.get("trde_unit"))),
            "amount": amount,
            "net_amount": (
                settlement
                if side == "DIVIDEND" and settlement
                else max(0, amount - fees - taxes)
            ),
            "fees": fees,
            "taxes": taxes,
            "source": "kiwoom",
            "estimated": False,
        }

    @classmethod
    def _normalize_local_transaction(
        cls,
        item: Mapping[str, Any],
        index: int,
    ) -> dict[str, Any]:
        side = str(item.get("side", "BUY")).upper()
        if side not in {"BUY", "SELL", "DIVIDEND"}:
            side = "BUY"
        date_value = str(item.get("date", "")).replace("-", "")[:8]
        return {
            "id": str(item.get("id") or f"local:{index}:{date_value}"),
            "date": date_value,
            "time": "",
            "side": side,
            "symbol": cls._normalize_symbol(item.get("symbol")),
            "name": str(item.get("name", "")).strip()[:80],
            "quantity": abs(cls._to_int(item.get("quantity"))),
            "unit_price": abs(cls._to_int(item.get("unit_price"))),
            "amount": abs(cls._to_int(item.get("amount"))),
            "net_amount": abs(cls._to_int(item.get("net_amount"))),
            "fees": abs(cls._to_int(item.get("fees"))),
            "taxes": abs(cls._to_int(item.get("taxes"))),
            "source": "local",
            "estimated": False,
        }

    @staticmethod
    def _normalize_symbol(raw_value: Any) -> str:
        symbol = str(raw_value or "").strip()
        if len(symbol) == 7 and symbol.startswith("A"):
            symbol = symbol[1:]
        for suffix in ("_NX", "_AL"):
            if symbol.endswith(suffix):
                symbol = symbol[: -len(suffix)]
        return symbol

    @staticmethod
    def _mask_account_number(account_number: str) -> str:
        compact = account_number.replace("-", "")
        if len(compact) <= 4:
            return "*" * len(compact)
        return f"{'*' * (len(compact) - 4)}{compact[-4:]}"

    @staticmethod
    def _to_int(value: Any) -> int:
        try:
            return int(float(str(value or "0").replace(",", "").strip()))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _to_float(value: Any) -> float:
        try:
            return float(str(value or "0").replace(",", "").strip())
        except (TypeError, ValueError):
            return 0.0

    def _token_is_valid(self) -> bool:
        if not self._access_token or not self._expires_at:
            return False
        return datetime.now() < self._expires_at - timedelta(seconds=60)

    @staticmethod
    def _parse_expiry(raw_value: Any) -> datetime:
        if raw_value:
            try:
                return datetime.strptime(str(raw_value), "%Y%m%d%H%M%S")
            except ValueError:
                pass
        return datetime.now() + timedelta(hours=12)


def _subtract_months(value, months: int):
    year = value.year
    month = value.month - months
    while month <= 0:
        year -= 1
        month += 12
    day = min(value.day, _days_in_month(year, month))
    return value.replace(year=year, month=month, day=day)


def _days_in_month(year: int, month: int) -> int:
    if month == 12:
        next_month = datetime(year + 1, 1, 1).date()
    else:
        next_month = datetime(year, month + 1, 1).date()
    this_month = datetime(year, month, 1).date()
    return (next_month - this_month).days
