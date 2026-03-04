import requests, re
from bs4 import BeautifulSoup
import pandas as pd

def _fallback_naver_all():
    print("Testing Naver Scraping Fallback for Market Movers...")
    try:
        results = []
        for sosok in [0, 1]: # 0: KOSPI, 1: KOSDAQ
            url = f"https://finance.naver.com/sise/sise_market_sum.naver?sosok={sosok}"
            resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            soup = BeautifulSoup(resp.content, 'html.parser', from_encoding='euc-kr')
            table = soup.find('table', {'class': 'type_2'})
            if not table: 
                print(f"Table not found for sosok {sosok}")
                continue
            
            rows = table.find_all('tr')
            print(f"Found {len(rows)} rows for sosok {sosok}")
            for tr in rows:
                tds = tr.find_all('td')
                if len(tds) < 12: continue
                name_tag = tds[1].find('a')
                if not name_tag: continue
                
                code = re.search(r'code=(\d+)', name_tag['href']).group(1)
                
                try:
                    close = float(tds[2].text.replace(',', '').strip())
                    change = float(tds[4].text.replace('%', '').replace(',', '').strip())
                    volume = int(tds[9].text.replace(',', '').strip())
                    marcap = int(tds[6].text.replace(',', '').strip()) if len(tds) > 6 else 0
                except:
                    close, change, volume, marcap = 0, 0, 0, 0

                results.append({
                    'Code': code,
                    'Name': name_tag.text.strip(),
                    'Market': 'KOSPI' if sosok == 0 else 'KOSDAQ',
                    'Close': close,
                    'ChagesRatio': change,
                    'Volume': volume,
                    'Marcap': marcap
                })
        print(f"Total results: {len(results)}")
        return pd.DataFrame(results)
    except Exception as e:
        print(f"Fallback scraper failed: {e}")
        return pd.DataFrame()

df = _fallback_naver_all()
if not df.empty:
    print(df.head())
else:
    print("Result is empty.")
