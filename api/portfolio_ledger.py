"""Portfolio lot ledger and FIFO performance calculations."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from typing import Any, Iterable, Mapping


def calculate_portfolio_performance(
    positions: Iterable[Mapping[str, Any]],
    transactions: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Calculate realized, unrealized and dividend returns using FIFO lots."""
    position_map = {
        str(position.get("symbol", "")).strip(): dict(position)
        for position in positions
        if str(position.get("symbol", "")).strip()
    }
    transaction_map: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for transaction in transactions:
        symbol = str(transaction.get("symbol", "")).strip()
        if symbol:
            transaction_map[symbol].append(dict(transaction))

    symbols = sorted(set(position_map) | set(transaction_map))
    results = [
        _calculate_symbol_performance(
            symbol,
            position_map.get(symbol, {}),
            transaction_map.get(symbol, []),
        )
        for symbol in symbols
    ]

    summary = {
        "realized_profit_loss": sum(item["realized_profit_loss"] for item in results),
        "unrealized_profit_loss": sum(
            item["unrealized_profit_loss"] for item in results
        ),
        "net_dividends": sum(item["net_dividends"] for item in results),
        "total_profit_loss": sum(item["total_profit_loss"] for item in results),
        "cost_basis": sum(item["cost_basis"] for item in results),
        "complete_symbols": sum(item["coverage"] == "complete" for item in results),
        "partial_symbols": sum(item["coverage"] != "complete" for item in results),
    }
    summary["total_return_rate"] = _rate(
        summary["total_profit_loss"],
        summary["cost_basis"],
    )

    return {
        "method": "FIFO",
        "summary": summary,
        "symbols": results,
    }


