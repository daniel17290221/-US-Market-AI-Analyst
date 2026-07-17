"""Stateless Korean household tax-planning endpoints."""

from flask import Blueprint, jsonify, make_response, request

try:
    from tax_engine import analyze_family, optimize_family_allocation
except ImportError:
    from ..tax_engine import analyze_family, optimize_family_allocation


tax_bp = Blueprint("tax", __name__, url_prefix="/api/tax")


def _private_json(payload, status=200):
    response = make_response(jsonify(payload), status)
    response.headers["Cache-Control"] = "no-store, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response


@tax_bp.post("/family-analysis")
def family_analysis():
    body = request.get_json(silent=True) or {}
    profiles = body.get("profiles")
    if not isinstance(profiles, list):
        return _private_json(
            {"message": "가족 프로필 목록이 필요합니다."},
            400,
        )
    if not profiles:
        return _private_json(
            {"message": "한 명 이상의 가족 프로필을 등록해 주세요."},
            400,
        )
    if len(profiles) > 10:
        return _private_json(
            {"message": "가족 프로필은 최대 10명까지 분석할 수 있습니다."},
            400,
        )
    if any(not isinstance(profile, dict) for profile in profiles):
        return _private_json(
            {"message": "가족 프로필 형식이 올바르지 않습니다."},
            400,
        )

    try:
        return _private_json(analyze_family(profiles))
    except Exception:
        return _private_json(
            {"message": "가족 절세 분석 중 오류가 발생했습니다."},
            500,
        )


@tax_bp.post("/allocation-optimization")
def allocation_optimization():
    body = request.get_json(silent=True) or {}
    profiles = body.get("profiles")
    if not isinstance(profiles, list) or not profiles:
        return _private_json(
            {"message": "한 명 이상의 가족 프로필이 필요합니다."},
            400,
        )
    if len(profiles) > 10 or any(not isinstance(profile, dict) for profile in profiles):
        return _private_json(
            {"message": "가족 프로필은 올바른 형식으로 최대 10명까지 입력할 수 있습니다."},
            400,
        )

    try:
        investment_amount = float(body.get("investment_amount", 0))
        annual_yield_rate = float(body.get("annual_yield_rate", 0))
        foreign_ratio = float(body.get("foreign_ratio", 0))
    except (TypeError, ValueError):
        return _private_json(
            {"message": "투자금액과 배당률은 숫자로 입력해 주세요."},
            400,
        )
    if not 0 < investment_amount <= 100_000_000_000:
        return _private_json(
            {"message": "추가 투자금은 1원 이상 1,000억원 이하로 입력해 주세요."},
            400,
        )
    if not 0.1 <= annual_yield_rate <= 30:
        return _private_json(
            {"message": "예상 배당률은 0.1% 이상 30% 이하로 입력해 주세요."},
            400,
        )
    if not 0 <= foreign_ratio <= 100:
        return _private_json(
            {"message": "해외자산 비중은 0% 이상 100% 이하로 입력해 주세요."},
            400,
        )

    try:
        return _private_json(
            optimize_family_allocation(
                profiles,
                investment_amount,
                annual_yield_rate,
                foreign_ratio,
            )
        )
    except ValueError as error:
        return _private_json({"message": str(error)}, 400)
    except Exception:
        return _private_json(
            {"message": "가족 자산 배치 최적화 중 오류가 발생했습니다."},
            500,
        )
