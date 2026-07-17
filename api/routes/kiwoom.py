"""Protected, read-only endpoints for the Kiwoom integration."""

import hmac
import os

from flask import Blueprint, jsonify, make_response, request

try:
    from kiwoom import (
        KiwoomAPIError,
        KiwoomClient,
        KiwoomConfigurationError,
    )
except ImportError:
    from ..kiwoom import (
        KiwoomAPIError,
        KiwoomClient,
        KiwoomConfigurationError,
    )


kiwoom_bp = Blueprint("kiwoom", __name__, url_prefix="/api/kiwoom")
_client = KiwoomClient()


def _has_sync_access() -> tuple[bool, str, int]:
    sync_secret = os.environ.get("KIWOOM_SYNC_SECRET", "").strip()
    if not sync_secret:
        return False, "KIWOOM_SYNC_SECRET 설정이 필요합니다.", 503

    provided_secret = request.headers.get("X-Kiwoom-Sync-Key", "")
    if not hmac.compare_digest(provided_secret, sync_secret):
        return False, "키움 계좌 조회 권한이 없습니다.", 401
    return True, "", 200


def _private_json(payload, status=200):
    response = make_response(jsonify(payload), status)
    response.headers["Cache-Control"] = "no-store, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response


@kiwoom_bp.get("/status")
def connection_status():
    """Expose safe setup metadata without contacting Kiwoom."""
    return jsonify(
        {
            **_client.public_status(),
            "verification_protected": True,
            "snapshot_available": (
                _client.is_configured
                and bool(os.environ.get("KIWOOM_SYNC_SECRET", "").strip())
            ),
        }
    )


@kiwoom_bp.post("/verify")
def verify_connection():
    """Verify credentials without returning a token or account information."""
    authorized, message, status = _has_sync_access()
    if not authorized:
        return _private_json({"connected": False, "message": message}, status)

    try:
        return _private_json(_client.verify_connection())
    except KiwoomConfigurationError as exc:
        return _private_json({"connected": False, "message": str(exc)}, 503)
    except KiwoomAPIError as exc:
        return _private_json({"connected": False, "message": str(exc)}, 502)
    except Exception:
        return _private_json(
            {
                "connected": False,
                "message": "키움 연결 확인 중 네트워크 오류가 발생했습니다.",
            },
            502,
        )


@kiwoom_bp.post("/snapshot")
def account_snapshot():
    """Return masked cash and domestic holdings for the connected account."""
    authorized, message, status = _has_sync_access()
    if not authorized:
        return _private_json({"connected": False, "message": message}, status)

    body = request.get_json(silent=True) or {}
    local_transactions = body.get("local_transactions") or []
    if not isinstance(local_transactions, list) or len(local_transactions) > 500:
        return _private_json(
            {
                "connected": False,
                "message": "로컬 거래내역은 한 번에 최대 500건까지 처리할 수 있습니다.",
            },
            400,
        )
    try:
        history_months = max(1, min(int(body.get("history_months", 12)), 60))
    except (TypeError, ValueError):
        return _private_json(
            {
                "connected": False,
                "message": "조회기간은 1~60개월 사이의 숫자여야 합니다.",
            },
            400,
        )

    try:
        return _private_json(
            {
                "connected": True,
                **_client.get_account_snapshot(
                    include_performance=body.get("include_performance", True) is not False,
                    history_months=history_months,
                    local_transactions=local_transactions,
                ),
            }
        )
    except KiwoomConfigurationError as exc:
        return _private_json({"connected": False, "message": str(exc)}, 503)
    except KiwoomAPIError as exc:
        return _private_json({"connected": False, "message": str(exc)}, 502)
    except Exception:
        return _private_json(
            {
                "connected": False,
                "message": "키움 계좌 조회 중 네트워크 오류가 발생했습니다.",
            },
            502,
        )
