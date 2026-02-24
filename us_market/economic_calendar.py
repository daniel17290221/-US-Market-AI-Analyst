#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
US Market Economic Calendar
"""
import os, json, logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EconomicCalendar:
    def __init__(self, data_dir: str = '.'):
        self.output_file = os.path.join(data_dir, 'economic_calendar.json')
        
    def get_events(self):
        # Mock major economic events for the week
        today = datetime.now()
        events = [
            {
                "date": (today + timedelta(days=1)).strftime("%Y-%m-%d"),
                "time": "21:30",
                "event": "CPI (Consumer Price Index)",
                "impact": "High",
                "forecast": "3.1%",
                "previous": "3.2%"
            },
            {
                "date": (today + timedelta(days=2)).strftime("%Y-%m-%d"),
                "time": "03:00",
                "event": "FOMC Meeting Minutes",
                "impact": "High",
                "forecast": "-",
                "previous": "-"
            },
            {
                "date": (today + timedelta(days=3)).strftime("%Y-%m-%d"),
                "time": "21:30",
                "event": "Non-Farm Payrolls",
                "impact": "High",
                "forecast": "180K",
                "previous": "216K"
            }
        ]
        return events

    def run(self):
        events = self.get_events()
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump({'events': events}, f, indent=2)
        logger.info(f"✅ Saved {len(events)} calendar events")

if __name__ == "__main__":
    EconomicCalendar().run()
