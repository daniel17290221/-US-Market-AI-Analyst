
import requests
from bs4 import BeautifulSoup

def test_ipo_table():
    url = "https://finance.naver.com/sise/ipo.naver"
    print(f"Testing URL: {url}")
    try:
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        print(f"Status Code: {resp.status_code}")
        if resp.status_code != 200:
            return
        
        soup = BeautifulSoup(resp.content, 'html.parser')
        
        # Find the table with IPOs
        # It's usually in a table with class 'type_1'
        table = soup.select_one('table.type_1')
        if not table:
            print("Table not found")
            return
            
        rows = table.select('tr')
        print(f"Rows found: {len(rows)}")
        
        ipo_list = []
        for row in rows:
            cols = row.select('td')
            if len(cols) >= 5:
                # Typically: Name, Subscription Date, Listing Date, Competition Ratio, etc.
                name = cols[0].get_text(strip=True)
                sub_date = cols[1].get_text(strip=True)
                list_date = cols[2].get_text(strip=True)
                price = cols[3].get_text(strip=True)
                
                if name and sub_date:
                    ipo_list.append({
                        "name": name,
                        "date": sub_date,
                        "status": "청약예정",
                        "price": price
                    })
        
        with open('debug_ipo_table.txt', 'w', encoding='utf-8') as f:
            for item in ipo_list:
                f.write(f"{item['name']} | {item['date']} | {item['price']}\n")
        print(f"Captured {len(ipo_list)} IPO items.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_ipo_table()