def _calculate_symbol_performance(
    symbol: str,
    position: Mapping[str, Any],
    transactions: list[dict[str, Any]],
) -> dict[str, Any]:
    ordered = sorted(
        transactions,
        key=lambda item: (
            str(item.get("date", "")),
            str(item.get("time", "")),
            str(item.get("id", "")),
        ),
    )
    lots: list[dict[str, Any]] = []
    realized = 0
    sold_basis = 0
    dividends = 0
    total_fees = 0
    total_taxes = 0
    coverage = "complete"
    first_purchase_date = None

    for transaction in ordered:
        side = str(transaction.get("side", "")).upper()
        quantity = abs(_number(transaction.get("quantity")))
        unit_price = abs(_number(transaction.get("unit_price")))
        fees = abs(_number(transaction.get("fees")))
        taxes = abs(_number(transaction.get("taxes")))
        total_fees += fees
        total_taxes += taxes

        if side == "BUY" and quantity > 0:
            transaction_date = _normalize_date(transaction.get("date"))
            if transaction_date and (
                first_purchase_date is None or transaction_date < first_purchase_date
            ):
                first_purchase_date = transaction_date
            lots.append(
                {
                    "purchase_date": transaction_date,
                    "quantity": quantity,
                    "remaining_quantity": quantity,
                    "unit_price": unit_price,
                    "remaining_fees": fees + taxes,
                    "source": transaction.get("source", "kiwoom"),
                    "estimated": bool(transaction.get("estimated", False)),
                }
            )
        elif side == "SELL" and quantity > 0:
            basis, uncovered = _consume_fifo(lots, quantity)
            proceeds = quantity * unit_price - fees - taxes
            sold_basis += basis
            realized += proceeds - basis
            if uncovered > 0:
                coverage = "partial"
        elif side == "DIVIDEND":
            dividends += _number(
                transaction.get("net_amount", transaction.get("amount", 0))
            )

    target_quantity = abs(_number(position.get("quantity")))
    ledger_quantity = sum(lot["remaining_quantity"] for lot in lots)

    if ledger_quantity > target_quantity:
        _consume_fifo(lots, ledger_quantity - target_quantity)
        coverage = "partial"
    elif target_quantity > ledger_quantity:
        missing_quantity = target_quantity - ledger_quantity
        lots.append(
            {
                "purchase_date": None,
                "quantity": missing_quantity,
                "remaining_quantity": missing_quantity,
                "unit_price": abs(_number(position.get("average_price"))),
                "remaining_fees": 0,
                "source": "broker_average",
                "estimated": True,
            }
        )
        coverage = "partial"

    current_price = abs(_number(position.get("current_price")))
    remaining_lots = []
    remaining_basis = 0
    unrealized = 0
    for lot in lots:
        remaining_quantity = lot["remaining_quantity"]
        if remaining_quantity <= 0:
            continue
        fee_share = lot["remaining_fees"]
        basis = remaining_quantity * lot["unit_price"] + fee_share
        market_value = remaining_quantity * current_price
        remaining_basis += basis
        unrealized += market_value - basis
        remaining_lots.append(
            {
                "purchase_date": lot["purchase_date"],
                "holding_days": _holding_days(lot["purchase_date"]),
                "quantity": _clean_number(remaining_quantity),
                "purchase_price": _clean_number(lot["unit_price"]),
                "current_price": _clean_number(current_price),
                "profit_loss": round(market_value - basis),
                "return_rate": _rate(market_value - basis, basis),
                "source": lot["source"],
                "estimated": lot["estimated"],
            }
        )

    cost_basis = sold_basis + remaining_basis
    total_profit_loss = realized + unrealized + dividends
    name = str(position.get("name", "")).strip()
    if not name:
        name = next(
            (
                str(transaction.get("name", "")).strip()
                for transaction in ordered
                if str(transaction.get("name", "")).strip()
            ),
            symbol,
        )

    return {
        "symbol": symbol,
        "name": name,
        "quantity": _clean_number(target_quantity),
        "current_price": _clean_number(current_price),
        "first_purchase_date": first_purchase_date,
        "realized_profit_loss": round(realized),
        "unrealized_profit_loss": round(unrealized),
        "net_dividends": round(dividends),
        "total_profit_loss": round(total_profit_loss),
        "total_return_rate": _rate(total_profit_loss, cost_basis),
        "cost_basis": round(cost_basis),
        "fees": round(total_fees),
        "taxes": round(total_taxes),
        "coverage": coverage,
        "lots": remaining_lots,
    }


def _consume_fifo(
    lots: list[dict[str, Any]],
    quantity: float,
) -> tuple[float, float]:
    remaining_to_sell = quantity
    consumed_basis = 0.0

    for lot in lots:
        available = lot["remaining_quantity"]
        if available <= 0 or remaining_to_sell <= 0:
            continue
        consumed = min(available, remaining_to_sell)
        ratio = consumed / available
        consumed_fees = lot["remaining_fees"] * ratio
        consumed_basis += consumed * lot["unit_price"] + consumed_fees
        lot["remaining_quantity"] -= consumed
        lot["remaining_fees"] -= consumed_fees
        remaining_to_sell -= consumed

    return consumed_basis, max(0.0, remaining_to_sell)


def _normalize_date(raw_value: Any) -> str | None:
    value = str(raw_value or "").strip().replace("-", "")
    if len(value) != 8 or not value.isdigit():
        return None
    try:
        parsed = datetime.strptime(value, "%Y%m%d").date()
    except ValueError:
        return None
    return parsed.isoformat()


def _holding_days(raw_date: str | None) -> int | None:
    if not raw_date:
        return None
    try:
        return max(0, (date.today() - date.fromisoformat(raw_date)).days)
    except ValueError:
        return None


def _number(value: Any) -> float:
    try:
        return float(str(value or "0").replace(",", "").strip())
    except (TypeError, ValueError):
        return 0.0


def _clean_number(value: float) -> int | float:
    return int(value) if float(value).is_integer() else round(value, 6)


def _rate(profit_loss: float, basis: float) -> float:
    if not basis:
        return 0.0
    return round((profit_loss / basis) * 100, 2)
