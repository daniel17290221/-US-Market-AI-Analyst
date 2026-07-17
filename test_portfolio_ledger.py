import unittest

from api.portfolio_ledger import calculate_portfolio_performance


class PortfolioLedgerTests(unittest.TestCase):
    def test_fifo_realized_unrealized_and_dividend_returns(self):
        positions = [
            {
                "symbol": "005930",
                "name": "삼성전자",
                "quantity": 7,
                "average_price": 110,
                "current_price": 150,
            }
        ]
        transactions = [
            {
                "id": "buy-1",
                "date": "20240101",
                "side": "BUY",
                "symbol": "005930",
                "quantity": 10,
                "unit_price": 100,
                "fees": 10,
                "taxes": 0,
            },
            {
                "id": "buy-2",
                "date": "20240201",
                "side": "BUY",
                "symbol": "005930",
                "quantity": 5,
                "unit_price": 120,
                "fees": 5,
                "taxes": 0,
            },
            {
                "id": "sell-1",
                "date": "20240301",
                "side": "SELL",
                "symbol": "005930",
                "quantity": 8,
                "unit_price": 140,
                "fees": 8,
                "taxes": 2,
            },
            {
                "id": "dividend-1",
                "date": "20240401",
                "side": "DIVIDEND",
                "symbol": "005930",
                "net_amount": 100,
                "fees": 0,
                "taxes": 15,
            },
        ]

        result = calculate_portfolio_performance(positions, transactions)
        stock = result["symbols"][0]

        self.assertEqual(stock["coverage"], "complete")
        self.assertEqual(stock["first_purchase_date"], "2024-01-01")
        self.assertEqual(stock["realized_profit_loss"], 302)
        self.assertEqual(stock["unrealized_profit_loss"], 243)
        self.assertEqual(stock["net_dividends"], 100)
        self.assertEqual(stock["total_profit_loss"], 645)
        self.assertEqual(stock["cost_basis"], 1615)
        self.assertEqual(stock["total_return_rate"], 39.94)
        self.assertEqual([lot["quantity"] for lot in stock["lots"]], [2, 5])

    def test_missing_history_uses_broker_average_as_estimated_lot(self):
        positions = [
            {
                "symbol": "000660",
                "name": "SK하이닉스",
                "quantity": 10,
                "average_price": 100,
                "current_price": 120,
            }
        ]

        result = calculate_portfolio_performance(positions, [])
        stock = result["symbols"][0]

        self.assertEqual(stock["coverage"], "partial")
        self.assertIsNone(stock["first_purchase_date"])
        self.assertEqual(stock["unrealized_profit_loss"], 200)
        self.assertEqual(stock["total_return_rate"], 20.0)
        self.assertTrue(stock["lots"][0]["estimated"])
        self.assertEqual(stock["lots"][0]["source"], "broker_average")


if __name__ == "__main__":
    unittest.main()
