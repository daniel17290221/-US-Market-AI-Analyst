
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json

def get_ipo_and_schedules():
    """Fetch IPO and corporate action schedules from Naver Finance"""
    try:
        print("Fetching IPO & Schedule news...")
        # Use Naver Finance IPO news sections
        url = "https://finance.naver.com/news/news_list.naver?mode=LSS3D&section_id=101&section_id2=258&section_id3=406" # 공시/IPO 뉴스
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        print(f"Response status: {resp.status_code}")
        if resp.status_code != 200: return []
        
        soup = BeautifulSoup(resp.content, 'html.parser')
        news_list = []
        
        # Parse news titles
        items = soup.select('.articleSubject a, .articleTitle a')
        print(f"Found {len(items)} news items total.")
        


        all_titles = []
        for item in items:
            title = item.get_text().strip()
            all_titles.append(title)
            # Filter for IPO, 유상증자, 무상증자, etc.
            if any(kw in title for kw in ['IPO', '공모', '청약', '유상', '무상', '증자', '상장']):
                link = "https://finance.naver.com" + item['href']
                news_list.append({
                    "name": title[:25] + "..." if len(title) > 25 else title,
                    "status": "뉴스",
                    "manager": "네이버금융",
                    "price": "-",
                    "date": datetime.now().strftime("%m.%d"),
                    "full_title": title,
                    "url": link
                })
        
        with open('debug_all_headlines.txt', 'w', encoding='utf-8') as f:
            for t in all_titles:
                f.write(t + '\n')
                
        if not news_list:
             print("No news matched keywords.")
        return news_list

    except Exception as e:
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    news = get_ipo_and_schedules()
    with open('debug_ipo_output.json', 'w', encoding='utf-8') as f:
        json.dump(news, f, ensure_ascii=False, indent=2)
    print(f"Result saved to debug_ipo_output.json. Found {len(news)} items.")

