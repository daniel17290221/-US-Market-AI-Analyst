"""Korean household dividend-tax screening engine.

The calculations are planning estimates, not a tax return. They intentionally
surface assumptions and risk thresholds instead of presenting false precision.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping


RULES_AS_OF = "2026-07-17"
FINANCIAL_INCOME_THRESHOLD = 20_000_000
HEALTH_DEPENDENT_INCOME_LIMIT = 20_000_000
PENSION_CREDIT_LIMIT = 9_000_000
PENSION_SAVINGS_SUBLIMIT = 6_000_000
ISA_TAX_FREE_PROFIT = 2_000_000
ISA_SEPARATE_TAX_RATE = 0.099
PENSION_WITHDRAWAL_TAX_RATE = 0.055

INCOME_TAX_BRACKETS = (
    (14_000_000, 0.06),
    (50_000_000, 0.15),
    (88_000_000, 0.24),
    (150_000_000, 0.35),
    (300_000_000, 0.38),
    (500_000_000, 0.40),
    (1_000_000_000, 0.42),
    (None, 0.45),
)

GIFT_ALLOWANCES = {
    "spouse": 600_000_000,
    "adult_child": 50_000_000,
    "minor_child": 20_000_000,
    "parent": 50_000_000,
    "other_relative": 10_000_000,
    "self": 0,
}

SOURCES = [
    {
        "label": "국가법령정보센터 소득세법 제14조",
        "url": "https://www.law.go.kr/lsLawLinkInfo.do?chrClsCd=010202&lsJoLnkSeq=1000225996",
    },
    {
        "label": "국세청 증여재산공제",
        "url": "https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7960&mi=6533",
    },
    {
        "label": "국민건강보험 피부양자 소득요건",
        "url": "https://www.nhis.or.kr/nhis/policy/wbhada07400m01.do",
    },
    {
        "label": "국세청 연금계좌 세액공제",
        "url": "https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?cntntsId=7875",
    },
]


def analyze_family(profiles: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    normalized = [_normalize_profile(profile, index) for index, profile in enumerate(profiles)]
    members = [_analyze_member(profile) for profile in normalized]

    safe_order = sorted(
        (
            {
                "profile_id": member["id"],
                "name": member["name"],
                "safe_additional_financial_income": member[
                    "safe_additional_financial_income"
                ],
            }
            for member in members
            if member["safe_additional_financial_income"] > 0
        ),
        key=lambda item: item["safe_additional_financial_income"],
        reverse=True,
    )

    summary = {
        "member_count": len(members),
        "financial_income": sum(member["financial_income"] for member in members),
        "estimated_withholding": sum(
            member["tax"]["estimated_withholding"] for member in members
        ),
        "estimated_additional_income_tax": sum(
            member["tax"]["estimated_additional_payment"] for member in members
        ),
        "planned_gifts": sum(member["gift"]["planned_gift"] for member in members),
        "estimated_gift_tax": sum(
            member["gift"]["estimated_incremental_gift_tax"] for member in members
        ),
        "estimated_pension_credit": sum(
            member["pension"]["estimated_additional_credit"] for member in members
        ),
        "health_dependent_risk_count": sum(
            member["health"]["dependent_status"] == "risk" for member in members
        ),
        "financial_comprehensive_tax_count": sum(
            member["financial_income_excess"] > 0 for member in members
        ),
    }

    return {
        "rules_as_of": RULES_AS_OF,
        "currency": "KRW",
        "estimate_only": True,
        "summary": summary,
        "members": members,
        "allocation_order": safe_order,
        "sources": SOURCES,
        "disclaimer": (
            "금융소득 비교과세, 배당가산·세액공제, 외국납부세액공제, "
            "건강보험 재산요건과 개인별 공제를 모두 확정 반영한 신고세액이 아닙니다."
        ),
    }


def optimize_family_allocation(
    profiles: Iterable[Mapping[str, Any]],
    investment_amount: Any,
    annual_yield_rate: Any,
    foreign_ratio: Any = 0,
) -> dict[str, Any]:
    """Allocate new dividend assets across family members and account types.

    Account room is supplied by each profile through ``isa_available`` and
    ``pension_asset_room``. The result is a planning heuristic: it keeps gifted
    assets within the entered ten-year allowance and protects dependent health
    insurance headroom before using taxable general accounts.
    """
    normalized = [
        _normalize_profile(profile, index)
        for index, profile in enumerate(profiles)
    ]
    if not normalized:
        raise ValueError("at least one family profile is required")

    amount = _money(investment_amount)
    yield_rate = _percentage(annual_yield_rate)
    overseas_share = _percentage(foreign_ratio)
    if amount <= 0 or yield_rate <= 0:
        raise ValueError("investment amount and yield must be positive")

    owner = next(
        (profile for profile in normalized if profile["relationship"] == "self"),
        normalized[0],
    )
    owner_id = owner["id"]
    base_analysis = analyze_family(normalized)
    base_members = {member["id"]: member for member in base_analysis["members"]}
    gift_room = {
        member["id"]: member["gift"]["remaining_allowance_before_plan"]
        for member in base_analysis["members"]
    }
    allocations: list[dict[str, Any]] = []
    remaining = amount

    def available_transfer(profile_id: str) -> int:
        return amount if profile_id == owner_id else gift_room[profile_id]

    def place(profile: Mapping[str, Any], account: str, capacity: int, reason: str) -> None:
        nonlocal remaining
        invest = min(remaining, max(0, capacity), available_transfer(profile["id"]))
        if invest <= 0:
            return
        allocations.append(
            {
                "profile_id": profile["id"],
                "name": profile["name"],
                "account": account,
                "investment": invest,
                "gift_required": invest if profile["id"] != owner_id else 0,
                "reason": reason,
            }
        )
        remaining -= invest
        if profile["id"] != owner_id:
            gift_room[profile["id"]] -= invest

    adults = [profile for profile in normalized if profile["age"] >= 19]
    pension_order = sorted(
        adults,
        key=lambda profile: (
            profile["id"] != owner_id,
            not (profile["gross_salary"] or profile["other_income"]),
            -profile["pension_asset_room"],
        ),
    )
    for profile in pension_order:
        place(
            profile,
            "pension",
            profile["pension_asset_room"],
            "연금계좌에서 배당 과세를 이연하고 인출세율을 낮춥니다.",
        )

    isa_order = sorted(
        adults,
        key=lambda profile: (
            profile["id"] != owner_id,
            -profile["isa_available"],
        ),
    )
    for profile in isa_order:
        place(
            profile,
            "isa",
            profile["isa_available"],
            "ISA 비과세 한도와 9.9% 분리과세를 우선 활용합니다.",
        )

    general_order = sorted(
        normalized,
        key=lambda profile: (
            profile["id"] != owner_id,
            -base_members[profile["id"]]["safe_additional_financial_income"],
        ),
    )
    for profile in general_order:
        safe_income = base_members[profile["id"]][
            "safe_additional_financial_income"
        ]
        safe_assets = round(safe_income / yield_rate) if yield_rate else 0
        place(
            profile,
            "general",
            safe_assets,
            "금융소득 종합과세와 피부양자 기준 이내의 여유를 사용합니다.",
        )

    if remaining:
        place(
            owner,
            "general",
            remaining,
            "남은 금액은 명의 분산 없이 현재 소유자의 일반계좌에 배치합니다.",
        )

    aggregated: dict[tuple[str, str], dict[str, Any]] = {}
    for allocation in allocations:
        key = (allocation["profile_id"], allocation["account"])
        if key not in aggregated:
            aggregated[key] = dict(allocation)
        else:
            aggregated[key]["investment"] += allocation["investment"]
            aggregated[key]["gift_required"] += allocation["gift_required"]
    allocations = list(aggregated.values())

    optimized_profiles = [dict(profile) for profile in normalized]
    optimized_by_id = {profile["id"]: profile for profile in optimized_profiles}
    account_dividends: dict[tuple[str, str], int] = {}
    for allocation in allocations:
        dividend = round(allocation["investment"] * yield_rate)
        account_dividends[(allocation["profile_id"], allocation["account"])] = dividend
        allocation["expected_annual_dividend"] = dividend
        allocation["domestic_dividend"] = round(dividend * (1 - overseas_share))
        allocation["foreign_dividend"] = dividend - allocation["domestic_dividend"]
        if allocation["account"] == "general":
            profile = optimized_by_id[allocation["profile_id"]]
            profile["domestic_dividends"] += allocation["domestic_dividend"]
            profile["foreign_dividends"] += allocation["foreign_dividend"]

    optimized_analysis = analyze_family(optimized_profiles)
    baseline_profiles = [dict(profile) for profile in normalized]
    baseline_owner = next(
        profile for profile in baseline_profiles if profile["id"] == owner_id
    )
    total_dividend = round(amount * yield_rate)
    baseline_domestic = round(total_dividend * (1 - overseas_share))
    baseline_owner["domestic_dividends"] += baseline_domestic
    baseline_owner["foreign_dividends"] += total_dividend - baseline_domestic
    baseline_analysis = analyze_family(baseline_profiles)

    base_tax = _analysis_tax_cost(base_analysis)
    baseline_tax = max(0, _analysis_tax_cost(baseline_analysis) - base_tax)
    general_tax = max(0, _analysis_tax_cost(optimized_analysis) - base_tax)
    baseline_withholding = max(
        0,
        baseline_analysis["summary"]["estimated_withholding"]
        - base_analysis["summary"]["estimated_withholding"],
    )
    baseline_additional_tax = max(
        0,
        baseline_analysis["summary"]["estimated_additional_income_tax"]
        - base_analysis["summary"]["estimated_additional_income_tax"],
    )
    optimized_general_withholding = max(
        0,
        optimized_analysis["summary"]["estimated_withholding"]
        - base_analysis["summary"]["estimated_withholding"],
    )
    optimized_general_additional_tax = max(
        0,
        optimized_analysis["summary"]["estimated_additional_income_tax"]
        - base_analysis["summary"]["estimated_additional_income_tax"],
    )

    isa_dividends: dict[str, int] = {}
    pension_dividends = 0
    for (profile_id, account), dividend in account_dividends.items():
        if account == "isa":
            isa_dividends[profile_id] = isa_dividends.get(profile_id, 0) + dividend
        elif account == "pension":
            pension_dividends += dividend
    isa_tax = sum(
        round(max(0, dividend - ISA_TAX_FREE_PROFIT) * ISA_SEPARATE_TAX_RATE)
        for dividend in isa_dividends.values()
    )
    pension_tax = round(pension_dividends * PENSION_WITHDRAWAL_TAX_RATE)
    optimized_tax = general_tax + isa_tax + pension_tax

    for allocation in allocations:
        dividend = allocation["expected_annual_dividend"]
        if allocation["account"] == "pension":
            allocation["estimated_tax"] = round(
                dividend * PENSION_WITHDRAWAL_TAX_RATE
            )
            allocation["tax_timing"] = "연금 수령 시 추정"
        elif allocation["account"] == "isa":
            member_total = isa_dividends.get(allocation["profile_id"], 0)
            member_tax = round(
                max(0, member_total - ISA_TAX_FREE_PROFIT)
                * ISA_SEPARATE_TAX_RATE
            )
            allocation["estimated_tax"] = member_tax
            allocation["tax_timing"] = "ISA 만기·해지 시 추정"
        else:
            allocation["estimated_tax"] = None
            allocation["tax_timing"] = "연간 원천징수·종합과세 추정"

    sheltered = sum(
        item["investment"]
        for item in allocations
        if item["account"] in {"isa", "pension"}
    )
    gift_required = sum(item["gift_required"] for item in allocations)
    warnings = []
    if gift_required:
        warnings.append(
            "가족 명의 배치는 실제 증여와 신고 검토가 필요하며 차명 운용은 허용되지 않습니다."
        )
    if optimized_analysis["summary"]["health_dependent_risk_count"]:
        warnings.append(
            "최적안 이후에도 건강보험 피부양자 소득요건 위험 구성원이 있습니다."
        )
    if any(item["account"] == "pension" for item in allocations):
        warnings.append(
            "연금계좌 배치금은 중도 인출 시 세제상 불이익과 유동성 제한이 있을 수 있습니다."
        )

    return {
        "rules_as_of": RULES_AS_OF,
        "currency": "KRW",
        "estimate_only": True,
        "inputs": {
            "owner_profile_id": owner_id,
            "owner_name": owner["name"],
            "investment_amount": amount,
            "annual_yield_rate": yield_rate,
            "foreign_ratio": overseas_share,
            "expected_annual_dividend": total_dividend,
        },
        "summary": {
            "baseline_estimated_tax": baseline_tax,
            "optimized_estimated_tax": optimized_tax,
            "estimated_annual_tax_savings": baseline_tax - optimized_tax,
            "sheltered_investment": sheltered,
            "general_investment": amount - sheltered,
            "gift_required": gift_required,
            "baseline_health_risk_count": baseline_analysis["summary"][
                "health_dependent_risk_count"
            ],
            "optimized_health_risk_count": optimized_analysis["summary"][
                "health_dependent_risk_count"
            ],
        },
        "allocations": allocations,
        "account_comparison": [
            {
                "account": "pension",
                "label": "연금계좌",
                "tax": pension_tax,
                "note": "운용 중 과세이연, 연금 수령세율 5.5%를 보수적으로 적용",
            },
            {
                "account": "isa",
                "label": "ISA",
                "tax": isa_tax,
                "note": "일반형 비과세 200만원 후 9.9% 분리과세 가정",
            },
            {
                "account": "general",
                "label": "일반계좌",
                "tax": general_tax,
                "note": "원천징수와 금융소득 종합과세 증가분 추정",
            },
        ],
        "calculation_evidence": {
            "formulas": [
                {
                    "code": "expected_dividend",
                    "label": "예상 연 배당",
                    "formula": "추가 투자금 × 예상 연 배당률",
                },
                {
                    "code": "general_tax",
                    "label": "일반계좌 추가세금",
                    "formula": "추가 원천징수 + 금융소득 종합과세 추가납부 추정액",
                },
                {
                    "code": "isa_tax",
                    "label": "ISA 추정세금",
                    "formula": "max(0, 구성원별 ISA 배당 - 200만원) × 9.9%",
                },
                {
                    "code": "pension_tax",
                    "label": "연금계좌 추정세금",
                    "formula": "연금계좌 예상 배당 × 5.5%",
                },
                {
                    "code": "annual_savings",
                    "label": "연간 예상 절감액",
                    "formula": "본인 일반계좌 집중 배치 세금 - 최적 배치 세금",
                },
            ],
            "assumptions": {
                "financial_income_threshold": FINANCIAL_INCOME_THRESHOLD,
                "health_dependent_income_limit": HEALTH_DEPENDENT_INCOME_LIMIT,
                "isa_tax_free_profit": ISA_TAX_FREE_PROFIT,
                "isa_separate_tax_rate": ISA_SEPARATE_TAX_RATE,
                "pension_withdrawal_tax_rate": PENSION_WITHDRAWAL_TAX_RATE,
                "domestic_withholding_rate": 0.154,
                "foreign_withholding_rate": 0.15,
            },
            "baseline_components": {
                "withholding": baseline_withholding,
                "additional_income_tax": baseline_additional_tax,
                "total": baseline_tax,
            },
            "optimized_components": {
                "general_withholding": optimized_general_withholding,
                "general_additional_income_tax": optimized_general_additional_tax,
                "isa_tax": isa_tax,
                "pension_tax": pension_tax,
                "total": optimized_tax,
            },
            "member_boundaries": [
                {
                    "profile_id": member["id"],
                    "name": member["name"],
                    "financial_income": member["financial_income"],
                    "financial_income_remaining": member[
                        "financial_income_remaining"
                    ],
                    "safe_additional_financial_income": member[
                        "safe_additional_financial_income"
                    ],
                    "health_dependent_status": member["health"]["dependent_status"],
                    "gift_allowance_remaining": member["gift"][
                        "remaining_allowance_before_plan"
                    ],
                }
                for member in optimized_analysis["members"]
            ],
            "sources": SOURCES,
        },
        "warnings": warnings,
        "disclaimer": (
            "ISA 의무가입기간·손익통산·서민형 자격, 연금 수령연령, 해외납부세액, "
            "건강보험 재산요건과 실제 증여관계를 확정 반영한 세무신고 결과가 아닙니다."
        ),
    }


def _analyze_member(profile: dict[str, Any]) -> dict[str, Any]:
    domestic_financial = profile["interest_income"] + profile["domestic_dividends"]
    financial_income = domestic_financial + profile["foreign_dividends"]
    financial_excess = max(0, financial_income - FINANCIAL_INCOME_THRESHOLD)
    financial_remaining = max(0, FINANCIAL_INCOME_THRESHOLD - financial_income)

    domestic_withholding = round(domestic_financial * 0.154)
    foreign_withholding = round(profile["foreign_dividends"] * 0.15)
    estimated_withholding = domestic_withholding + foreign_withholding
    allocated_withholding = (
        round(estimated_withholding * financial_excess / financial_income)
        if financial_income
        else 0
    )

    base_tax = _progressive_income_tax(profile["taxable_base"])
    combined_tax = _progressive_income_tax(
        profile["taxable_base"] + financial_excess
    )
    incremental_comprehensive_tax = round((combined_tax - base_tax) * 1.1)
    estimated_additional_payment = max(
        0,
        incremental_comprehensive_tax - allocated_withholding,
    )

    health_total_income = profile["other_income"] + financial_income
    health_status = "not_applicable"
    health_headroom = None
    if profile["health_insurance"] == "dependent":
        health_headroom = max(
            0,
            HEALTH_DEPENDENT_INCOME_LIMIT - health_total_income,
        )
        health_status = (
            "risk"
            if health_total_income > HEALTH_DEPENDENT_INCOME_LIMIT
            else "within_limit"
        )

    safe_financial_room = financial_remaining
    if health_headroom is not None:
        safe_financial_room = min(safe_financial_room, health_headroom)

    gift_allowance = _gift_allowance(profile)
    prior_gifts = profile["gift_received_10y"]
    planned_gift = profile["planned_gift"]
    taxable_before = max(0, prior_gifts - gift_allowance)
    taxable_after = max(0, prior_gifts + planned_gift - gift_allowance)
    gift_tax_before = _gift_tax(taxable_before)
    gift_tax_after = _gift_tax(taxable_after)

    pension_room = max(0, PENSION_CREDIT_LIMIT - profile["pension_contribution"])
    has_taxable_income = profile["gross_salary"] > 0 or profile["other_income"] > 0
    pension_rate = (
        0.165
        if (
            profile["gross_salary"] <= 55_000_000
            and profile["other_income"] <= 45_000_000
        )
        else 0.132
    )
    estimated_pension_credit = (
        round(pension_room * pension_rate) if has_taxable_income else 0
    )

    recommendations = _member_recommendations(
        profile,
        financial_excess,
        financial_remaining,
        health_status,
        gift_allowance,
        pension_room,
        has_taxable_income,
    )

    return {
        "id": profile["id"],
        "name": profile["name"],
        "relationship": profile["relationship"],
        "age": profile["age"],
        "financial_income": financial_income,
        "financial_income_threshold": FINANCIAL_INCOME_THRESHOLD,
        "financial_income_remaining": financial_remaining,
        "financial_income_excess": financial_excess,
        "safe_additional_financial_income": safe_financial_room,
        "tax": {
            "domestic_withholding": domestic_withholding,
            "foreign_withholding": foreign_withholding,
            "estimated_withholding": estimated_withholding,
            "incremental_comprehensive_tax": incremental_comprehensive_tax,
            "estimated_additional_payment": estimated_additional_payment,
        },
        "health": {
            "insurance_type": profile["health_insurance"],
            "assessed_income": health_total_income,
            "dependent_income_limit": HEALTH_DEPENDENT_INCOME_LIMIT,
            "dependent_headroom": health_headroom,
            "dependent_status": health_status,
        },
        "gift": {
            "allowance": gift_allowance,
            "gift_received_10y": prior_gifts,
            "planned_gift": planned_gift,
            "remaining_allowance_before_plan": max(0, gift_allowance - prior_gifts),
            "taxable_amount_after_plan": taxable_after,
            "estimated_incremental_gift_tax": max(
                0,
                gift_tax_after - gift_tax_before,
            ),
        },
        "pension": {
            "current_contribution": profile["pension_contribution"],
            "credit_limit": PENSION_CREDIT_LIMIT,
            "additional_contribution_room": pension_room,
            "credit_rate": pension_rate,
            "estimated_additional_credit": estimated_pension_credit,
        },
        "recommendations": recommendations,
    }


def _member_recommendations(
    profile: Mapping[str, Any],
    financial_excess: int,
    financial_remaining: int,
    health_status: str,
    gift_allowance: int,
    pension_room: int,
    has_taxable_income: bool,
) -> list[dict[str, str]]:
    recommendations = []
    if financial_excess:
        recommendations.append(
            {
                "code": "financial_comprehensive_tax",
                "severity": "warning",
                "title": "금융소득 종합과세 구간",
                "detail": f"기준금액을 {financial_excess:,}원 초과하는 추정치입니다.",
            }
        )
    else:
        recommendations.append(
            {
                "code": "financial_income_room",
                "severity": "info",
                "title": "금융소득 기준 여유",
                "detail": f"현재 입력 기준 {financial_remaining:,}원의 여유가 있습니다.",
            }
        )
    if health_status == "risk":
        recommendations.append(
            {
                "code": "health_dependent_risk",
                "severity": "danger",
                "title": "건강보험 피부양자 위험",
                "detail": "전체 소득 합계가 피부양자 소득요건을 초과합니다.",
            }
        )
    if profile["planned_gift"] and (
        profile["gift_received_10y"] + profile["planned_gift"] > gift_allowance
    ):
        recommendations.append(
            {
                "code": "gift_tax_risk",
                "severity": "warning",
                "title": "증여공제 초과 예상",
                "detail": "최근 10년 누적 증여와 계획금액이 공제한도를 초과합니다.",
            }
        )
    if pension_room and has_taxable_income:
        recommendations.append(
            {
                "code": "pension_credit_room",
                "severity": "info",
                "title": "연금계좌 세액공제 여유",
                "detail": f"세액공제 대상 납입한도가 {pension_room:,}원 남았습니다.",
            }
        )
    return recommendations


def _normalize_profile(profile: Mapping[str, Any], index: int) -> dict[str, Any]:
    relationship = str(profile.get("relationship", "self"))
    if relationship not in GIFT_ALLOWANCES:
        relationship = "other_relative"
    health_insurance = str(profile.get("health_insurance", "employee"))
    if health_insurance not in {"employee", "local", "dependent"}:
        health_insurance = "employee"

    return {
        "id": str(profile.get("id") or f"profile-{index}")[:80],
        "name": str(profile.get("name") or f"가족 {index + 1}")[:40],
        "relationship": relationship,
        "age": max(0, min(_money(profile.get("age")), 120)),
        "gross_salary": _money(profile.get("gross_salary")),
        "other_income": _money(profile.get("other_income")),
        "taxable_base": _money(
            profile.get("taxable_base", profile.get("other_income"))
        ),
        "interest_income": _money(profile.get("interest_income")),
        "domestic_dividends": _money(profile.get("domestic_dividends")),
        "foreign_dividends": _money(profile.get("foreign_dividends")),
        "health_insurance": health_insurance,
        "gift_received_10y": _money(profile.get("gift_received_10y")),
        "planned_gift": _money(profile.get("planned_gift")),
        "pension_contribution": _money(profile.get("pension_contribution")),
        "isa_available": _money(profile.get("isa_available")),
        "pension_asset_room": _money(profile.get("pension_asset_room")),
    }


def _gift_allowance(profile: Mapping[str, Any]) -> int:
    relationship = profile["relationship"]
    if relationship in {"adult_child", "minor_child"}:
        return (
            GIFT_ALLOWANCES["minor_child"]
            if profile["age"] < 19
            else GIFT_ALLOWANCES["adult_child"]
        )
    return GIFT_ALLOWANCES[relationship]


def _progressive_income_tax(taxable_base: int) -> float:
    remaining = max(0, taxable_base)
    previous_limit = 0
    tax = 0.0
    for upper_limit, rate in INCOME_TAX_BRACKETS:
        if upper_limit is None:
            tax += remaining * rate
            break
        bracket_width = upper_limit - previous_limit
        taxable_in_bracket = min(remaining, bracket_width)
        tax += taxable_in_bracket * rate
        remaining -= taxable_in_bracket
        if remaining <= 0:
            break
        previous_limit = upper_limit
    return tax


def _gift_tax(taxable_amount: int) -> int:
    if taxable_amount <= 0:
        return 0
    if taxable_amount <= 100_000_000:
        return round(taxable_amount * 0.10)
    if taxable_amount <= 500_000_000:
        return round(taxable_amount * 0.20 - 10_000_000)
    if taxable_amount <= 1_000_000_000:
        return round(taxable_amount * 0.30 - 60_000_000)
    if taxable_amount <= 3_000_000_000:
        return round(taxable_amount * 0.40 - 160_000_000)
    return round(taxable_amount * 0.50 - 460_000_000)


def _money(value: Any) -> int:
    try:
        return max(0, int(float(str(value or "0").replace(",", "").strip())))
    except (TypeError, ValueError):
        return 0


def _percentage(value: Any) -> float:
    try:
        number = max(0.0, float(str(value or "0").replace(",", "").strip()))
    except (TypeError, ValueError):
        return 0.0
    return min(number / 100, 1.0)


def _analysis_tax_cost(analysis: Mapping[str, Any]) -> int:
    summary = analysis["summary"]
    return (
        summary["estimated_withholding"]
        + summary["estimated_additional_income_tax"]
    )
